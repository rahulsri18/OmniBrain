
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
from agents.nodes import router_node
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
"""
agents/graph.py

Configures nodes, conditional edges, and the Max Loop filter (Max Loop = 3).
"""

from typing import Any, Dict
from langgraph.graph import END, StateGraph

# pyrefly: ignore [missing-import
from OmniBrain.agents.nodes.fallback import fallback_node
# Import your other nodes here (e.g., retriever_node, grader_node, transformer_node, generate_node)

MAX_LOOPS = 3


def decide_to_generate_or_rewrite(state: Dict[str, Any]) -> str:
    """
    Conditional edge router for Day 12:
    Evaluates document relevance and enforces Max Loop = 3.
    """
    loop_count = state.get("loop_count", 0)
    documents = state.get("documents", [])
    
    # Check if any documents are relevant (using M7's grading flag or count)
    has_relevant_docs = any(doc.get("relevant", False) for doc in documents)

    if has_relevant_docs:
        print("---DECISION: DOCS ARE RELEVANT -> GENERATE---")
        return "generate"

    # Enforce Maximum Loop Limit (Max Loop = 3)
    if loop_count >= MAX_LOOPS:
        print(f"---DECISION: MAX LOOPS ({MAX_LOOPS}) REACHED -> GENERATE WITH FALLBACK CONTEXT---")
        return "generate_fallback"

    print(f"---DECISION: NO RELEVANT DOCS (Attempt {loop_count + 1}/{MAX_LOOPS}) -> REWRITE QUERY---")
    return "transform_query"


def increment_loop_count(state: Dict[str, Any]) -> Dict[str, Any]:
    """Helper node or inline state update to increment loop count prior to re-querying."""
    current_count = state.get("loop_count", 0)
    return {
        **state,
        "loop_count": current_count + 1
    }
    # Create Workflow
workflow = StateGraph(GraphState)

# Add Nodes
# workflow.add_node("retrieve", retrieve_node)
# workflow.add_node("grade_documents", grade_documents_node)
# workflow.add_node("transform_query", transform_query_node)
# workflow.add_node("generate", generate_node)
workflow.add_node("fallback", fallback_node)

# Set Entry Point
# workflow.set_entry_point("retrieve")

# Add Conditional Edge from Grader to next step
# workflow.add_conditional_edges(
#     "grade_documents",
#     decide_to_generate_or_rewrite,
#     {
#         "generate": "generate",
#         "transform_query": "transform_query",
#         "generate_fallback": "generate",  # Proceeds to generate using best available context or fallback
#     },
# )

# workflow.add_edge("transform_query", "retrieve")
# workflow.add_edge("generate", END)

# Compile with recursion limit protection
app_graph = workflow.compile()
