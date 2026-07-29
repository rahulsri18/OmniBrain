from typing import TypedDict, List, Optional, Dict, Any, Annotated
import operator


class GraphState(TypedDict):
    """
    Shared state passed between LangGraph nodes.
    """
    # User input
    question: str

    # Conversation history (Append-only)
    chat_history: Annotated[List[Dict[str, str]], operator.add]

    # Retrieved context/documents (Append-only)
    context: Annotated[List[str], operator.add]

    # Final LLM response
    response: str

    # Selected route/node (Supervisor Node के लिए ज़रूरी)
    route: Optional[str]

    # Error message (if any)
    error: Optional[str]

    # Additional metadata
    metadata: Dict[str, Any]


def create_initial_state(question: str) -> GraphState:
    """
    Create the default state for every new query.
    """
    return {
        "question": question,
        "chat_history": [],
        "context": [],
        "response": "",
        "route": None,
        "error": None,
        "metadata": {},
    }
from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict, total=False):
    messages: List[Dict[str, Any]]
    file_path: Optional[str]
    question: Optional[str]
    # Day 11 Addition for Vision Quality Check:
    image_error: Optional[bool]
    image_error_message: Optional[str]
    """
agents/state.py

Defines the shared state schema across all agent nodes in LangGraph.
"""

from typing import Any, Dict, List, TypedDict


class GraphState(TypedDict):
    messages: List[Dict[str, Any]]
    question: str
    documents: List[Dict[str, Any]]
    rewritten_query: str
    error: str
    loop_count: int  # Day 12: Tracks retry/rewrite loop executions
    next_step: str
    execution_status: str