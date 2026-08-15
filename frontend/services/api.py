import os
import requests

BACKEND_URL = os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:8000")
BASE_URL = f"{BACKEND_URL}/api/v1"


def upload_pdf(uploaded_file):
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            "application/pdf"
        )
    }

    try:
        response = requests.post(
            f"{BASE_URL}/upload",
            files=files
        )
        return response

    except Exception as e:
        return e