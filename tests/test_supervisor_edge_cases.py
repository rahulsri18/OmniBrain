from unittest.mock import MagicMock, patch

with patch("langchain_openai.ChatOpenAI") as MockLLM:
    MockLLM.return_value = MagicMock()
    from agents.nodes import router_node


class MockResponse:
    def __init__(self, content):
        self.content = content


@patch("agents.nodes.parse_retriever_output")
@patch("agents.nodes.retriever_tool")
def test_invalid_route_defaults_to_general(mock_retriever, mock_parser):

    mock_retriever.return_value = []
    mock_parser.return_value = []

    router_node.__globals__["llm"].invoke = MagicMock(
        return_value=MockResponse("unknown_route")
    )

    state = {
        "question": "Hello",
        "context": []
    }

    result = router_node(state)

    assert result["route"] == "general"


@patch("agents.nodes.parse_retriever_output")
@patch("agents.nodes.retriever_tool")
def test_empty_query(mock_retriever, mock_parser):

    mock_retriever.return_value = []
    mock_parser.return_value = []

    router_node.__globals__["llm"].invoke = MagicMock(
        return_value=MockResponse("general")
    )

    state = {
        "question": "",
        "context": []
    }

    result = router_node(state)

    assert result["route"] == "general"


@patch("agents.nodes.parse_retriever_output")
@patch("agents.nodes.retriever_tool")
def test_whitespace_query(mock_retriever, mock_parser):

    mock_retriever.return_value = []
    mock_parser.return_value = []

    router_node.__globals__["llm"].invoke = MagicMock(
        return_value=MockResponse("general")
    )

    state = {
        "question": "     ",
        "context": []
    }

    result = router_node(state)

    assert result["route"] == "general"