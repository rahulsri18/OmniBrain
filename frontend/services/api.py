import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"


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