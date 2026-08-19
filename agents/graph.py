"""
OmniBrain LangGraph Workflow

Flow:

INPUT
  ↓
Input Safety Rail
  ↓
Supervisor / Router
  ├── SQL ───────────────┐
  ├── Retriever ─────────┤
  ├── Hybrid ──┬─ SQL ───┤
  │            └─ RAG ───┤
  ├── Vision ────────────┤
  └── General/Fallback ──┤
                         ↓
                       Merge
                         ↓
                       Grader
                      /      \
                  retry      accept
                    ↓          ↓
              Query Rewriter  Generate
                    ↓          ↓
               Supervisor   Output Rail
                               ↓
                              END
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
    generate_node,
)

from agents.guardrail import input_safety_rail_node
from agents.vision_node import vision_node
from agents.output_guardrail import output_validation_rail_node


# ==========================================================
# Configuration
# ==========================================================

MAX_LOOPS = 3


# ==========================================================
# 1. Supervisor Routing
# ==========================================================

def route_after_supervisor(state: GraphState) -> list[str]:
    """
    Decide which execution node(s) should run after the supervisor.

    Routes:
        sql       -> SQL node
        retriever -> Retriever node
        hybrid    -> SQL + Retriever in parallel
        vision    -> Vision node
        general   -> Fallback node
    """

    # If something has already failed, go directly to fallback.
    if state.get("error"):
        return ["fallback"]

    route = state.get("route", "general")

    # Hybrid = SQL + Retriever in parallel
    if route == "hybrid":
        return ["sql", "retriever"]

    # Individual routes
    if route == "sql":
        return ["sql"]

    if route == "retriever":
        return ["retriever"]

    if route == "vision":
        return ["vision"]

    # ------------------------------------------------------
    # General / unknown route
    #
    # There is currently no general_node in your project.
    # Therefore fallback is used until a proper general node
    # is added.
    # ------------------------------------------------------
    if route == "general":
        return ["retriever"]

    return ["retriever"]

# ==========================================================
# 2. Grader Routing
# ==========================================================

def route_after_grader(state: GraphState) -> str:
    grade = state.get("metadata", {}).get("grade", "accept")
    loop_count = state.get("loop_count", 0)
    max_loops = state.get("max_loops", MAX_LOOPS)

    if grade == "accept":
        return "accept"
    if loop_count >= max_loops:
        return "accept"
    return "retry"


# ==========================================================
# 3. Create Graph Builder
# ==========================================================

builder = StateGraph(GraphState)


# ==========================================================
# 4. Register Nodes
# ==========================================================

# Entry / Safety
builder.add_node("input_rail", input_safety_rail_node)

# Supervisor
builder.add_node("supervisor", router_node)

# Retrieval / Execution
builder.add_node("sql", sql_node)
builder.add_node("retriever", retriever_node)
builder.add_node("vision", vision_node)

# Merge
builder.add_node("merge", merge_node)

# Self-RAG
builder.add_node("grader", grader_node)
builder.add_node("query_rewriter", query_rewriter_node)
builder.add_node("generate", generate_node)

# Error handling
builder.add_node("fallback", fallback_node)

# Final safety
builder.add_node("output_rail", output_validation_rail_node)


# ==========================================================
# 5. Connect Edges & Flow
# ==========================================================

# Entry Point
builder.set_entry_point("input_rail")

# Input Safety → Supervisor
builder.add_edge("input_rail", "supervisor")

# Supervisor → Execution Branches
builder.add_conditional_edges("supervisor", route_after_supervisor)

# SQL / Retriever → Merge
builder.add_edge("sql", "merge")
builder.add_edge("retriever", "merge")

# Merge → Grader
builder.add_edge("merge", "grader")

# Grader → Retry / Accept
builder.add_conditional_edges(
    "grader",
    route_after_grader,
    {
        "retry": "query_rewriter",
        "accept": "generate",
    },
)

# Query Rewriter → Supervisor (loop back)
builder.add_edge("query_rewriter", "supervisor")

# Generate → Output Rail
builder.add_edge("generate", "output_rail")

# Vision → Output Rail
builder.add_edge("vision", "output_rail")

# Fallback → Output Rail
builder.add_edge("fallback", "output_rail")

# Output Rail → END
builder.add_edge("output_rail", END)


# ==========================================================
# 6. Compile Graph (STRICTLY AT THE VERY END)
# ==========================================================

app_graph = builder.compile()
graph = app_graph