from app import app
from flask import request, jsonify


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)

    if data == None:
        return jsonify({"error": "campos obrigatórios: username, email, password"}), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if username == None or username == "":
        return jsonify({"error": "campos obrigatórios: username, email, password"}), 400

    if email == None or email == "":
        return jsonify({"error": "campos obrigatórios: username, email, password"}), 400

    if password == None or password == "":
        return jsonify({"error": "campos obrigatórios: username, email, password"}), 400

    return jsonify(data), 200