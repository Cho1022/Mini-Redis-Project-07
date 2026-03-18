from flask import Flask, jsonify, request

from db_benchmark import run_benchmark


app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    return response


@app.route("/db-benchmark", methods=["GET"])
def db_benchmark():
    warmup_count = request.args.get("warmup", default=30, type=int)
    benchmark_count = request.args.get("count", default=200, type=int)
    redis_host = request.args.get("redis_host", default="127.0.0.1", type=str)
    redis_port = request.args.get("redis_port", default=6379, type=int)
    mini_redis_host = request.args.get("mini_redis_host", default="127.0.0.1", type=str)
    mini_redis_port = request.args.get("mini_redis_port", default=6380, type=int)

    if (
        warmup_count < 0
        or benchmark_count < 1
        or redis_port < 1
        or mini_redis_port < 1
    ):
        return (
            jsonify(
                {
                    "result": "fail",
                    "message": "warmup must be 0 or more, count must be 1 or more, and ports must be valid.",
                }
            ),
            400,
        )

    try:
        result = run_benchmark(
            warmup_count=warmup_count,
            benchmark_count=benchmark_count,
            redis_host=redis_host,
            redis_port=redis_port,
            mini_redis_host=mini_redis_host,
            mini_redis_port=mini_redis_port,
        )
    except Exception as error:
        return jsonify({"result": "fail", "message": str(error)}), 500

    return jsonify({"result": "success", "benchmark": result})


if __name__ == "__main__":
    app.run("0.0.0.0", port=5003, debug=True)
