import importlib
from unittest.mock import patch

# ---------------------------------------------------------
# Prevent OpenAI initialization during import
# ---------------------------------------------------------

with patch("langchain_openai.ChatOpenAI"):
    graph_module = importlib.import_module("agents.graph")

route_after_supervisor = graph_module.route_after_supervisor
route_after_vision = graph_module.route_after_vision


# ---------------------------------------------------------
# Supervisor Routing
# ---------------------------------------------------------

def test_sql_route():

    state = {
        "route": "sql",
        "error": None,
    }

    assert route_after_supervisor(state) == "sql"


def test_retriever_route():

    state = {
        "route": "retriever",
        "error": None,
    }

    assert route_after_supervisor(state) == "retriever"


def test_vision_route():

    state = {
        "route": "vision",
        "error": None,
    }

    assert route_after_supervisor(state) == "vision"


def test_general_route():

    state = {
        "route": "general",
        "error": None,
    }

    assert route_after_supervisor(state) == "general"


def test_invalid_route_defaults_to_general():

    state = {
        "route": "xyz",
        "error": None,
    }

    assert route_after_supervisor(state) == "general"


def test_missing_route_defaults_to_general():

    state = {
        "error": None,
    }

    assert route_after_supervisor(state) == "general"


def test_error_goes_to_fallback():

    state = {
        "route": "sql",
        "error": "Database Error",
    }

    assert route_after_supervisor(state) == "fallback"


# ---------------------------------------------------------
# Vision Routing
# ---------------------------------------------------------

def test_vision_success():

    state = {
        "image_error": False,
        "error": None,
    }

    assert route_after_vision(state) == "end"


def test_vision_image_error():

    state = {
        "image_error": True,
        "error": None,
    }

    assert route_after_vision(state) == "fallback"


def test_vision_runtime_error():

    state = {
        "image_error": False,
        "error": "OCR Failed",
    }

    assert route_after_vision(state) == "fallback"