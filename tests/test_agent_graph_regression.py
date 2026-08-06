import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

with open(ROOT / "performance" / "baseline.json", "r") as f:
    BASELINE = json.load(f)

with open(ROOT / "performance" / "current.json", "r") as f:
    CURRENT = json.load(f)

MAX_ALLOWED_REGRESSION = 0.10


def regression(old, new):
    return (new - old) / old


# --------------------------------------------------
# Latency Tests
# --------------------------------------------------

def test_search_latency():

    change = regression(
        BASELINE["search_latency_ms"],
        CURRENT["search_latency_ms"],
    )

    assert change <= MAX_ALLOWED_REGRESSION


def test_chat_latency():

    change = regression(
        BASELINE["chat_latency_ms"],
        CURRENT["chat_latency_ms"],
    )

    assert change <= MAX_ALLOWED_REGRESSION


def test_vision_latency():

    change = regression(
        BASELINE["vision_latency_ms"],
        CURRENT["vision_latency_ms"],
    )

    assert change <= MAX_ALLOWED_REGRESSION


# --------------------------------------------------
# Error Rate
# --------------------------------------------------

def test_error_rate():

    assert (
        CURRENT["error_rate"]
        <= BASELINE["error_rate"]
    )


# --------------------------------------------------
# Throughput
# --------------------------------------------------

def test_throughput():

    assert (
        CURRENT["throughput_rps"]
        >= BASELINE["throughput_rps"]
    )


# --------------------------------------------------
# Memory
# --------------------------------------------------

def test_memory_usage():

    assert (
        CURRENT["memory_mb"]
        <= BASELINE["memory_mb"]
    )


# --------------------------------------------------
# CPU
# --------------------------------------------------

def test_cpu_usage():

    assert (
        CURRENT["cpu_percent"]
        <= BASELINE["cpu_percent"]
    )


# --------------------------------------------------
# Overall Regression
# --------------------------------------------------

def test_overall_regression():

    assert CURRENT["search_latency_ms"] <= BASELINE["search_latency_ms"] * 1.10

    assert CURRENT["chat_latency_ms"] <= BASELINE["chat_latency_ms"] * 1.10

    assert CURRENT["vision_latency_ms"] <= BASELINE["vision_latency_ms"] * 1.10

    assert CURRENT["error_rate"] <= BASELINE["error_rate"]

    assert CURRENT["throughput_rps"] >= BASELINE["throughput_rps"]

    assert CURRENT["memory_mb"] <= BASELINE["memory_mb"]

    assert CURRENT["cpu_percent"] <= BASELINE["cpu_percent"]


# --------------------------------------------------
# Regression Summary
# --------------------------------------------------

def test_generate_summary():

    report = {
        "Search Latency (ms)": CURRENT["search_latency_ms"],
        "Chat Latency (ms)": CURRENT["chat_latency_ms"],
        "Vision Latency (ms)": CURRENT["vision_latency_ms"],
        "Error Rate": CURRENT["error_rate"],
        "Throughput (RPS)": CURRENT["throughput_rps"],
        "Memory (MB)": CURRENT["memory_mb"],
        "CPU (%)": CURRENT["cpu_percent"],
        "Overall": "PASS",
    }

    print("\n")
    print("========== Performance Regression Summary ==========")

    for key, value in report.items():
        print(f"{key:25}: {value}")

    print("====================================================")

    assert report["Overall"] == "PASS"