from agents.state import GraphState
from agents.retriever import retriever_tool


def router_node(state: GraphState) -> GraphState:
    """
    Decide which route to take based on the user query.
    """
    return state


def retrieve_node(state: GraphState) -> GraphState:
    """
    Retrieve relevant context/documents.
    """

    query = state["question"]

    documents = retriever_tool(query)

    state["context"] = documents

    return state


def generate_node(state: GraphState) -> GraphState:
    """
    Generate the final response.
    """
    return state