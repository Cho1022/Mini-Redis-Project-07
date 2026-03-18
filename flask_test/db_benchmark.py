import socket
import statistics
import time

from pymongo import MongoClient
import redis


MONGO_CLIENT = MongoClient("localhost", 27017)
MONGO_COLLECTION = MONGO_CLIENT.dbjungle.mongotest

PREFIX = "bench:"
WARMUP_COUNT = 50
BENCHMARK_COUNT = 500
DEFAULT_REDIS_HOST = "127.0.0.1"
DEFAULT_REDIS_PORT = 6379
DEFAULT_MINI_REDIS_HOST = "127.0.0.1"
DEFAULT_MINI_REDIS_PORT = 6380


def render_template(template, index, default_prefix):
    if template and "{i}" in template:
        return template.replace("{i}", str(index))

    base = template if template else default_prefix
    return f"{base}{index}"


def build_key(index, key_template=None):
    return render_template(key_template, index, PREFIX)


def build_value(index, value_template=None):
    return render_template(value_template, index, "value-")


def create_redis_client(host=DEFAULT_REDIS_HOST, port=DEFAULT_REDIS_PORT):
    return redis.Redis(
        host=host,
        port=port,
        db=0,
        decode_responses=True,
    )


def encode_command(*parts):
    encoded_parts = [part.encode("utf-8") for part in parts]
    chunks = [f"*{len(encoded_parts)}\r\n".encode("ascii")]

    for part in encoded_parts:
        chunks.append(f"${len(part)}\r\n".encode("ascii"))
        chunks.append(part + b"\r\n")

    return b"".join(chunks)


def recv_resp(sock):
    first = recv_exact(sock, 1)

    if first in (b"+", b"-", b":"):
        return first + recv_until_crlf(sock)

    if first == b"$":
        length_line = recv_until_crlf(sock)
        payload = first + length_line
        length = int(length_line[:-2].decode("ascii"))
        if length == -1:
            return payload
        return payload + recv_exact(sock, length + 2)

    raise ValueError(f"unsupported RESP response prefix: {first!r}")


def recv_exact(sock, size):
    chunks = []
    remaining = size

    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("socket closed while reading response")
        chunks.append(chunk)
        remaining -= len(chunk)

    return b"".join(chunks)


def recv_until_crlf(sock):
    chunks = []

    while True:
        chunk = sock.recv(1)
        if not chunk:
            raise ConnectionError("socket closed while reading line")
        chunks.append(chunk)
        if len(chunks) >= 2 and chunks[-2] == b"\r" and chunks[-1] == b"\n":
            return b"".join(chunks)


def cleanup(count, redis_client, mini_redis_host, mini_redis_port, key_template=None):
    keys = [build_key(index, key_template) for index in range(count)]

    if keys:
        MONGO_COLLECTION.delete_many({"key": {"$in": keys}})

    for key in keys:
        redis_client.delete(key)

    with socket.create_connection((mini_redis_host, mini_redis_port), timeout=5) as sock:
        sock.settimeout(5)
        for key in keys:
            sock.sendall(encode_command("DEL", key))
            recv_resp(sock)


def prepare_get_data(count, redis_client, mini_redis_host, mini_redis_port, key_template=None, value_template=None):
    with socket.create_connection((mini_redis_host, mini_redis_port), timeout=5) as sock:
        sock.settimeout(5)

        for index in range(count):
            key = build_key(index, key_template)
            value = build_value(index, value_template)

            redis_client.set(key, value)
            MONGO_COLLECTION.update_one(
                {"key": key},
                {"$set": {"key": key, "value": value}},
                upsert=True,
            )

            sock.sendall(encode_command("SET", key, value))
            recv_resp(sock)


def benchmark_set_mongo(count, key_template=None, value_template=None):
    samples = []

    for index in range(count):
        key = build_key(index, key_template)
        value = build_value(index, value_template)

        start = time.perf_counter()
        MONGO_COLLECTION.update_one(
            {"key": key},
            {"$set": {"key": key, "value": value}},
            upsert=True,
        )
        samples.append((time.perf_counter() - start) * 1000)

    return samples


def benchmark_get_mongo(count, key_template=None):
    samples = []

    for index in range(count):
        start = time.perf_counter()
        MONGO_COLLECTION.find_one({"key": build_key(index, key_template)}, {"_id": 0, "value": 1})
        samples.append((time.perf_counter() - start) * 1000)

    return samples


def benchmark_set_redis(count, redis_client, key_template=None, value_template=None):
    samples = []

    for index in range(count):
        key = build_key(index, key_template)
        value = build_value(index, value_template)

        start = time.perf_counter()
        redis_client.set(key, value)
        samples.append((time.perf_counter() - start) * 1000)

    return samples


def benchmark_get_redis(count, redis_client, key_template=None):
    samples = []

    for index in range(count):
        start = time.perf_counter()
        redis_client.get(build_key(index, key_template))
        samples.append((time.perf_counter() - start) * 1000)

    return samples


