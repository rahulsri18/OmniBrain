import pytest

from backend.app.config import settings

if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "mock-key-for-test":
    pytest.skip(
        "A real OPENAI_API_KEY is not configured.",
        allow_module_level=True,
    )

from agents.graph import app_graph
from agents.state import create_initial_state


@pytest.mark.integration
def test_production_agent_graph_smoke():
    """Run the complete agent graph with configured Gemini credentials."""

    state = create_initial_state(
        "Give me a brief summary of the uploaded document."
    )

    result = app_graph.invoke(state)

    assert result is not None
    assert "route" in result
    assert "response" in result
    assert "metadata" in result