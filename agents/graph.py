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
    fallback_node,
    routing_decider,
)
from agents.guardrail import input_safety_rail_node
from agents.vision_node import vision_node
# pyrefly: ignore [missing-import]
from agents.output_guardrail import output_validation_rail_node

import importlib.util
from pathlib import Path

MAX_LOOPS = 3


def decide_to_generate_or_rewrite(state: GraphState) -> str:
    """
    Day 19 - Self-RAG loop routing.

    Decides whether the workflow should generate a response,
    rewrite the query for another retrieval attempt, or fall
    back after reaching the maximum retry limit.
    """

    documents = state.get("documents", [])
    loop_count = state.get("loop_count", 0)

    # If relevant documents are available, proceed to generation.
    if any(document.get("relevant", False) for document in documents):
        return "generate"

    # Stop retrying once the maximum loop count is reached.
    if loop_count >= MAX_LOOPS:
        return "generate_fallback"

    # Otherwise rewrite the query and retry retrieval.
    return "transform_query"


# ---------------------------------------------------------------------------
# 1. Routing logic
# ---------------------------------------------------------------------------

_fallback_path = Path(__file__).parent / "nodes" / "fallback.py"
_fallback_spec = importlib.util.spec_from_file_location(
    "agents_fallback_node",
    _fallback_path,
)

if _fallback_spec is None or _fallback_spec.loader is None:
    raise ImportError(f"Unable to load fallback node from {_fallback_path}")

_fallback_module = importlib.util.module_from_spec(_fallback_spec)
_fallback_spec.loader.exec_module(_fallback_module)

fallback_node = _fallback_module.fallback_node

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
builder.add_node("grader", grader_node)
builder.add_node("query_rewriter", query_rewriter_node)
builder.add_node("vision", vision_node)
builder.add_node("fallback", fallback_node)
builder.add_node("output_rail", output_validation_rail_node)

# NOTE: "retriever" and "sql" are currently handled *inside* router_node
# itself (see agents/nodes.py), not as separate graph nodes. They route
# straight to END below. If/when they're split into standalone nodes,
# add them here with builder.add_node(...) and point the conditional
# edges at those names instead of END.
builder.add_node("sql", sql_node)
builder.add_node("retriever", retriever_node)
builder.add_node("merge", merge_node)


# 2. Wire Entry Point & Supervisor
builder.set_entry_point("input_rail")
builder.add_edge("input_rail", "supervisor")

# 3. Parallel Conditional Edges
builder.add_conditional_edges(
    "supervisor",
    route_after_supervisor,
    {
        "retriever": "grader",
        "sql": "output_rail",
        "sql": "sql",
        "retriever": "retriever",
        "vision": "vision",
        "fallback": "fallback",
    },
)
builder.add_conditional_edges(
    "grader",
    routing_decider,
    {
        "retry": "query_rewriter",
        "accept": "output_rail",
    },
)

builder.add_edge("query_rewriter", "supervisor")

# 4. Sync Branches into Merge Node
builder.add_edge("sql", "merge")
builder.add_edge("retriever", "merge")
builder.add_edge("merge", "output_rail")

builder.add_edge("vision", "output_rail")
builder.add_edge("fallback", "output_rail")
builder.add_edge("output_rail", END)

app_graph = builder.compile()
graph = app_graph