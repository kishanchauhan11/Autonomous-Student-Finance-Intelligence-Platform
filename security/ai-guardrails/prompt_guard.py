# prompt_guard.py - AI Guardrails: Prompt Injection & Safety Validation
# Defends against prompt injection, jailbreaks, and unsafe content in AI queries.

import re
from typing import Dict, Any, List

# Patterns that indicate prompt injection attempts
INJECTION_PATTERNS: List[str] = [
    r"ignore (all )?(previous|prior|above) instructions",
    r"forget (your |all )?(instructions|training|role)",
    r"you are now",
    r"act as (a |an )?(different|new|unconstrained|evil|hacker|admin)",
    r"disregard (your |all )?",
    r"override (your |all )?(safety|rules|constraints)",
    r"pretend (you are|to be|that)",
    r"jailbreak",
    r"dan mode",
    r"developer mode",
    r"<[^>]{1,50}>",            # HTML/XML injection tags
    r"\{\{.*?\}\}",             # Template injection
    r"system\s*:[\s\S]*",       # Fake system prompt injection
]

# Topics that are off-limits for finance AI
BLOCKED_TOPICS: List[str] = [
    "personal bank login", "steal", "hack", "exploit", "bypass", 
    "illegal", "money laundering", "fraud", "phishing", "identity theft",
    "malware", "ransomware", "sql injection", "xss", "IDOR"
]

# Maximum safe input token length (approx 4 chars per token)
MAX_INPUT_LENGTH = 2000

class AIGuardrailService:
    """
    Multi-layer prompt injection detection and content safety enforcement.
    Applied at the gateway level before any LLM call.
    """

    @staticmethod
    def scan_for_injection(query: str) -> Dict[str, Any]:
        """Scans input for known prompt injection patterns."""
        query_lower = query.lower()
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                print(f"[GUARDRAIL] Prompt injection detected: pattern='{pattern}' query='{query[:80]}'")
                return {
                    "safe": False,
                    "threat": "PROMPT_INJECTION",
                    "reason": f"Potential prompt injection detected: pattern matched — '{pattern}'"
                }
        return {"safe": True, "threat": None, "reason": None}

    @staticmethod
    def scan_for_blocked_topics(query: str) -> Dict[str, Any]:
        """Checks for off-limits financial crime or abuse topics."""
        query_lower = query.lower()
        for topic in BLOCKED_TOPICS:
            if topic in query_lower:
                print(f"[GUARDRAIL] Blocked topic detected: '{topic}'")
                return {
                    "safe": False,
                    "threat": "BLOCKED_TOPIC",
                    "reason": f"Query contains prohibited content: '{topic}'"
                }
        return {"safe": True, "threat": None, "reason": None}

    @staticmethod
    def check_input_length(query: str) -> Dict[str, Any]:
        """Rejects excessively long inputs to prevent token stuffing attacks."""
        if len(query) > MAX_INPUT_LENGTH:
            return {
                "safe": False,
                "threat": "TOKEN_STUFFING",
                "reason": f"Input length ({len(query)} chars) exceeds maximum allowed ({MAX_INPUT_LENGTH} chars)."
            }
        return {"safe": True, "threat": None, "reason": None}

    @staticmethod
    def validate_query(query: str) -> Dict[str, Any]:
        """Full guardrail pipeline: injection → topic → length checks."""
        for check_fn in [
            AIGuardrailService.check_input_length,
            AIGuardrailService.scan_for_injection,
            AIGuardrailService.scan_for_blocked_topics,
        ]:
            result = check_fn(query)
            if not result["safe"]:
                return result
        return {
            "safe": True,
            "threat": None,
            "reason": "All guardrail checks passed."
        }

    @staticmethod
    def sanitize_output(response: str) -> str:
        """
        Strips any system-level metadata or injected instructions from AI output
        before returning to the user.
        """
        # Remove potential leaked system prompt markers
        cleaned = re.sub(r"\[SYSTEM\].*?\[/SYSTEM\]", "", response, flags=re.DOTALL)
        cleaned = re.sub(r"(ASSISTANT:|USER:|SYSTEM:)", "", cleaned)
        return cleaned.strip()
