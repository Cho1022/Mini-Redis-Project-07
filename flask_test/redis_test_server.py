from flask import Flask, jsonify, request
import redis


app = Flask(__name__)

# Local Redis test connection
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True,
)

ALLOWED_COMMANDS = {"GET", "SET"}


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/redis", methods=["GET", "POST"])
def redis_test():
    if request.method == "GET":
        command = request.args.get("command", "").upper()
        key = request.args.get("key")
        value = None
    else:
        command = (
            request.form.get("command")
            or (request.json or {}).get("command")
            or ""
        ).upper()
        key = request.form.get("key") or (request.json or {}).get("key")
        value = request.form.get("value") or (request.json or {}).get("value")

    if command not in ALLOWED_COMMANDS:
        return (
            jsonify(
                {
                    "result": "fail",
                    "message": "Only GET and SET commands are allowed.",
                }
            ),
            400,
        )

    if not key:
        return jsonify({"result": "fail", "message": "key is required."}), 400

    if command == "GET":
        stored_value = redis_client.get(key)
        return jsonify(
            {
                "result": "success",
                "command": command,
                "key": key,
                "value": stored_value,
            }
        )

    if value is None:
        return jsonify({"result": "fail", "message": "value is required."}), 400

    redis_client.set(key, value)
    return jsonify(
        {
            "result": "success",
            "command": command,
            "key": key,
            "value": value,
        }
    )


if __name__ == "__main__":
    app.run("0.0.0.0", port=5002, debug=False)
