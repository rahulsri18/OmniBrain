import pytest
from unittest.mock import MagicMock, patch

# Import the actual nodes module so that the module-level LLM
# can be patched without depending on router_node.__globals__.
with patch("langchain_openai.ChatOpenAI") as MockLLM:
    MockLLM.return_value = MagicMock()
    import agents.nodes as nodes_module


router_node = nodes_module.router_node


class MockResponse:
    def __init__(self, content):
        self.content = content


TEST_CASES = [
    ("Summarize the uploaded PDF document.", "retriever"),
    ("Find information from the uploaded report.", "retriever"),
    ("Search the uploaded file for diabetes.", "retriever"),
    ("Generate an SQL query to count employees.", "sql"),
    ("Show the highest salary from employee table.", "sql"),
    ("Describe the uploaded image.", "vision"),
    ("Explain what is shown in this image.", "vision"),
    ("Hello, how are you?", "general"),
    ("Tell me a joke.", "general"),
    ("What is Artificial Intelligence?", "general"),
]


@pytest.mark.parametrize(
    "query,expected_route",
    TEST_CASES,
    ids=[
        "retriever_pdf",
        "retriever_report",
        "retriever_search",
        "sql_count",
        "sql_salary",
        "vision_describe",
        "vision_explain",
        "general_greeting",
        "general_joke",
        "general_ai",
    ],
)
@patch("agents.nodes.parse_retriever_output")
@patch("agents.nodes.retriever_tool")
def test_supervisor_routing(
    mock_retriever,
    mock_parser,
    query,
    expected_route,
):
    mock_retriever.return_value = []
    mock_parser.return_value = []

    nodes_module.llm.invoke = MagicMock(
        return_value=MockResponse(expected_route)
    )

    state = {
        "question": query,
        "context": [],
    }

    result = router_node(state)

    assert result["route"] == expected_route