"""
agents/safety/vision_sanitizer.py

Sanitizes text returned by Vision Models to prevent indirect prompt injection attacks.
"""

from typing import Tuple, Optional
from agents.safety.ban_list import get_keywords

INJECTION_PATTERNS = get_keywords("prompt_injection") + (
    "system prompt",
    "developer mode",
    "ignore above",
    "new rule:",
    "admin override",
)

def sanitize_vision_output(extracted_text: str) -> Tuple[str, bool]:
    """
    Scans visual extraction for injected prompt instructions.
    
    Returns:
        (sanitized_text, injection_detected_flag)
    """
    lowered = extracted_text.lower()
    injection_detected = False

    for pattern in INJECTION_PATTERNS:
        if pattern in lowered:
            injection_detected = True
            # Strip out or neutralize suspected injection lines
            extracted_text = extracted_text.replace(pattern, f"[REDACTED_INJECTION: {pattern}]")

    return extracted_text, injection_detected