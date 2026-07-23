import os
from unittest import result
import pytest

if os.getenv("OPENAI_API_KEY"):

    from agents.nodes import router_node

    @pytest.mark.integration
    def test_real_supervisor():

        state = {
            "question": "Describe the uploaded image.",
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