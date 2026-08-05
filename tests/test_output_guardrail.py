import pytest

from agents.output_guardrail import output_validation_rail_node

def create_state(
    answer="Artificial Intelligence is the simulation of human intelligence.",
    blocked=False,
    error=None,
):
    state = {
        "answer": answer,
        "metadata": {
            "blocked": blocked
        }
    }

    if error is not None:
        state["error"] = error

    return state

#Test 1:Valid answer should pass
def test_valid_answer_passes():

    state = create_state()

    result = output_validation_rail_node(state)

    assert result["metadata"]["output_blocked"] is False

    assert (
        result["answer"]
        == "Artificial Intelligence is the simulation of human intelligence."
    )

#Test 2:Empty answer

def test_empty_answer_blocked():

    state = create_state(
        answer=""
    )

    result = output_validation_rail_node(state)

    assert result["metadata"]["output_blocked"] is True

    assert (
        result["answer"]
        == "I'm unable to provide a reliable response for this request."
    )

#Test 3:Whitespace answer

def test_whitespace_answer_blocked():

    state = create_state(
        answer="      "
    )

    result = output_validation_rail_node(state)

    assert result["metadata"]["output_blocked"] is True

    assert (
        result["answer"]
        == "I'm unable to provide a reliable response for this request."
    )

#Test 4:Existing error should block the response

def test_existing_error_blocks_output():

    state = create_state(
        error="Hallucination detected"
    )

    result = output_validation_rail_node(state)

    assert result["metadata"]["output_blocked"] is True

    assert (
        result["answer"]
        == "I'm unable to provide a reliable response for this request."
    )

#Test 5:Previously blocked input should block the output

def test_previously_blocked_input():

    state = create_state(
        blocked=True
    )

    result = output_validation_rail_node(state)

    assert result["metadata"]["output_blocked"] is True

    assert (
        result["answer"]
        == "I'm unable to provide a reliable response for this request."
    )

#Test 6 : Blocked input with an existing answer should replace the answer

def test_blocked_input_replaces_answer():

    state = create_state(
        answer="This is a fabricated answer.",
        blocked=True
    )

    result = output_validation_rail_node(state)

    assert result["metadata"]["output_blocked"] is True

    assert (
        result["answer"]
        == "I'm unable to provide a reliable response for this request."
    )

#Test 7:Existing error with an answer should also replace the answer

def test_error_replaces_answer():

    state = create_state(
        answer="Incorrect answer.",
        error="Unsafe response"
    )

    result = output_validation_rail_node(state)

    assert result["metadata"]["output_blocked"] is True

    assert (
        result["answer"]
        == "I'm unable to provide a reliable response for this request."
    )

#Test 8:Safe answer should remain unchanged
def test_safe_answer_remains_unchanged():

    answer = (
        "Machine Learning is a subset of Artificial Intelligence."
    )

    state = create_state(
        answer=answer
    )

    result = output_validation_rail_node(state)

    assert result["metadata"]["output_blocked"] is False
    assert result["answer"] == answer

#Test 9:Existing metadata should be preserved
def test_existing_metadata_preserved():

    state = create_state()

    state["metadata"]["source"] = "RAG"
    state["metadata"]["confidence"] = 0.95

    result = output_validation_rail_node(state)

    assert result["metadata"]["output_blocked"] is False
    assert result["metadata"]["source"] == "RAG"
    assert result["metadata"]["confidence"] == 0.95

#Test 10:False Positive Test (Correct answer should NOT be blocked)

def test_false_positive_rate():

    state = create_state(
        answer=(
            "Artificial Intelligence enables machines to "
            "perform tasks that normally require human intelligence."
        )
    )

    result = output_validation_rail_node(state)

    assert result["metadata"]["output_blocked"] is False

    assert (
        result["answer"]
        == "Artificial Intelligence enables machines to "
           "perform tasks that normally require human intelligence."
    )