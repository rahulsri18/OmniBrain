import os
import pytest

if os.getenv("OPENAI_API_KEY"):

    from agents.nodes import router_node

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "question",
        [
            "Describe the uploaded image.",
            "Summarize my uploaded PDF.",
            "Show total sales by region.",
            "Hello, how are you?"
        ]
    )
    def test_real_supervisor(question):

        state = {
            "question": question,
            "context": []
        }

        result = router_node(state)

        assert "route" in result
        assert result["route"] in {
            "vision",
            "retriever",
            "sql",
            "general"
        }
        assert "context" in result

else:

    @pytest.mark.skip(reason="OPENAI_API_KEY not available")
    def test_real_supervisor():
        pass