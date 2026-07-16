from agents.state import GraphState


def router_node(state: GraphState) -> GraphState:
    """
    Decide which route to take based on the user query.
    """
    return state


def retrieve_node(state: GraphState) -> GraphState:
    """
    Retrieve relevant context/documents.
    """
    return state


def generate_node(state: GraphState) -> GraphState:
    """
    Generate the final response.
    """
    return state