"""
Autonomous ReAct Orchestrator with Real-Time SSE Streaming and Tool Dispatch.
"""

import json
import re
import time
from typing import Any, Dict, Generator, Optional

from src.agent.guardrails import AgentGuardrails
from src.agent.llm_client import LLMClient
from src.agent.memory import EpisodicMemory, StructuredAuditMemory, WorkingMemory
from src.agent.prompts import SYSTEM_PERSONA_FDE
from src.tools.mcp_server import MCPServer


class AgentEvent:
    def __init__(self, event_type: str, data: Dict[str, Any]):
        self.event_type = event_type
        self.data = data
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"event_type": self.event_type, "data": self.data, "timestamp": self.timestamp}


class AgentOrchestrator:
    def __init__(
        self, llm_client: Optional[LLMClient] = None, audit_db_path: str = "agent_audit.sqlite"
    ):
        self.llm = llm_client or LLMClient()
        self.working_mem = WorkingMemory()
        self.episodic_mem = EpisodicMemory()
        self.audit_mem = StructuredAuditMemory(audit_db_path)
        self.guardrails = AgentGuardrails()

    def run_stream(
        self, user_prompt: str, task_id: str = "TASK-001"
    ) -> Generator[AgentEvent, None, Dict[str, Any]]:
        """Runs the ReAct agent loop and yields streaming SSE events in real-time."""
        start_time = time.time()
        self.working_mem.clear()

        # Guardrail check on input
        sanitized_prompt = self.guardrails.sanitize_input(user_prompt)
        yield AgentEvent(
            "INPUT_SANITIZED",
            {"original_len": len(user_prompt), "sanitized_prompt": sanitized_prompt},
        )

        messages = [
            {"role": "system", "content": SYSTEM_PERSONA_FDE},
            {"role": "user", "content": sanitized_prompt},
        ]

        yield AgentEvent("TASK_STARTED", {"task_id": task_id, "prompt": sanitized_prompt})

        loop_count = 0
        max_loops = 6
        seen_actions = set()
        failed = False
        final_synthesis = ""

        while loop_count < max_loops:
            loop_count += 1
            try:
                llm_resp = self.llm.chat(messages=messages)
            except Exception:
                failed = True
                final_synthesis = "Provider failed; no verified result is available."
                break
            content = self.guardrails.sanitize_input(llm_resp.content)

            # Parse Thought
            thought_match = re.search(
                r"Thought:\s*(.*?)(?=\nAction:|\nSynthesis:|$)", content, re.DOTALL
            )
            if thought_match:
                thought = thought_match.group(1).strip()
                self.working_mem.add_thought(thought)
                yield AgentEvent(
                    "THOUGHT",
                    {
                        "step": loop_count,
                        "thought": thought,
                        "latency_ms": round(llm_resp.latency_ms, 2),
                    },
                )

            # Check for Synthesis (Terminal State)
            if "Synthesis:" in content or "{" in content and "status" in content:
                synthesis_match = re.search(r"Synthesis:\s*(.*?)$", content, re.DOTALL)
                final_synthesis = synthesis_match.group(1).strip() if synthesis_match else content
                break

            # Parse Action
            action_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)\((.*?)\)", content)
            if action_match:
                tool_name = action_match.group(1).strip()
                raw_args_str = action_match.group(2).strip()

                # Parse arguments
                tool_args = {}
                try:
                    # Simple kwargs parser
                    for pair in re.findall(
                        r"([a-zA-Z0-9_]+)=['\"]([^'\"]*)['\"]|([a-zA-Z0-9_]+)=([0-9]+)",
                        raw_args_str,
                    ):
                        k = pair[0] or pair[2]
                        v = pair[1] or (int(pair[3]) if pair[3].isdigit() else pair[3])
                        tool_args[k] = v
                except Exception:
                    tool_args = {}

                self.working_mem.add_action(tool_name, tool_args)
                yield AgentEvent(
                    "ACTION_DISPATCHED", {"step": loop_count, "tool": tool_name, "args": tool_args}
                )

                # Execute tool
                tool_start = time.time()
                action_key = json.dumps([tool_name, tool_args], sort_keys=True)
                if action_key in seen_actions:
                    tool_result = {"error": "Repeated tool invocation blocked"}
                else:
                    seen_actions.add(action_key)
                    tool_result = MCPServer.call_tool(tool_name, tool_args)
                success = "error" not in tool_result
                failed = failed or not success

                tool_duration_ms = (time.time() - tool_start) * 1000
                self.working_mem.add_observation(tool_result)
                self.audit_mem.log_tool_call(
                    task_id, tool_name, tool_args, tool_result, success, tool_duration_ms
                )

                yield AgentEvent(
                    "OBSERVATION",
                    {
                        "step": loop_count,
                        "tool": tool_name,
                        "result": tool_result,
                        "success": success,
                        "duration_ms": round(tool_duration_ms, 2),
                    },
                )

                # Append to context
                messages.append({"role": "assistant", "content": content})
                messages.append(
                    {"role": "user", "content": f"Observation: {json.dumps(tool_result)}"}
                )
            else:
                final_synthesis = content
                break

        if not final_synthesis:
            failed = True
            final_synthesis = "Iteration limit reached without a verified synthesis."
        total_latency = (time.time() - start_time) * 1000
        yield AgentEvent(
            "SYNTHESIS",
            {
                "task_id": task_id,
                "response": final_synthesis,
                "status": "FAILED" if failed else "COMPLETED",
                "total_loops": loop_count,
                "total_latency_ms": round(total_latency, 2),
            },
        )

        self.audit_mem.log_execution(
            task_id=task_id,
            prompt=sanitized_prompt,
            plan={"steps": loop_count},
            response=final_synthesis,
            status="FAILED" if failed else "COMPLETED",
            latency_ms=total_latency,
        )

        return {
            "task_id": task_id,
            "synthesis": final_synthesis,
            "trace": self.working_mem.get_trace(),
            "total_latency_ms": total_latency,
        }
