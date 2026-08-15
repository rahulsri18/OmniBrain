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

    # Retrieved context
    context: List[str]

    # Final LLM response
    response: str

    # Selected route
    route: Optional[str]

    # Error message
    error: Optional[str]

    # Additional metadata
    metadata: Dict[str, Any]

    # Parallel execution results
    sql_result: Optional[Any]
    retriever_result: Optional[List[str]]
    merged_context: Optional[List[str]]

    # Self-RAG retry tracking
    loop_count: int
    max_loops: int

    # Additional agent workflow fields
    messages: List[Dict[str, Any]]
    documents: List[Dict[str, Any]]
    rewritten_query: str
    next_step: str
    execution_status: str


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
        "sql_result": None,
        "retriever_result": None,
        "merged_context": [],
        "loop_count": 0,
        "max_loops": 3,
        "messages": [],
        "documents": [],
        "rewritten_query": "",
        "next_step": "",
        "execution_status": "",
    }


class AgentState(TypedDict, total=False):
    messages: List[Dict[str, Any]]
    file_path: Optional[str]
    question: Optional[str]
    image_error: Optional[bool]
    image_error_message: Optional[str]