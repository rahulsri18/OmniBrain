from langgraph.graph import StateGraph, END

from agents.state import GraphState
from agents.nodes import router_node


def route_query(state: GraphState):
    return state.get("route", "general")


builder = StateGraph(GraphState)

builder.add_node("router", router_node)

builder.set_entry_point("router")

builder.add_conditional_edges(
    "router",
    route_query,
    {
        "retriever": END,
        "sql": END,
        "vision": END,
        "general": END,
    },
)

graph = builder.compile()