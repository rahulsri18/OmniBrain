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
                     ↓           ↓
               Query Rewriter  Output Rail
                     ↓           ↓
                 Supervisor     END
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

    # ------------------------------------------------------
    # Hybrid = SQL + Retriever in parallel
    # ------------------------------------------------------
    if route == "hybrid":
        return ["sql", "retriever"]

    # ------------------------------------------------------
    # Individual routes
    # ------------------------------------------------------
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
        return ["fallback"]

    # Safety fallback
    return ["fallback"]


# ==========================================================
# 2. Grader Routing
# ==========================================================

def route_after_grader(state: GraphState) -> str:
    """
    Decide whether to:
        - retry retrieval using query rewriting
        - accept the current result
    """

    grade = state.get("metadata", {}).get("grade", "accept")

    loop_count = state.get("loop_count", 0)

    # Context is good
    if grade == "accept":
        return "accept"

    # Context is poor, but retry limit reached
    if loop_count >= MAX_LOOPS:
        return "accept"

    # Context is poor, retry
    return "retry"


# ==========================================================
# 3. Create Graph
# ==========================================================

builder = StateGraph(GraphState)


# ==========================================================
# 4. Register Nodes
# ==========================================================

# Entry / Safety
builder.add_node(
    "input_rail",
    input_safety_rail_node,
)

# Supervisor
builder.add_node(
    "supervisor",
    router_node,
)

# Retrieval / Execution
builder.add_node(
    "sql",
    sql_node,
)

builder.add_node(
    "retriever",
    retriever_node,
)

builder.add_node(
    "vision",
    vision_node,
)

# Merge
builder.add_node(
    "merge",
    merge_node,
)

# Self-RAG
builder.add_node(
    "grader",
    grader_node,
)

builder.add_node(
    "query_rewriter",
    query_rewriter_node,
)

# Error handling
builder.add_node(
    "fallback",
    fallback_node,
)

# Final safety
builder.add_node(
    "output_rail",
    output_validation_rail_node,
)


# ==========================================================
# 5. Entry Point
# ==========================================================

builder.set_entry_point("input_rail")


# ==========================================================
# 6. Input Safety → Supervisor
# ==========================================================

builder.add_edge(
    "input_rail",
    "supervisor",
)


# ==========================================================
# 7. Supervisor → Execution Branches
# ==========================================================

builder.add_conditional_edges(
    "supervisor",
    route_after_supervisor,
)


# ==========================================================
# 8. SQL / Retriever → Merge
#
# For normal SQL:
#
#     supervisor
#          ↓
#         SQL
#          ↓
#        merge
#
# For normal Retriever:
#
#     supervisor
#          ↓
#      Retriever
#          ↓
#        merge
#
# For Hybrid:
#
#          ┌── SQL ───────┐
# supervisor               → merge
#          └── Retriever ─┘
# ==========================================================

builder.add_edge(
    "sql",
    "merge",
)

builder.add_edge(
    "retriever",
    "merge",
)


# ==========================================================
# 9. Merge → Grader
# ==========================================================

builder.add_edge(
    "merge",
    "grader",
)


# ==========================================================
# 10. Grader → Retry / Accept
# ==========================================================

builder.add_conditional_edges(
    "grader",
    route_after_grader,
    {
        "retry": "query_rewriter",
        "accept": "output_rail",
    },
)


# ==========================================================
# 11. Query Rewriter → Supervisor
#
# The rewritten question goes back through the supervisor
# so the route can be decided again.
# ==========================================================

builder.add_edge(
    "query_rewriter",
    "supervisor",
)


# ==========================================================
# 12. Vision → Output Rail
# ==========================================================

builder.add_edge(
    "vision",
    "output_rail",
)


# ==========================================================
# 13. Fallback → Output Rail
# ==========================================================

builder.add_edge(
    "fallback",
    "output_rail",
)


# ==========================================================
# 14. Output Rail → END
# ==========================================================

builder.add_edge(
    "output_rail",
    END,
)


# ==========================================================
# 15. Compile
# ==========================================================

app_graph = builder.compile()

graph = app_graph