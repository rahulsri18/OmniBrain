"""
LangGraph Workflow Definition with Day 16 Parallel Branching.
"""

from langgraph.graph import StateGraph, END
from agents.state import GraphState
from agents.nodes import (
    router_node,
    sql_node,
    retriever_node,
    merge_node,
    grader_node,
    query_rewriter_node,
    routing_decider,
)
from agents.guardrail import input_safety_rail_node
from agents.vision_node import vision_node
# pyrefly: ignore [missing-import]
from agents.nodes.fallback import fallback_node
from agents.output_guardrail import output_validation_rail_node


def route_after_supervisor(state: GraphState) -> list[str]:
    """
    Returns a list of node names to enable parallel branch execution.
    If state['route'] == 'hybrid', both SQL and Retriever run in parallel!
    """
    if state.get("error"):
        return ["fallback"]

    route = state.get("route", "general")

    if route == "hybrid":
        return ["sql", "retriever"]  # Spawns parallel branches in LangGraph
    elif route == "sql":
        return ["sql"]
    elif route == "retriever":
        return ["retriever"]
    elif route == "vision":
        return ["vision"]
    
    return ["retriever"]  # Default path


builder = StateGraph(GraphState)

# 1. Register Nodes
builder.add_node("input_rail", input_safety_rail_node)
builder.add_node("supervisor", router_node)
builder.add_node("sql", sql_node)
builder.add_node("retriever", retriever_node)
builder.add_node("merge", merge_node)
builder.add_node("vision", vision_node)
builder.add_node("fallback", fallback_node)
builder.add_node("output_rail", output_validation_rail_node)

# 2. Wire Entry Point & Supervisor
builder.set_entry_point("input_rail")
builder.add_edge("input_rail", "supervisor")

# 3. Parallel Conditional Edges
builder.add_conditional_edges(
    "supervisor",
    route_after_supervisor,
    {
        "sql": "sql",
        "retriever": "retriever",
        "vision": "vision",
        "fallback": "fallback",
    },
)

# 4. Sync Branches into Merge Node
builder.add_edge("sql", "merge")
builder.add_edge("retriever", "merge")
builder.add_edge("merge", "output_rail")

builder.add_edge("vision", "output_rail")
builder.add_edge("fallback", "output_rail")
builder.add_edge("output_rail", END)

app_graph = builder.compile()
graph = app_graph