
# agents/graph.py
"""
LangGraph Workflow Definition & Compiler.

Single source of truth for the OmniBrain agent graph:
- One state schema (agents.state.GraphState)
- One StateGraph instance
- Supervisor node is the entry point (NOT fallback)
- Conditional routing to retriever / sql / vision / general
- Fallback node only triggers on error, not as the default path
"""

from langgraph.graph import StateGraph, END

from agents.state import GraphState
from agents.nodes import (
    router_node,
    sql_node,
    retriever_node,
    merge_node,
    grader_node,
    routing_decider,
    query_rewriter_node,
)

from agents.guardrail import input_safety_rail_node
from agents.vision_node import vision_node
# pyrefly: ignore [missing-import]
from agents.nodes.fallback import fallback_node
from agents.output_guardrail import output_validation_rail_node


# ---------------------------------------------------------------------------
# 1. Routing logic
# ---------------------------------------------------------------------------

def route_after_supervisor(state: GraphState) -> str:
    """
    Reads the 'route' value set by router_node and sends execution to the
    matching node. Falls back safely to 'general' if the route is missing
    or not recognized, and to 'fallback' if an error was captured upstream.
    """
    if state.get("error"):
        return "fallback"

    route = state.get("route", "general")

    valid_routes = {"retriever", "sql", "vision", "general"}
    if route not in valid_routes:
        return "general"

    return route


def route_after_vision(state: GraphState) -> str:
    """
    After the vision node runs, decide whether to end normally or divert
    to the fallback node (e.g. blurry image / unreadable chart).
    """
    if state.get("error") or state.get("image_error"):
        return "fallback"
    return "end"


# ---------------------------------------------------------------------------
# 2. Build the graph
# ---------------------------------------------------------------------------

builder = StateGraph(GraphState)

# Register every node exactly once, on the one graph object.
builder.add_node("input_rail", input_safety_rail_node)
builder.add_node("supervisor", router_node)
builder.add_node("vision", vision_node)
builder.add_node("fallback", fallback_node)
builder.add_node("output_rail", output_validation_rail_node)
builder.add_edge("output_rail", END)

# NOTE: "retriever" and "sql" are currently handled *inside* router_node
# itself (see agents/nodes.py), not as separate graph nodes. They route
# straight to END below. If/when they're split into standalone nodes,
# add them here with builder.add_node(...) and point the conditional
# edges at those names instead of END.

builder.set_entry_point("input_rail")
builder.add_edge("input_rail", "supervisor")

builder.add_conditional_edges(
    "supervisor",
    route_after_supervisor,
    {
        "retriever": "output_rail",
        "sql": "output_rail",
        "vision": "vision",
        "general": "output_rail",
        "fallback": "fallback",
    },
)

builder.add_conditional_edges(
    "vision",
    route_after_vision,
    {
        "end": "output_rail",
        "fallback": "fallback",
    },
)

builder.add_edge("fallback", "output_rail")
builder.add_edge("output_rail", END)

# ---------------------------------------------------------------------------
# 3. Compile once
# ---------------------------------------------------------------------------

app_graph = builder.compile()
graph = app_graph  # backwards-compatible alias, in case other files import `graph`
