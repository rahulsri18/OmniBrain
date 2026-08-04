import importlib
from unittest.mock import MagicMock, patch

import pytest


# -------------------------------------------------------
# Prevent ChatOpenAI initialization during import
# -------------------------------------------------------

with patch("langchain_openai.ChatOpenAI"):
    nodes = importlib.import_module("agents.nodes")


grader_node = nodes.grader_node
query_rewriter_node = nodes.query_rewriter_node
routing_decider = nodes.routing_decider


# -------------------------------------------------------
# Helper
# -------------------------------------------------------

def create_state(
    question="What is Artificial Intelligence?",
    context=None,
    loop_count=0,
    max_loops=2,
):
    if context is None:
        context = []

    return {
        "question": question,
        "context": context,
        "metadata": {},
        "loop_count": loop_count,
        "max_loops": max_loops,
    }


# =======================================================
# Test 1
# Context exists -> Accept
# =======================================================

def test_grader_accepts_relevant_context():

    state = create_state(
        context=["Artificial Intelligence is the simulation of human intelligence."]
    )

    result = grader_node(state)

    assert result["metadata"]["grade"] == "accept"


# =======================================================
# Test 2
# Empty Context -> Retry
# =======================================================

def test_grader_retries_on_empty_context():

    state = create_state(context=[])

    result = grader_node(state)

    assert result["metadata"]["grade"] == "retry"


# =======================================================
# Test 3
# Query rewritten successfully
# =======================================================

@patch("agents.nodes.transformer")
def test_query_rewriter_updates_question(mock_transformer):

    mock_transformer.transform.return_value = MagicMock(
        rewritten_query="Explain Artificial Intelligence",
        used_fallback=False,
    )

    state = create_state()

    result = query_rewriter_node(state)

    assert result["question"] == "Explain Artificial Intelligence"
    assert result["loop_count"] == 1
    assert result["metadata"]["rewritten"] is True


# =======================================================
# Test 4
# Query rewrite fallback
# =======================================================

@patch("agents.nodes.transformer")
def test_query_rewriter_fallback(mock_transformer):

    mock_transformer.transform.return_value = MagicMock(
        rewritten_query="What is Artificial Intelligence?",
        used_fallback=True,
    )

    state = create_state()

    result = query_rewriter_node(state)

    assert result["question"] == "What is Artificial Intelligence?"
    assert result["loop_count"] == 1
    assert result["metadata"]["rewritten"] is False


# =======================================================
# Test 5
# Retry decision
# =======================================================

def test_routing_decider_retry():

    state = create_state()

    state["metadata"]["grade"] = "retry"

    decision = routing_decider(state)

    assert decision == "retry"

# =======================================================
# Test 6
# Accept decision
# =======================================================

def test_routing_decider_accept():

    state = create_state()

    state["metadata"]["grade"] = "accept"

    decision = routing_decider(state)

    assert decision == "accept"


# =======================================================
# Test 7
# Maximum retry reached
# =======================================================

def test_routing_decider_stops_at_max_loops():

    state = create_state(
        loop_count=2,
        max_loops=2,
    )

    state["metadata"]["grade"] = "retry"

    decision = routing_decider(state)

    assert decision == "accept"


# =======================================================
# Test 8
# Loop counter increments
# =======================================================

@patch("agents.nodes.transformer")
def test_loop_counter_increment(mock_transformer):

    mock_transformer.transform.return_value = MagicMock(
        rewritten_query="Explain AI",
        used_fallback=False,
    )

    state = create_state(loop_count=0)

    result = query_rewriter_node(state)

    assert result["loop_count"] == 1


# =======================================================
# Test 9
# Rewritten query differs from original
# =======================================================

@patch("agents.nodes.transformer")
def test_rewritten_query_is_different(mock_transformer):

    mock_transformer.transform.return_value = MagicMock(
        rewritten_query="Explain Artificial Intelligence",
        used_fallback=False,
    )

    state = create_state(
        question="AI"
    )

    result = query_rewriter_node(state)

    assert result["question"] != "AI"
    assert result["question"] == "Explain Artificial Intelligence"


# =======================================================
# Test 10
# Complete Self-RAG Flow
# =======================================================

@patch("agents.nodes.transformer")
def test_complete_self_rag_flow(mock_transformer):

    # --------------------------
    # Step 1
    # Initial retrieval failed
    # --------------------------

    state = create_state(
        question="AI",
        context=[],
        loop_count=0,
        max_loops=2,
    )

    graded = grader_node(state)

    assert graded["metadata"]["grade"] == "retry"

    decision = routing_decider(graded)

    assert decision == "retry"

    # --------------------------
    # Step 2
    # Rewrite Query
    # --------------------------

    mock_transformer.transform.return_value = MagicMock(
        rewritten_query="Explain Artificial Intelligence",
        used_fallback=False,
    )

    rewritten = query_rewriter_node(graded)

    assert rewritten["question"] == "Explain Artificial Intelligence"
    assert rewritten["loop_count"] == 1
    assert rewritten["metadata"]["rewritten"] is True

    # --------------------------
    # Step 3
    # Retrieval succeeds
    # --------------------------

    rewritten["context"] = [
        "Artificial Intelligence is the simulation of human intelligence."
    ]

    graded_again = grader_node(rewritten)

    assert graded_again["metadata"]["grade"] == "accept"

    decision = routing_decider(graded_again)

    assert decision == "accept"


