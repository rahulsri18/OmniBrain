from unittest.mock import MagicMock, patch

# Import the actual module so the module-level LLM can be patched
# without depending on router_node.__globals__.
with patch("langchain_openai.ChatOpenAI") as MockLLM:
    MockLLM.return_value = MagicMock()
    import agents.nodes as nodes_module


router_node = nodes_module.router_node


class MockResponse:
    def __init__(self, content):
        self.content = content


@patch("agents.nodes.parse_retriever_output")
@patch("agents.nodes.retriever_tool")
def test_invalid_route_defaults_to_general(mock_retriever, mock_parser):

    mock_retriever.return_value = []
    mock_parser.return_value = []

    nodes_module.llm.invoke = MagicMock(
        return_value=MockResponse("unknown_route")
    )

    state = {
        "question": "Hello",
        "context": [],
    }

    result = router_node(state)

    assert result["route"] == "general"


@patch("agents.nodes.parse_retriever_output")
@patch("agents.nodes.retriever_tool")
def test_empty_query(mock_retriever, mock_parser):

    mock_retriever.return_value = []
    mock_parser.return_value = []

    nodes_module.llm.invoke = MagicMock(
        return_value=MockResponse("general")
    )

    state = {
        "question": "",
        "context": [],
    }

    result = router_node(state)

    assert result["route"] == "general"


@patch("agents.nodes.parse_retriever_output")
@patch("agents.nodes.retriever_tool")
def test_whitespace_query(mock_retriever, mock_parser):

    mock_retriever.return_value = []
    mock_parser.return_value = []

    nodes_module.llm.invoke = MagicMock(
        return_value=MockResponse("general")
    )

    state = {
        "question": "     ",
        "context": [],
    }

    result = router_node(state)

    assert result["route"] == "general"