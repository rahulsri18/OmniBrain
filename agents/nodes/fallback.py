"""
backend/app/agents/nodes/fallback.py

Fallback node triggered when node/graph execution captures a fatal error.
"""

from typing import Any, Dict
from langchain_core.messages import AIMessage


async def fallback_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handles graceful recovery when upstream nodes fail or route to error states.
    """
    error_detail = state.get("error", "An unexpected runtime error occurred.")

    fallback_message = (
        "I encountered a temporary glitch while processing your request. "
        "I have captured the execution error and saved the current session state. "
        "Please try rephrasing your prompt or uploading the document again."
    )

    messages = state.get("messages", [])
    messages.append(AIMessage(content=fallback_message))

    return {
        **state,
        "messages": messages,
        "error": error_detail,
        "execution_status": "failed_gracefully",
    }


async def fallback_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handles graceful recovery when upstream nodes fail or route to error states.
    """
    error_detail = state.get("error", "An unexpected runtime error occurred.")

    fallback_message = (
        "I encountered a temporary glitch while processing your request. "
        "I have captured the execution error and saved the current session state. "
        "Please try rephrasing your prompt or uploading the document again."
    )

    messages = state.get("messages", [])
    messages.append(AIMessage(content=fallback_message))

    return {
        **state,
        "messages": messages,
        "error": error_detail,
        "execution_status": "failed_gracefully",
    }