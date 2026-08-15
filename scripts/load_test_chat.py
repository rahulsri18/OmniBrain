"""
load_test_chat.py

M7 Day 6 Task:
Load-testing script to measure Chat API's streaming response, 
Connection Latency, Time-To-First-Byte (TTFB), and Total Stream Duration.
"""

import asyncio
import time
import statistics
import aiohttp
from typing import List, Dict, Any

TARGET_URL = "http://127.0.0.1:8000/api/v1/chat"
CONCURRENT_USERS = 10
TOTAL_REQUESTS = 50
PROMPT = "Explain the architecture of a Retrieval-Augmented Generation system in detail."


async def send_streaming_request(session: aiohttp.ClientSession, request_id: int) -> Dict[str, Any]:
    payload = {
        "message": PROMPT,
        "session_id": f"load_test_session_{request_id}"
    }

    start_time = time.perf_counter()
    first_chunk_time = None
    total_chunks = 0
    total_bytes = 0

    try:
        async with session.post(TARGET_URL, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
            # 1. Connection Latency (Time taken to get HTTP Headers)
            connection_latency = (time.perf_counter() - start_time) * 1000  # ms

            if response.status != 200:
                return {
                    "request_id": request_id,
                    "status": "FAILED",
                    "error": f"HTTP {response.status}",
                    "connection_latency_ms": connection_latency
                }

            # 2. Reading Stream Chunks
            async for chunk in response.content.iter_any():
                if not first_chunk_time:
                    # Time To First Byte / First Chunk (TTFB)
                    first_chunk_time = time.perf_counter()

                total_chunks += 1
                total_bytes += len(chunk)

            end_time = time.perf_counter()

            ttfb_ms = ((first_chunk_time - start_time) * 1000) if first_chunk_time else 0
            total_duration_ms = (end_time - start_time) * 1000

            return {
                "request_id": request_id,
                "status": "SUCCESS",
                "connection_latency_ms": connection_latency,
                "ttfb_ms": ttfb_ms,
                "total_duration_ms": total_duration_ms,
                "total_chunks": total_chunks,
                "total_bytes": total_bytes
            }

    except Exception as e:
        return {
            "request_id": request_id,
            "status": "ERROR",
            "error": str(e),
            "connection_latency_ms": (time.perf_counter() - start_time) * 1000
        }


async def run_load_test():
    print("=" * 65)
    print(f"🚀 Starting Chat API Streaming Load Test")
    print(f"Target URL: {TARGET_URL}")
    print(f"Concurrent Users: {CONCURRENT_USERS} | Total Requests: {TOTAL_REQUESTS}")
    print("=" * 65)

    semaphore = asyncio.Semaphore(CONCURRENT_USERS)

    async def worker(session: aiohttp.ClientSession, req_id: int):
        async with semaphore:
            return await send_streaming_request(session, req_id)

    async with aiohttp.ClientSession() as session:
        tasks = [worker(session, i + 1) for i in range(TOTAL_REQUESTS)]
        results = await asyncio.gather(*tasks)

    successful = [r for r in results if r["status"] == "SUCCESS"]
    failed = [r for r in results if r["status"] != "SUCCESS"]

    print("\n" + "=" * 65)
    print("📊 LOAD TEST SUMMARY RESULTS")
    print("=" * 65)
    print(f"Total Requests Sent : {TOTAL_REQUESTS}")
    print(f"Successful Requests : {len(successful)} ✅")
    print(f"Failed Requests     : {len(failed)} ❌")

    if successful:
        conn_latencies = [r["connection_latency_ms"] for r in successful]
        ttfbs = [r["ttfb_ms"] for r in successful]
        durations = [r["total_duration_ms"] for r in successful]

        print("\n--- Latency Metrics (in milliseconds) ---")
        print(f"Avg Connection Latency : {statistics.mean(conn_latencies):.2f} ms")
        print(f"Min Connection Latency : {min(conn_latencies):.2f} ms")
        print(f"Max Connection Latency : {max(conn_latencies):.2f} ms")

        print(f"\nAvg TTFB (First Chunk) : {statistics.mean(ttfbs):.2f} ms  ⚡")
        print(f"P95 TTFB (95th %ile)   : {sorted(ttfbs)[int(len(ttfbs)*0.95)-1]:.2f} ms")

        print(f"\nAvg Total Stream Duration : {statistics.mean(durations):.2f} ms")
        print(f"Max Total Stream Duration : {max(durations):.2f} ms")

    if failed:
        print("\n--- Failure Logs ---")
        for f in failed[:5]:
            print(f"Req #{f['request_id']}: {f.get('error')}")

    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_load_test())