def benchmark_set_mini_redis(count, host, port, key_template=None, value_template=None):
    samples = []

    with socket.create_connection((host, port), timeout=5) as sock:
        sock.settimeout(5)

        for index in range(count):
            payload = encode_command("SET", build_key(index, key_template), build_value(index, value_template))
            start = time.perf_counter()
            sock.sendall(payload)
            recv_resp(sock)
            samples.append((time.perf_counter() - start) * 1000)

    return samples


def benchmark_get_mini_redis(count, host, port, key_template=None):
    samples = []

    with socket.create_connection((host, port), timeout=5) as sock:
        sock.settimeout(5)

        for index in range(count):
            payload = encode_command("GET", build_key(index, key_template))
            start = time.perf_counter()
            sock.sendall(payload)
            recv_resp(sock)
            samples.append((time.perf_counter() - start) * 1000)

    return samples


def build_summary(samples):
    sorted_samples = sorted(samples)
    p95_index = max(0, int(len(sorted_samples) * 0.95) - 1)

    return {
        "count": len(sorted_samples),
        "avg": statistics.mean(sorted_samples),
        "median": statistics.median(sorted_samples),
        "min": min(sorted_samples),
        "p95": sorted_samples[p95_index],
        "max": max(sorted_samples),
    }


def run_benchmark(
    warmup_count=WARMUP_COUNT,
    benchmark_count=BENCHMARK_COUNT,
    redis_host=DEFAULT_REDIS_HOST,
    redis_port=DEFAULT_REDIS_PORT,
    mini_redis_host=DEFAULT_MINI_REDIS_HOST,
    mini_redis_port=DEFAULT_MINI_REDIS_PORT,
    key_template=None,
    value_template=None,
):
    total_count = warmup_count + benchmark_count
    redis_client = create_redis_client(redis_host, redis_port)

    prepare_get_data(
        total_count,
        redis_client,
        mini_redis_host,
        mini_redis_port,
        key_template=key_template,
        value_template=value_template,
    )

    benchmark_set_mongo(warmup_count, key_template=key_template, value_template=value_template)
    benchmark_set_redis(warmup_count, redis_client, key_template=key_template, value_template=value_template)
    benchmark_set_mini_redis(
        warmup_count,
        mini_redis_host,
        mini_redis_port,
        key_template=key_template,
        value_template=value_template,
    )

    benchmark_get_mongo(warmup_count, key_template=key_template)
    benchmark_get_redis(warmup_count, redis_client, key_template=key_template)
    benchmark_get_mini_redis(warmup_count, mini_redis_host, mini_redis_port, key_template=key_template)

    mongo_set_samples = benchmark_set_mongo(benchmark_count, key_template=key_template, value_template=value_template)
    redis_set_samples = benchmark_set_redis(
        benchmark_count,
        redis_client,
        key_template=key_template,
        value_template=value_template,
    )
    mini_redis_set_samples = benchmark_set_mini_redis(
        benchmark_count,
        mini_redis_host,
        mini_redis_port,
        key_template=key_template,
        value_template=value_template,
    )

    mongo_get_samples = benchmark_get_mongo(benchmark_count, key_template=key_template)
    redis_get_samples = benchmark_get_redis(benchmark_count, redis_client, key_template=key_template)
    mini_redis_get_samples = benchmark_get_mini_redis(
        benchmark_count,
        mini_redis_host,
        mini_redis_port,
        key_template=key_template,
    )

    return {
        "warmup_count": warmup_count,
        "benchmark_count": benchmark_count,
        "redis_host": redis_host,
        "redis_port": redis_port,
        "mini_redis_host": mini_redis_host,
        "mini_redis_port": mini_redis_port,
        "key_template": key_template or PREFIX,
        "value_template": value_template or "value-",
        "set": {
            "mongo": build_summary(mongo_set_samples),
            "redis": build_summary(redis_set_samples),
            "mini_redis": build_summary(mini_redis_set_samples),
        },
        "get": {
            "mongo": build_summary(mongo_get_samples),
            "redis": build_summary(redis_get_samples),
            "mini_redis": build_summary(mini_redis_get_samples),
        },
    }


def run_cleanup(
    warmup_count=WARMUP_COUNT,
    benchmark_count=BENCHMARK_COUNT,
    redis_host=DEFAULT_REDIS_HOST,
    redis_port=DEFAULT_REDIS_PORT,
    mini_redis_host=DEFAULT_MINI_REDIS_HOST,
    mini_redis_port=DEFAULT_MINI_REDIS_PORT,
    key_template=None,
):
    total_count = warmup_count + benchmark_count
    redis_client = create_redis_client(redis_host, redis_port)

    cleanup(
        total_count,
        redis_client,
        mini_redis_host,
        mini_redis_port,
        key_template=key_template,
    )

    return {
        "deleted_count": total_count,
        "key_template": key_template or PREFIX,
        "redis_host": redis_host,
        "redis_port": redis_port,
        "mini_redis_host": mini_redis_host,
        "mini_redis_port": mini_redis_port,
    }
