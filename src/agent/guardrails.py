"""
Deterministic Safety Guardrails and Pre/Post-Flight Validators.
"""

import re
from typing import Dict, Any, Tuple, Optional
from pydantic import BaseModel

DANGEROUS_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r"\bdrop\s+database\b",
    r"\btruncate\s+table\b",
    r"\bshutdown\s+-h\b",
    r"\breboot\s+-f\b",
]

SECRET_PATTERNS = [
    (r"(?i)(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*['\"]?([^\s'\"]+)['\"]?", r"\1: [REDACTED_SECRET]"),
    (r"\b(ghp_[a-zA-Z0-9]{36}|sk-[a-zA-Z0-9]{48})\b", "[REDACTED_TOKEN]")
]

class GuardrailResult:
    def __init__(self, is_safe: bool, sanitized_content: str, violation_reason: Optional[str] = None):
        self.is_safe = is_safe
        self.sanitized_content = sanitized_content
        self.violation_reason = violation_reason

class AgentGuardrails:
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitizes sensitive tokens and passwords from input text before model ingestion."""
        sanitized = text
        for pattern, replacement in SECRET_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized)
        return sanitized

    @staticmethod
    def validate_command_safety(command: str, is_dry_run: bool = False) -> GuardrailResult:
        """Inspects shell commands or actions for catastrophic destructive operations."""
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                if not is_dry_run:
                    return GuardrailResult(
                        is_safe=False,
                        sanitized_content=command,
                        violation_reason=f"Dangerous command pattern detected: '{pattern}'. Destructive actions blocked without simulated dry-run verification."
                    )
        return GuardrailResult(is_safe=True, sanitized_content=command)

    @staticmethod
    def validate_tool_args(schema_class: type[BaseModel], args: Dict[str, Any]) -> Tuple[bool, Optional[BaseModel], Optional[str]]:
        """Type-validates tool arguments against a Pydantic schema."""
        try:
            validated = schema_class(**args)
            return True, validated, None
        except Exception as e:
            return False, None, f"Schema validation error: {str(e)}"
