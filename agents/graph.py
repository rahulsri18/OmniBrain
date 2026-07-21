from langgraph.graph import StateGraph, END

from agents.state import GraphState
from agents.nodes import router_node


def route_query(state: GraphState):
    """
    Placeholder routing function.
    Actual supervisor routing logic will be implemented later.
    """
    return state.get("route", "end")


builder = StateGraph(GraphState)

# Register nodes
builder.add_node("router", router_node)

# Entry point
builder.set_entry_point("router")

# Conditional routing
builder.add_conditional_edges(
    "router",
    route_query,
    {
        "end": END,
    },
)

graph = builder.compile()