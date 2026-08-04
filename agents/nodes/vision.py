"""
agents/nodes/vision.py

Vision Node updated with Day 13 Visual Guardrails.
"""

from typing import Dict, Any
# pyrefly: ignore [missing-import]
from agents.prompts.vision_prompts import VISION_SAFETY_SYSTEM_PROMPT, build_vision_user_prompt
from agents.safety.vision_sanitizer import sanitize_vision_output
from agents.state import AgentState


async def secure_vision_node(state: AgentState, vision_llm_client: Any) -> Dict[str, Any]:
    file_path = state.get("file_path")
    question = state.get("question", "Describe this image.")

    if not file_path:
        return {
            "image_error": True,
            "image_error_message": "No file path provided for visual analysis."
        }

    # Format user prompt safely
    formatted_user_prompt = build_vision_user_prompt(question)

    try:
        # Call Vision LLM using system safety prompt
        raw_response = await vision_llm_client.invoke(
            system_prompt=VISION_SAFETY_SYSTEM_PROMPT,
            user_prompt=formatted_user_prompt,
            image_path=file_path
        )

        # Sanitize extracted text for indirect prompt injections
        sanitized_content, is_injected = sanitize_vision_output(raw_response)

        return {
            "image_error": False,
            "vision_output": sanitized_content,
            "visual_injection_flagged": is_injected,
            "messages": state.get("messages", []) + [{
                "role": "assistant",
                "content": sanitized_content
            }]
        }

    except Exception as e:
        return {
            "image_error": True,
            "image_error_message": f"Vision processing error: {str(e)}"
        }