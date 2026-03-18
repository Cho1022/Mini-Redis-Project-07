from pymongo import MongoClient
from flask import Flask,request, jsonify

client = MongoClient("localhost",27017)

db = client.dbjungle

mongotest = db.mongotest

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/mongogettest",methods=["GET"])
def mongoGetTest():
    print(request)
    key = request.args.get("key")
    value = mongotest.find_one({"key":key})
    if value != None:
        result = value["value"]
    else:
        result = None
    return jsonify({"result":"success","value":result})

@app.route("/mongosettest",methods=["POST"])
def mongoSetTest():
    key = request.form["key"]
    value = request.form["value"]
    mongotest.insert_one({"key":key,"value":value})
    return jsonify({"result":"success"})

@app.route("/mongodeleteall",methods=["GET"])
def mongoDeleteAll():
    mongotest.delete_many({})
    return jsonify({"result":"success"})


if __name__ == "__main__":
    app.run("0.0.0.0", port=5001, debug=False)
