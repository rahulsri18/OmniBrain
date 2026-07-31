"""
tests/test_vision_backup_prompt.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
# pyrefly: ignore [missing-import]
from agents.nodes.vision_node import execute_vision_agent


@pytest.mark.asyncio
async def test_vision_backup_prompt_rephrasing():
    # Mock LLM response
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Rephrased Summary: The image shows a revenue table with $10M in Q1 and $12M in Q2."
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    raw_unclear_text = "Q1 10M revenue... blurry text ... Q2 12M"
    question = "What is the quarterly revenue?"

    result = await execute_vision_agent(
        image_path="sample.png",
        question=question,
        vision_llm=mock_llm,
        use_backup_rephraser=True,
        raw_previous_output=raw_unclear_text
    )

    assert result["is_rephrased"] is True
    assert result["image_error"] is False
    assert "Rephrased Summary" in result["vision_output"]
    mock_llm.ainvoke.assert_called_once()