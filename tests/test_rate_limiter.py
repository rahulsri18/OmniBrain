"""
tests/test_rate_limiter.py
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_upload_rate_limit():
    """Verify that file upload endpoint enforces 10 requests/minute limit."""
    # Dummy file
    files = {"file": ("test.pdf", b"%PDF-1.4 dummy content", "application/pdf")}

    # Send requests up to limit
    responses = [client.post("/api/v1/upload", files=files) for _ in range(12)]

    # The 11th and 12th requests should be blocked with 429
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes