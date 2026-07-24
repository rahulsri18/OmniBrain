"""
vision_fallback.py

Day 8 - M4 Task:
Backup error-handler node and safe wrapper for Vision model execution.
Prevents app crashes on vision processing failures.
"""

from typing import Dict, Any, Optional
from app.logger import logger


def vision_error_handler_node(state: Dict[str, Any], error_message: str) -> Dict[str, Any]:
    """
    Fallback node executed when vision processing fails.
    Populates state with a friendly user message and logs telemetry.
    """
    logger.error(f"Vision Fallback Triggered | Reason: {error_message}")

    fallback_response = (
        "⚠️ **Vision Processing Unavailable**\n\n"
        "We encountered an issue while analyzing the attached image. "
        "The file might be corrupted, unsupported, or the vision model service is temporarily unreachable.\n\n"
        "*Tip: You can continue asking text-based questions or try re-uploading a clear PNG/JPEG image.*"
    )

    # State update without crashing
    state["context"] = "Vision processing failed."
    state["fallback_triggered"] = True
    state["error"] = error_message
    
    # Store clean fallback response in state metadata
    if "metadata" not in state or state["metadata"] is None:
        state["metadata"] = {}
    
    state["metadata"]["vision_error"] = error_message
    state["metadata"]["fallback_response"] = fallback_response

    return state


def safe_vision_execution_wrapper(vision_func):
    """
    Decorator / Safe Execution Wrapper for Vision Sub-Agent nodes.
    Catches any runtime exception and reroutes to vision_error_handler_node.
    """
    def wrapper(state: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
        file_path: Optional[str] = state.get("file_path")

        # 1. Validation Check: Ensure file exists/provided
        if not file_path:
            logger.warning("Vision node invoked without an attached file_path.")
            return vision_error_handler_node(state, "No image file provided for vision analysis.")

        # 2. Attempt Vision Function Execution
        try:
            return vision_func(state, *args, **kwargs)
            
        except FileNotFoundError as fnf_err:
            return vision_error_handler_node(state, f"Image file not found: {str(fnf_err)}")
            
        except ValueError as val_err:
            return vision_error_handler_node(state, f"Invalid image format/dimensions: {str(val_err)}")
            
        except Exception as exc:
            # Catch API failures, CUDA OOM, unexpected errors
            return vision_error_handler_node(state, f"Unhandled vision error: {str(exc)}")

    return wrapper