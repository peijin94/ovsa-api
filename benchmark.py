import argparse
import statistics
import time
from typing import List

import requests


def time_request(method: str, url: str) -> float:
    start = time.perf_counter()
    resp = requests.request(method, url, timeout=5.0)
    resp.raise_for_status()
    end = time.perf_counter()
    return (end - start) * 1000.0  # ms


def run_benchmark(base_url: str, iterations: int) -> None:
    endpoints = [
        "/ephm/el",
        "/ephm/az",
        "/ephm/sunup",
        "/ephm/info",
    ]

    print(f"Benchmarking {len(endpoints)} endpoints for {iterations} iterations each")
    print(f"Base URL: {base_url.rstrip('/')}")
    print()

    for path in endpoints:
        url = base_url.rstrip("/") + path
        times: List[float] = []
        print(f"Endpoint: {url}")

        for i in range(iterations):
            try:
                t_ms = time_request("GET", url)
            except Exception as exc:
                print(f"  Request {i + 1} failed: {exc}")
                continue
            times.append(t_ms)

        if not times:
            print("  No successful requests.")
            print()
            continue

        avg = statistics.mean(times)
        p50 = statistics.median(times)
        p95 = statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times)
        t_min = min(times)
        t_max = max(times)

        print(f"  count={len(times)}")
        print(f"  avg={avg:.3f} ms  p50={p50:.3f} ms  p95={p95:.3f} ms")
        print(f"  min={t_min:.3f} ms  max={t_max:.3f} ms")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark ephm API endpoints.")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8012",
        help="Base URL of the API server (default: http://localhost:8012)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Number of requests per endpoint (default: 100)",
    )
    args = parser.parse_args()

    run_benchmark(args.base_url, args.iterations)


if __name__ == "__main__":
    main()

