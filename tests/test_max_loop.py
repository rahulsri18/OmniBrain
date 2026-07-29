"""
tests/test_max_loop.py
"""

import pytest
from agents.graph import decide_to_generate_or_rewrite, MAX_LOOPS


def test_router_allows_rewrite_under_max_loops():
    state = {
        "loop_count": 1,
        "documents": [{"relevant": False}]
    }
    decision = decide_to_generate_or_rewrite(state)
    assert decision == "transform_query"


def test_router_triggers_fallback_at_max_loops():
    state = {
        "loop_count": 3,
        "documents": [{"relevant": False}]
    }
    decision = decide_to_generate_or_rewrite(state)
    assert decision == "generate_fallback"


def test_router_proceeds_when_docs_are_relevant():
    state = {
        "loop_count": 1,
        "documents": [{"relevant": True}]
    }
    decision = decide_to_generate_or_rewrite(state)
    assert decision == "generate"