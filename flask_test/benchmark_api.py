from flask import Flask, jsonify, request

from db_benchmark import run_benchmark, run_cleanup


app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def read_common_params():
    return {
        "warmup_count": request.args.get("warmup", default=30, type=int),
        "benchmark_count": request.args.get("count", default=200, type=int),
        "redis_host": request.args.get("redis_host", default="127.0.0.1", type=str),
        "redis_port": request.args.get("redis_port", default=6379, type=int),
        "mini_redis_host": request.args.get("mini_redis_host", default="127.0.0.1", type=str),
        "mini_redis_port": request.args.get("mini_redis_port", default=6380, type=int),
        "key_template": request.args.get("key_template", default="bench:{i}", type=str),
        "value_template": request.args.get("value_template", default="value-{i}", type=str),
    }


def validate_common_params(params):
    return not (
        params["warmup_count"] < 0
        or params["benchmark_count"] < 1
        or params["redis_port"] < 1
        or params["mini_redis_port"] < 1
    )


@app.route("/db-benchmark", methods=["GET"])
def db_benchmark():
    params = read_common_params()

    if not validate_common_params(params):
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
        result = run_benchmark(**params)
    except Exception as error:
        return jsonify({"result": "fail", "message": str(error)}), 500

    return jsonify({"result": "success", "benchmark": result})


@app.route("/db-cleanup", methods=["POST"])
def db_cleanup():
    params = read_common_params()

    if not validate_common_params(params):
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
        result = run_cleanup(
            warmup_count=params["warmup_count"],
            benchmark_count=params["benchmark_count"],
            redis_host=params["redis_host"],
            redis_port=params["redis_port"],
            mini_redis_host=params["mini_redis_host"],
            mini_redis_port=params["mini_redis_port"],
            key_template=params["key_template"],
        )
    except Exception as error:
        return jsonify({"result": "fail", "message": str(error)}), 500

    return jsonify({"result": "success", "cleanup": result})


if __name__ == "__main__":
    app.run("0.0.0.0", port=5003, debug=True)
