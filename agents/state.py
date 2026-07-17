from typing import TypedDict, List, Optional, Dict, Any, Annotated
import operator


class GraphState(TypedDict):
    """
    Shared state passed between LangGraph nodes.
    """

    # User input
    question: str

    # Conversation history
    chat_history: Annotated[List[Dict[str, str]], operator.add]

    # Retrieved context/documents
    context: Annotated[List[str], operator.add]

    # Final LLM response
    response: str

    # Selected route/node
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