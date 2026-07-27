import importlib
from unittest.mock import patch
import pytest

with patch("langchain_openai.ChatOpenAI"):
    nodes_module = importlib.import_module("agents.nodes")

router_node = nodes_module.router_node


@pytest.mark.integration
class TestAgentGraphRegression:

    @patch.object(nodes_module, "sql_agent_node")
    @patch.object(nodes_module, "llm")
    def test_sql_route(self, mock_llm, mock_sql):

        mock_llm.invoke.return_value.content = "sql"

        mock_sql.return_value = {
            "sql_query": "SELECT COUNT(*) FROM sales;",
            "data": [{"count": 120}],
            "error": None,
        }

        state = {
            "question": "How many sales records are there?",
            "context": [],
            "metadata": {},
        }

        result = router_node(state)

        assert result["route"] == "sql"
        assert result["metadata"]["sql_query"] == "SELECT COUNT(*) FROM sales;"
        assert result["context"] == "[{'count': 120}]"

    @patch.object(nodes_module, "llm")
    def test_vision_route(self, mock_llm):

        mock_llm.invoke.return_value.content = "vision"

        state = {
            "question": "Describe the uploaded image.",
            "context": [],
            "metadata": {},
        }

        result = router_node(state)

        assert result["route"] == "vision"

    @patch.object(nodes_module, "llm")
    def test_general_route(self, mock_llm):

        mock_llm.invoke.return_value.content = "general"

        state = {
            "question": "Hello!",
            "context": [],
            "metadata": {},
        }

        result = router_node(state)

        assert result["route"] == "general"

    @patch.object(nodes_module, "llm")
    def test_invalid_route_defaults_to_general(self, mock_llm):

        mock_llm.invoke.return_value.content = "something_random"

        state = {
            "question": "Test",
            "context": [],
            "metadata": {},
        }

        result = router_node(state)

        assert result["route"] == "general"