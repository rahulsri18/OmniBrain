"""
load_tests/locustfile.py
M1 Day 16: System-wide Load & Bottleneck Test Suite for OmniBrain AI
"""

from locust import HttpUser, task, between, events
import random
import io
from PIL import Image


class OmniBrainLoadTestUser(HttpUser):
    """
    Simulates user interaction patterns with OmniBrain, testing authentication,
    document search, batched vision processing, and SSE stream endpoints.
    """

    wait_time = between(1, 3)  # Simulate human think-time between tasks

    def on_start(self):
        """Pre-test setup: Log in or acquire standard headers."""
        self.headers = {
            "Accept-Encoding": "gzip",
            "Content-Type": "application/json",
        }

    @task(4)
    def test_health_and_telemetry(self):
        """Tests lightweight API routes to measure baseline network overhead."""
        self.client.get("/api/v1/telemetry", headers=self.headers, name="[GET] Telemetry")

    @task(3)
    def test_document_search_and_retrieval(self):
        """Tests search and retrieval pipeline under concurrent query load."""
        payload = {
            "query": "Compare annual revenue trends from financial report",
            "top_k": 4,
        }
        self.client.post(
            "/api/v1/search",
            json=payload,
            headers=self.headers,
            name="[POST] Vector Search",
        )

    @task(2)
    def test_quantized_vision_batch(self):
        """Tests M4's vision batch inference endpoint with synthetic image uploads."""
        # Generate in-memory synthetic image byte stream
        img = Image.new("RGB", (200, 200), color="blue")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_bytes = img_byte_arr.getvalue()

        files = [
            ("files", ("test_img_1.png", img_bytes, "image/png")),
            ("files", ("test_img_2.png", img_bytes, "image/png")),
        ]

        self.client.post(
            "/api/v1/vision/batch-analyze",
            files=files,
            name="[POST] Vision Batch Processing",
        )

    @task(1)
    def test_chat_response_stream(self):
        """Tests SSE chat streaming endpoint for connection pooling and latency."""
        payload = {
            "message": "Summarize key findings from page 12 of the annual report.",
            "stream": True,
        }
        with self.client.post(
            "/api/v1/chat",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="[POST] Chat Stream",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Chat stream failed with status {response.status_code}")


@events.test_start.connect
def on_test_start(environment, **kwargs):
    print("==========================================================")
    print("🚀 Starting M1 System-wide Load Test against OmniBrain API")
    print("==========================================================")