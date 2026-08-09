import os

# Must be set BEFORE importing the application because
# ChatOpenAI is initialized during module import.
os.environ.setdefault("OPENAI_API_KEY", "test-key-for-rate-limit")

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import settings


client = TestClient(app)


def test_upload_rate_limit():
    """
    Verify that /api/v1/upload enforces the 10 requests/minute limit.
    """

    # The upload endpoint is protected by API-key authentication.
    headers = {
        settings.API_KEY_NAME: settings.API_KEY
    }

    responses = []

    for _ in range(12):
        files = {
            "file": (
                "test.pdf",
                b"%PDF-1.4 dummy content",
                "application/pdf",
            )
        }

        response = client.post(
            "/api/v1/upload",
            files=files,
            headers=headers,
        )

        responses.append(response)

    status_codes = [response.status_code for response in responses]

    print(f"\nUpload status codes: {status_codes}")

    # 10 requests/minute are allowed.
    # Requests after the limit must receive 429.
    assert 429 in status_codes, (
        f"Expected HTTP 429 after exceeding the upload rate limit. "
        f"Received: {status_codes}"
    )