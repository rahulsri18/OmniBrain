"""
tests/test_gzip_middleware.py
M5 Day 16: Verification test for GZip compression middleware
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_gzip_compression_enabled():
    """Verify responses larger than 1000 bytes are gzip-compressed when requested."""
    # Send request with Accept-Encoding header
    headers = {"Accept-Encoding": "gzip"}
    response = client.get("/api/v1/telemetry", headers=headers)

    # Note: If test response payload > 1000 bytes, content-encoding header will be set
    if len(response.content) >= 1000:
        assert response.headers.get("Content-Encoding") == "gzip"


def test_gzip_ignored_for_small_responses():
    """Verify tiny responses (< 1000 bytes) skip compression to avoid overhead."""
    headers = {"Accept-Encoding": "gzip"}
    response = client.get("/", headers=headers)

    # Root route payload is small (< 1000 bytes)
    assert response.headers.get("Content-Encoding") != "gzip"