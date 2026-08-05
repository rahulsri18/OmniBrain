import logging

from agents.langfuse_tracing import trace_node

#Test 1:Decorator returns original result

def test_trace_returns_original_result():

    @trace_node("dummy")
    def sample_node(state):
        state["value"] = 10
        return state

    state = {}

    result = sample_node(state)

    assert result["value"] == 10


#Test 2:Start log is emitted

def test_trace_logs_start(caplog):

    @trace_node("router")
    def sample_node(state):
        return state

    with caplog.at_level(logging.INFO):
        sample_node({})

    assert "[Langfuse] Starting node: router" in caplog.text

#Test 3:Finish log is emitted
def test_trace_logs_finish(caplog):

    @trace_node("router")
    def sample_node(state):
        return state

    with caplog.at_level(logging.INFO):
        sample_node({})

    assert "[Langfuse] Finished node: router" in caplog.text

#Test 4:Decorator preserves function name

def test_trace_preserves_function_name():

    @trace_node("router")
    def sample_node(state):
        return state

    assert sample_node.__name__ == "sample_node"

#Test 5:Decorator preserves docstring

def test_trace_preserves_docstring():

    @trace_node("router")
    def sample_node(state):
        """Dummy documentation."""
        return state

    assert sample_node.__doc__ == "Dummy documentation."

#Test 6:Logs both start and finish exactly once

def test_trace_logs_once(caplog):

    @trace_node("router")
    def sample_node(state):
        return state

    with caplog.at_level(logging.INFO):
        sample_node({})

    assert caplog.text.count(
        "[Langfuse] Starting node: router"
    ) == 1

    assert caplog.text.count(
        "[Langfuse] Finished node: router"
    ) == 1

#Test 7:Multiple calls should produce multiple traces

def test_multiple_calls_generate_multiple_logs(caplog):

    @trace_node("router")
    def sample_node(state):
        return state

    with caplog.at_level(logging.INFO):

        sample_node({})
        sample_node({})
        sample_node({})

    assert caplog.text.count(
        "[Langfuse] Starting node: router"
    ) == 3

    assert caplog.text.count(
        "[Langfuse] Finished node: router"
    ) == 3

#Test 8:Different node names should be logged correctly

def test_different_node_names(caplog):

    @trace_node("router")
    def router(state):
        return state

    @trace_node("grader")
    def grader(state):
        return state

    with caplog.at_level(logging.INFO):

        router({})
        grader({})

    assert "[Langfuse] Starting node: router" in caplog.text
    assert "[Langfuse] Finished node: router" in caplog.text

    assert "[Langfuse] Starting node: grader" in caplog.text
    assert "[Langfuse] Finished node: grader" in caplog.text

#Test 9:State object should remain unchanged except for node logic

def test_state_integrity():

    @trace_node("router")
    def sample_node(state):
        return state

    state = {
        "question": "What is AI?",
        "metadata": {}
    }

    result = sample_node(state)

    assert result == state

#Test 10:Exception should propagate from wrapped function

import pytest


def test_exception_propagates():

    @trace_node("router")
    def sample_node(state):
        raise RuntimeError("Node execution failed")

    with pytest.raises(RuntimeError):
        sample_node({})
