"""
tests/test_gzip_middleware.py

M5 Day 16
Tests for GZip middleware.
"""

import importlib
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

# ---------------------------------------------------
# Prevent ChatOpenAI from initializing
# ---------------------------------------------------

with patch("langchain_openai.ChatOpenAI", MagicMock()):
    main_module = importlib.import_module("backend.app.main")

app = main_module.app

client = TestClient(app)


# ---------------------------------------------------
# Large response
# ---------------------------------------------------

def test_gzip_compression_enabled():

    headers = {
        "Accept-Encoding": "gzip"
    }

    response = client.get(
        "/api/v1/telemetry",
        headers=headers,
    )

    if len(response.content) >= 1000:

        assert (
            response.headers.get("Content-Encoding")
            == "gzip"
        )


# ---------------------------------------------------
# Small response
# ---------------------------------------------------

def test_gzip_ignored_for_small_responses():

    headers = {
        "Accept-Encoding": "gzip"
    }

    response = client.get(
        "/",
        headers=headers,
    )

    assert (
        response.headers.get("Content-Encoding")
        != "gzip"
    )