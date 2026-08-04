"""
test_supervisor_integration.py

Day 9 - M3 Task:
Integration tests for Supervisor Node routing.
"""

import os
import pytest

if os.getenv("OPENAI_API_KEY"):

    from agents.nodes import router_node

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "question, expected_route",
        [
            ("Describe the uploaded image.", "vision"),
            ("Summarize my uploaded PDF.", "retriever"),
            ("Show total sales by region.", "sql"),
            ("Count the number of active customers in the database.", "sql"),
            ("What does page 5 of the contract say about numbers?", "retriever"),  # Explicit test for numerical doc queries
            ("Hello, how are you?", "general")
        ]
    )
    def test_real_supervisor(question, expected_route):
        state = {
            "question": question,
            "context": []
        }

        result = router_node(state)

        assert "route" in result
        # 🎯 Strict Route Match Assertion
        assert result["route"] == expected_route, f"Expected {expected_route} for question '{question}', but got {result['route']}"
        assert "context" in result

else:

    @pytest.mark.skip(reason="OPENAI_API_KEY not available for integration tests")
    def test_real_supervisor():
        pass