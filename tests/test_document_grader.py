import pytest

from backend.app.ingestion.document_grader import DocumentGrader


# --------------------------------------------------------
# Helper
# --------------------------------------------------------

def create_doc(text):
    return {
        "id": "doc1",
        "payload": {
            "text": text
        }
    }


# --------------------------------------------------------
# Mock Responses
# --------------------------------------------------------

def relevant_response(system_prompt, user_prompt):
    return """
    {
        "relevant": true,
        "score": 0.92,
        "reason": "Contains useful information."
    }
    """


def irrelevant_response(system_prompt, user_prompt):
    return """
    {
        "relevant": false,
        "score": 0.10,
        "reason": "Irrelevant."
    }
    """


# --------------------------------------------------------
# 1
# --------------------------------------------------------

def test_relevant_document():

    grader = DocumentGrader(call_fn=relevant_response)

    result = grader.grade_one(
        "What is AI?",
        create_doc("Artificial Intelligence is a branch of Computer Science.")
    )

    assert result["relevant"] is True


# --------------------------------------------------------
# 2
# --------------------------------------------------------

def test_irrelevant_document():

    grader = DocumentGrader(call_fn=irrelevant_response)

    result = grader.grade_one(
        "What is AI?",
        create_doc("Football World Cup Results")
    )

    assert result["relevant"] is False


# --------------------------------------------------------
# 3
# --------------------------------------------------------

def test_high_score():

    grader = DocumentGrader(call_fn=relevant_response)

    result = grader.grade_one(
        "AI",
        create_doc("Artificial Intelligence")
    )

    assert result["relevance_score"] == pytest.approx(0.92)


# --------------------------------------------------------
# 4
# --------------------------------------------------------

def test_threshold_equal():

    def response(system_prompt, user_prompt):
        return """
        {
            "relevant": true,
            "score": 0.50,
            "reason": "Threshold"
        }
        """

    grader = DocumentGrader(
        call_fn=response,
        relevance_threshold=0.5
    )

    result = grader.grade_one("AI", create_doc("AI"))

    assert result["relevant"] is True


# --------------------------------------------------------
# 5
# --------------------------------------------------------

def test_threshold_below():

    def response(system_prompt, user_prompt):
        return """
        {
            "relevant": true,
            "score": 0.49,
            "reason": "Below threshold"
        }
        """

    grader = DocumentGrader(
        call_fn=response,
        relevance_threshold=0.5
    )

    result = grader.grade_one("AI", create_doc("AI"))

    assert result["relevant"] is False


# --------------------------------------------------------
# 6
# --------------------------------------------------------

def test_empty_chunk():

    grader = DocumentGrader(call_fn=relevant_response)

    result = grader.grade_one(
        "AI",
        create_doc("")
    )

    assert result["relevant"] is False


# --------------------------------------------------------
# 7
# --------------------------------------------------------

def test_extract_payload_text():

    grader = DocumentGrader(call_fn=relevant_response)

    doc = {
        "payload": {
            "text": "Artificial Intelligence"
        }
    }

    result = grader.grade_one("AI", doc)

    assert result["relevant"] is True


# --------------------------------------------------------
# 8
# --------------------------------------------------------

def test_extract_payload_content():

    grader = DocumentGrader(call_fn=relevant_response)

    doc = {
        "payload": {
            "content": "Artificial Intelligence"
        }
    }

    result = grader.grade_one("AI", doc)

    assert result["relevant"] is True


# --------------------------------------------------------
# 9
# --------------------------------------------------------

def test_extract_payload_chunk():

    grader = DocumentGrader(call_fn=relevant_response)

    doc = {
        "payload": {
            "chunk": "Artificial Intelligence"
        }
    }

    result = grader.grade_one("AI", doc)

    assert result["relevant"] is True


# --------------------------------------------------------
# 10
# --------------------------------------------------------

def test_extract_doc_text():

    grader = DocumentGrader(call_fn=relevant_response)

    doc = {
        "text": "Artificial Intelligence"
    }

    result = grader.grade_one("AI", doc)

    assert result["relevant"] is True


# --------------------------------------------------------
# 11
# --------------------------------------------------------

def test_invalid_json():

    def response(system_prompt, user_prompt):
        return "INVALID JSON"

    grader = DocumentGrader(call_fn=response)

    result = grader.grade_one(
        "AI",
        create_doc("Artificial Intelligence")
    )

    assert result["relevant"] is False
    assert result["relevance_reason"] == "unparsable_grader_output"


# --------------------------------------------------------
# 12
# --------------------------------------------------------

def test_markdown_json():

    def response(system_prompt, user_prompt):
        return """```json
{
    "relevant": true,
    "score": 0.85,
    "reason": "Relevant"
}
```"""

    grader = DocumentGrader(call_fn=response)

    result = grader.grade_one(
        "AI",
        create_doc("Artificial Intelligence")
    )

    assert result["relevant"] is True
    assert result["relevance_score"] == pytest.approx(0.85)


# --------------------------------------------------------
# 13
# --------------------------------------------------------

def test_exception_defaults_to_not_relevant():

    def failing_call(system_prompt, user_prompt):
        raise RuntimeError("LLM API Error")

    grader = DocumentGrader(
        call_fn=failing_call,
        on_ungraded="not_relevant"
    )

    result = grader.grade_one(
        "Explain AI",
        create_doc("Artificial Intelligence")
    )

    assert result["relevant"] is False
    assert result["relevance_ungraded"] is True
    assert result["relevance_score"] == 0.0
    assert "ungraded_llm_error" in result["relevance_reason"]


# --------------------------------------------------------
# 14
# --------------------------------------------------------

def test_exception_defaults_to_relevant():

    def failing_call(system_prompt, user_prompt):
        raise RuntimeError("Network Timeout")

    grader = DocumentGrader(
        call_fn=failing_call,
        on_ungraded="relevant"
    )

    result = grader.grade_one(
        "Explain ML",
        create_doc("Machine Learning")
    )

    assert result["relevant"] is True
    assert result["relevance_ungraded"] is True
    assert result["relevance_score"] == 1.0
    assert "ungraded_llm_error" in result["relevance_reason"]


# --------------------------------------------------------
# 15
# --------------------------------------------------------

def test_batch_grading():

    def mock_call(system_prompt, user_prompt):

        if "Football" in user_prompt:
            return """
            {
                "relevant": false,
                "score": 0.15,
                "reason": "Irrelevant"
            }
            """

        return """
        {
            "relevant": true,
            "score": 0.91,
            "reason": "Relevant"
        }
        """

    grader = DocumentGrader(call_fn=mock_call)

    docs = [
        create_doc("Artificial Intelligence is transforming healthcare."),
        create_doc("Machine Learning improves predictions."),
        create_doc("Football World Cup final.")
    ]

    results = grader.grade_batch(
        "Explain Artificial Intelligence",
        docs
    )

    assert len(results) == 3

    assert results[0]["relevant"] is True
    assert results[1]["relevant"] is True
    assert results[2]["relevant"] is False

    for result in results:
        assert "relevant" in result
        assert "relevance_score" in result
        assert "relevance_reason" in result
        assert "relevance_ungraded" in result
        assert "grader_prompt_version" in result