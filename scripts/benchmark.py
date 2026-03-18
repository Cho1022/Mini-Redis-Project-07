from __future__ import annotations

import argparse
import socket
import statistics
import time
from dataclasses import dataclass
from typing import Callable, Iterable

from scripts.demo_client import encode_command


@dataclass(slots=True)
class BenchmarkResult:
    name: str
    count: int
    total_seconds: float
    avg_ms: float
    min_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    max_ms: float
    ops_per_sec: float


def recv_resp(sock: socket.socket) -> bytes:
    first = _recv_exact(sock, 1)

    if first in (b"+", b"-", b":"):
        return first + _recv_until_crlf(sock)

    if first == b"$":
        length_line = _recv_until_crlf(sock)
        payload = first + length_line
        length = int(length_line[:-2].decode("ascii"))
        if length == -1:
            return payload
        return payload + _recv_exact(sock, length + 2)

    raise ValueError(f"unsupported RESP response prefix: {first!r}")


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("socket closed while reading response")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _recv_until_crlf(sock: socket.socket) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = sock.recv(1)
        if not chunk:
            raise ConnectionError("socket closed while reading line")
        chunks.append(chunk)
        if len(chunks) >= 2 and chunks[-2] == b"\r" and chunks[-1] == b"\n":
            return b"".join(chunks)


def percentile(sorted_values: list[float], ratio: float) -> float:
    if not sorted_values:
        return 0.0
    index = max(0, min(len(sorted_values) - 1, int(round((len(sorted_values) - 1) * ratio))))
    return sorted_values[index]


def benchmark_scenario(
    sock: socket.socket,
    name: str,
    count: int,
    command_factory: Callable[[int], Iterable[str]],
    expected_prefix: bytes | None = None,
) -> BenchmarkResult:
    latencies_ms: list[float] = []

    for index in range(count):
        payload = encode_command(*command_factory(index))
        started = time.perf_counter()
        sock.sendall(payload)
        response = recv_resp(sock)
        elapsed_ms = (time.perf_counter() - started) * 1000
        latencies_ms.append(elapsed_ms)

        if expected_prefix is not None and not response.startswith(expected_prefix):
            raise AssertionError(f"unexpected response for {name}: {response!r}")

    total_seconds = sum(latency / 1000 for latency in latencies_ms)
    sorted_latencies = sorted(latencies_ms)
    return BenchmarkResult(
        name=name,
        count=count,
        total_seconds=total_seconds,
        avg_ms=statistics.fmean(latencies_ms),
        min_ms=sorted_latencies[0],
        p50_ms=percentile(sorted_latencies, 0.50),
        p95_ms=percentile(sorted_latencies, 0.95),
        p99_ms=percentile(sorted_latencies, 0.99),
        max_ms=sorted_latencies[-1],
        ops_per_sec=(count / total_seconds) if total_seconds > 0 else 0.0,
    )


def warm_up(sock: socket.socket, count: int) -> None:
    for _ in range(count):
        sock.sendall(encode_command("PING"))
        recv_resp(sock)


def prepare_get_dataset(sock: socket.socket, count: int, value: str, key_prefix: str) -> None:
    for index in range(count):
        sock.sendall(encode_command("SET", f"{key_prefix}{index}", value))
        response = recv_resp(sock)
        if response != b"+OK\r\n":
            raise AssertionError(f"failed to seed dataset: {response!r}")


def print_result(result: BenchmarkResult) -> None:
    print(f"[{result.name}]")
    print(f"count       : {result.count}")
    print(f"total (s)   : {result.total_seconds:.4f}")
    print(f"ops/sec     : {result.ops_per_sec:.2f}")
    print(f"avg (ms)    : {result.avg_ms:.4f}")
    print(f"min (ms)    : {result.min_ms:.4f}")
    print(f"p50 (ms)    : {result.p50_ms:.4f}")
    print(f"p95 (ms)    : {result.p95_ms:.4f}")
    print(f"p99 (ms)    : {result.p99_ms:.4f}")
    print(f"max (ms)    : {result.max_ms:.4f}")
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark the Mini Redis TCP server.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host.")
    parser.add_argument("--port", type=int, default=6379, help="Server port.")
    parser.add_argument("--count", type=int, default=1000, help="Number of requests per scenario.")
    parser.add_argument("--warmup", type=int, default=50, help="Warm-up PING requests before measuring.")
    parser.add_argument(
        "--scenario",
        choices=["ping", "set", "get", "all"],
        default="all",
        help="Which benchmark scenario to run.",
    )
    parser.add_argument("--value-size", type=int, default=16, help="Value size in bytes for SET/GET.")
    parser.add_argument("--key-prefix", default="bench:key:", help="Prefix for generated benchmark keys.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    value = "v" * args.value_size

    with socket.create_connection((args.host, args.port), timeout=5) as sock:
        sock.settimeout(5)
        warm_up(sock, args.warmup)

        scenarios: list[BenchmarkResult] = []

        if args.scenario in ("ping", "all"):
            scenarios.append(
                benchmark_scenario(
                    sock,
                    name="PING",
                    count=args.count,
                    command_factory=lambda _: ["PING"],
                    expected_prefix=b"+PONG",
                )
            )

        if args.scenario in ("set", "all"):
            scenarios.append(
                benchmark_scenario(
                    sock,
                    name="SET",
                    count=args.count,
                    command_factory=lambda index: ["SET", f"{args.key_prefix}set:{index}", value],
                    expected_prefix=b"+OK",
                )
            )

        if args.scenario in ("get", "all"):
            prepare_get_dataset(sock, args.count, value, f"{args.key_prefix}get:")
            scenarios.append(
                benchmark_scenario(
                    sock,
                    name="GET",
                    count=args.count,
                    command_factory=lambda index: ["GET", f"{args.key_prefix}get:{index}"],
                    expected_prefix=b"$",
                )
            )

    print(f"host        : {args.host}")
    print(f"port        : {args.port}")
    print(f"count       : {args.count}")
    print(f"warmup      : {args.warmup}")
    print(f"value size  : {args.value_size}")
    print()

    for result in scenarios:
        print_result(result)


if __name__ == "__main__":
    main()
