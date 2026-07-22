import time
import statistics
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----------------------------
# Configuration
# ----------------------------
BASE_URL = "http://127.0.0.1:8000/api/v1/chat"

PAYLOAD = {
    "message": "Hello"
}

HEADERS = {
    "Content-Type": "application/json"
}

TOTAL_REQUESTS = 20
CONCURRENT_USERS = 5


def send_request(request_id):

    start = time.perf_counter()

    try:

        response = requests.post(
            BASE_URL,
            json=PAYLOAD,
            headers=HEADERS,
            stream=True,
            timeout=120
        )

        connection_latency = time.perf_counter() - start

        if response.status_code != 200:
            return {
                "success": False,
                "request": request_id,
                "status": response.status_code
            }

        first_chunk = None
        chunks = 0

        for line in response.iter_lines():

            if not line:
                continue

            current = time.perf_counter()

            if first_chunk is None:
                first_chunk = current - start

            chunks += 1

        total_time = time.perf_counter() - start

        return {
            "success": True,
            "request": request_id,
            "connection": connection_latency,
            "first_chunk": first_chunk,
            "total": total_time,
            "chunks": chunks
        }

    except Exception as e:

        return {
            "success": False,
            "request": request_id,
            "error": str(e)
        }


def print_summary(results):

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print("\n" + "=" * 65)
    print("CHAT API PERFORMANCE REPORT")
    print("=" * 65)

    print(f"Total Requests      : {len(results)}")
    print(f"Concurrent Users    : {CONCURRENT_USERS}")
    print(f"Successful Requests : {len(successful)}")
    print(f"Failed Requests     : {len(failed)}")

    if successful:

        connection = [r["connection"] for r in successful]
        first = [r["first_chunk"] for r in successful]
        total = [r["total"] for r in successful]
        chunks = [r["chunks"] for r in successful]

        print("\nPerformance Metrics")
        print("-" * 65)

        print(f"Average Connection Latency : {statistics.mean(connection):.3f} sec")
        print(f"Minimum Connection         : {min(connection):.3f} sec")
        print(f"Maximum Connection         : {max(connection):.3f} sec")

        print()

        print(f"Average First Chunk Time   : {statistics.mean(first):.3f} sec")
        print(f"Average Total Response     : {statistics.mean(total):.3f} sec")
        print(f"Average Stream Chunks      : {statistics.mean(chunks):.2f}")

        throughput = len(successful) / max(total)

        print(f"Approx Throughput          : {throughput:.2f} requests/sec")

    if failed:

        print("\nFailed Requests")

        for item in failed:
            print(item)


def main():

    print("=" * 65)
    print("OmniBrain Chat API Load Test")
    print("=" * 65)

    start = time.perf_counter()

    results = []

    with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:

        futures = [
            executor.submit(send_request, i + 1)
            for i in range(TOTAL_REQUESTS)
        ]

        completed = 0

        for future in as_completed(futures):

            result = future.result()

            completed += 1

            if result["success"]:

                print(
                    f"[{completed:02d}] "
                    f"Req {result['request']:02d} | "
                    f"Conn {result['connection']:.3f}s | "
                    f"TTFT {result['first_chunk']:.3f}s | "
                    f"Total {result['total']:.3f}s | "
                    f"Chunks {result['chunks']}"
                )

            else:

                print(f"[{completed:02d}] Request {result['request']} Failed")

            results.append(result)

    duration = time.perf_counter() - start

    print_summary(results)

    print(f"\nOverall Test Duration : {duration:.2f} sec")


if __name__ == "__main__":
    main()