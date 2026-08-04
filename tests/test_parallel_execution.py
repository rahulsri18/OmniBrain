"""
tests/test_parallel_execution.py
"""

from agents.nodes import merge_node
from agents.state import create_initial_state


def test_merge_node_combines_sql_and_retriever():
    state = create_initial_state(question="What was Q3 revenue and customer count?")
    state["sql_result"] = "SELECT COUNT(*) FROM customers; -> 1450"
    state["retriever_result"] = ["Q3 financial report shows $12M revenue."]

    updated_state = merge_node(state)

    assert len(updated_state["context"]) == 2
    assert "1450" in updated_state["context"][1]
    assert "$12M" in updated_state["context"][0]