import importlib
from unittest.mock import patch


# ---------------------------------------------------------
# Prevent OpenAI initialization during test collection
# ---------------------------------------------------------

with patch("langchain_openai.ChatOpenAI"):
    graph_module = importlib.import_module("agents.graph")


route_after_supervisor = graph_module.route_after_supervisor


# ---------------------------------------------------------
# Supervisor Routing Tests
# ---------------------------------------------------------

def test_sql_route():
    state = {
        "route": "sql",
        "error": None,
    }

    result = route_after_supervisor(state)

    assert result == ["sql"]


def test_retriever_route():
    state = {
        "route": "retriever",
        "error": None,
    }

    result = route_after_supervisor(state)

    assert result == ["retriever"]


def test_vision_route():
    state = {
        "route": "vision",
        "error": None,
    }

    result = route_after_supervisor(state)

    assert result == ["vision"]


def test_general_route_defaults_to_retriever():
    state = {
        "route": "general",
        "error": None,
    }

    result = route_after_supervisor(state)

    assert result == ["retriever"]


def test_invalid_route_defaults_to_retriever():
    state = {
        "route": "xyz",
        "error": None,
    }

    result = route_after_supervisor(state)

    assert result == ["retriever"]


def test_missing_route_defaults_to_retriever():
    state = {
        "error": None,
    }

    result = route_after_supervisor(state)

    assert result == ["retriever"]


# ---------------------------------------------------------
# Error Routing Tests
# ---------------------------------------------------------

def test_error_goes_to_fallback():
    state = {
        "route": "sql",
        "error": "Database Error",
    }

    result = route_after_supervisor(state)

    assert result == ["fallback"]


def test_error_has_priority_over_route():
    state = {
        "route": "vision",
        "error": "Vision processing failed",
    }

    result = route_after_supervisor(state)

    assert result == ["fallback"]


# ---------------------------------------------------------
# Hybrid Routing
# ---------------------------------------------------------

def test_hybrid_route():
    state = {
        "route": "hybrid",
        "error": None,
    }

    result = route_after_supervisor(state)

    assert result == ["sql", "retriever"]


# ---------------------------------------------------------
# Route Result Type
# ---------------------------------------------------------

def test_route_result_is_list():
    states = [
        {
            "route": "sql",
            "error": None,
        },
        {
            "route": "retriever",
            "error": None,
        },
        {
            "route": "vision",
            "error": None,
        },
        {
            "route": "general",
            "error": None,
        },
    ]

    for state in states:
        result = route_after_supervisor(state)

        assert isinstance(result, list)
        assert len(result) >= 1


# ---------------------------------------------------------
# Valid Route Coverage
# ---------------------------------------------------------

def test_all_supported_routes():
    expected_routes = {
        "sql": ["sql"],
        "retriever": ["retriever"],
        "vision": ["vision"],
        "hybrid": ["sql", "retriever"],
        "general": ["retriever"],
    }

    for route, expected in expected_routes.items():
        state = {
            "route": route,
            "error": None,
        }

        assert route_after_supervisor(state) == expected