"""
Slack and Discord Bot Connector & Webhook Simulator.
Enables bidirectional Agent interaction via Slack slash commands and Discord channel webhooks.
"""

import time
from typing import Any, Dict, Optional

from pydantic import BaseModel

from src.agent.llm_client import LLMClient
from src.agent.orchestrator import AgentOrchestrator


class SlackCommandRequest(BaseModel):
    command: str  # e.g., "/triage", "/patch", "/rca"
    text: str  # arguments, e.g. "SV-10492"
    user_name: str
    channel_id: str
    response_url: Optional[str] = None


class DiscordWebhookPayload(BaseModel):
    content: str
    username: str = "Enterprise-Agentic-Bot"
    avatar_url: Optional[str] = "https://img.icons8.com/color/96/bot.png"
    embeds: Optional[list] = None


class SlackDiscordConnector:
    @staticmethod
    def handle_slack_slash_command(req: SlackCommandRequest) -> Dict[str, Any]:
        """Processes incoming Slack slash commands and triggers agent execution."""
        cmd = req.command.lower()
        arg = req.text.strip()
        orchestrator = AgentOrchestrator(LLMClient(provider="mock"))

        if "/triage" in cmd or "triage" in arg.lower():
            target_server = arg if arg else "SV-10492"
            prompt = f"Perform an automated disk health triage for server {target_server}."
            task_id = f"SLACK-TRIAGE-{int(time.time())}"
        elif "/patch" in cmd or "patch" in arg.lower():
            target_cluster = arg if arg else "CL-PROD-01"
            prompt = f"Generate a zero-downtime firmware upgrade and patch plan for cluster {target_cluster}."
            task_id = f"SLACK-PATCH-{int(time.time())}"
        else:
            incident_id = arg if arg else "INC-LOG-992"
            prompt = f"Perform root cause analysis on distributed incident {incident_id}."
            task_id = f"SLACK-RCA-{int(time.time())}"

        events = list(orchestrator.run_stream(user_prompt=prompt, task_id=task_id))
        synthesis = next(
            (e.data.get("response") for e in reversed(events) if e.event_type == "SYNTHESIS"),
            "Execution completed.",
        )

        # Return Slack Block Kit compatible payload
        return {
            "response_type": "in_channel",
            "text": f"🤖 *Agentic AI Execution Result* for `{req.user_name}`:",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⚡ *Command Triggered*: `{req.command} {req.text}`\n*Task ID*: `{task_id}`",
                    },
                },
                {"type": "section", "text": {"type": "mrkdwn", "text": f"```\n{synthesis}\n```"}},
            ],
        }

    @staticmethod
    def format_discord_notification(
        title: str, description: str, color_hex: int = 0x00F0FF
    ) -> Dict[str, Any]:
        """Formats an outgoing alert embed for Discord channel webhooks."""
        return {
            "username": "Enterprise Agentic Bot",
            "embeds": [
                {
                    "title": f"🚨 {title}",
                    "description": description,
                    "color": color_hex,
                    "footer": {"text": "Enterprise Agentic AI Blueprint • Dell OME Modernization"},
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
            ],
        }
