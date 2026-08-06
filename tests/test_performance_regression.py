import pytest


BASELINE = {
    "search_latency_ms": 145,
    "chat_latency_ms": 320,
    "vision_latency_ms": 890,
    "error_rate": 0.12,
}


CURRENT = {
    "search_latency_ms": 145,
    "chat_latency_ms": 315,
    "vision_latency_ms": 875,
    "error_rate": 0.08,
}


MAX_REGRESSION = 0.10


def regression(old, new):
    return (new - old) / old


def test_search_latency():

    change = regression(
        BASELINE["search_latency_ms"],
        CURRENT["search_latency_ms"],
    )

    assert change <= MAX_REGRESSION


def test_chat_latency():

    change = regression(
        BASELINE["chat_latency_ms"],
        CURRENT["chat_latency_ms"],
    )

    assert change <= MAX_REGRESSION


def test_vision_latency():

    change = regression(
        BASELINE["vision_latency_ms"],
        CURRENT["vision_latency_ms"],
    )

    assert change <= MAX_REGRESSION


def test_error_rate():

    assert CURRENT["error_rate"] <= BASELINE["error_rate"]


def test_search_improved():

    assert (
        CURRENT["search_latency_ms"]
        <= BASELINE["search_latency_ms"]
    )


def test_chat_improved():

    assert (
        CURRENT["chat_latency_ms"]
        <= BASELINE["chat_latency_ms"]
    )


def test_vision_improved():

    assert (
        CURRENT["vision_latency_ms"]
        <= BASELINE["vision_latency_ms"]
    )


def test_error_rate_improved():

    assert (
        CURRENT["error_rate"]
        <= BASELINE["error_rate"]
    )


def test_overall_regression():

    assert all([
        CURRENT["search_latency_ms"] <= BASELINE["search_latency_ms"] * 1.10,
        CURRENT["chat_latency_ms"] <= BASELINE["chat_latency_ms"] * 1.10,
        CURRENT["vision_latency_ms"] <= BASELINE["vision_latency_ms"] * 1.10,
        CURRENT["error_rate"] <= BASELINE["error_rate"],
    ])


def test_regression_summary():

    summary = {
        "search": CURRENT["search_latency_ms"],
        "chat": CURRENT["chat_latency_ms"],
        "vision": CURRENT["vision_latency_ms"],
        "error_rate": CURRENT["error_rate"],
    }

    assert summary["search"] == 145
    assert summary["chat"] == 315
    assert summary["vision"] == 875
    assert summary["error_rate"] == 0.08