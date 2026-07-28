from langgraph.graph import StateGraph, START, END

from agents.state import GraphState
from agents.nodes import (
    router_node,
    grader_node,
    routing_decider,
)

workflow = StateGraph(GraphState)

workflow.add_node("router", router_node)
workflow.add_node("grader", grader_node)

workflow.add_edge(START, "router")
workflow.add_edge("router", "grader")

workflow.add_conditional_edges(
    "grader",
    routing_decider,
    {
        "retry": "router",
        "accept": END,
    },
)

app_graph = workflow.compile()