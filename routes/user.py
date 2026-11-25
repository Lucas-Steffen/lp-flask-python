from flask import request, jsonify
from sqlalchemy import asc, desc

from werkzeug.security import generate_password_hash

from app import app, db
from jwt import verify_jwt, get_token_payload
from model.movement import Movement
from model.user import User


@app.route("/users", methods=["GET"])
def list_users():
    # pega o token que veio no header (Authorization: Bearer <token>)
    auth = request.headers.get("Authorization", "")

    if not auth.startswith("Bearer "):
        return jsonify({"error": "token ausente"}), 401

    token = auth.split(" ")[1]
    payload = verify_jwt(token)

    if payload is None:
        return jsonify({"error": "token inválido ou expirado"}), 401

    query_params = request.args

    page = query_params.get('page', default=0, type=int)
    limit = query_params.get('limit', default=10, type=int)
    offset = page * limit

    filter = {}
    ignored_fields = ['page', 'limit', 'sort_by', 'sort_direction']
    for field, value in query_params.items():
        if field not in ignored_fields:
            filter[field] = value

    sort_by = query_params.get('sort_by', default='id', type=str)
    sort_direction = query_params.get('sort_direction', default='asc', type=str)

    order_by = asc(sort_by) if sort_direction == 'asc' else desc(sort_by)

    users = User.query.filter_by(**filter).order_by(order_by).offset(offset).limit(limit).all()
    if not users:
        return jsonify([]), 200

    status_code = 206 if len(users) == limit else 200

    result = [{'id': user.id, 'username': user.username, 'email': user.email} for user in users]

    return jsonify(result), status_code


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    payload = get_token_payload()
    if payload is None:
        return jsonify({"error": "token ausente, inválido ou expirado"}), 401

    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "usuário não encontrado"}), 404

    return jsonify({"id": user.id, "username": user.username, "email": user.email}), 200


@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    payload = get_token_payload()
    if payload is None:
        return jsonify({"error": "token ausente, inválido ou expirado"}), 401

    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "usuário não encontrado"}), 404

    # so pode alterar a propria conta
    if int(payload["sub"]) != user.id:
        return jsonify({"error": "você só pode alterar o seu próprio usuário"}), 403

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "corpo JSON obrigatório"}), 400

    # so altera o que veio no json
    if "username" in data:
        username = data["username"]
        if username == "":
            return jsonify({"error": "username inválido"}), 400

        # ve se outro usuario ja usa esse username
        outro = User.query.filter_by(username=username).first()
        if outro is not None and outro.id != user.id:
            return jsonify({"error": "username já cadastrado"}), 409
        user.username = username

    if "email" in data:
        email = data["email"]
        if email == "":
            return jsonify({"error": "email inválido"}), 400

        outro = User.query.filter_by(email=email).first()
        if outro is not None and outro.id != user.id:
            return jsonify({"error": "email já cadastrado"}), 409
        user.email = email

    if "password" in data:
        password = data["password"]
        if password == "":
            return jsonify({"error": "password inválido"}), 400
        user.password = generate_password_hash(password)

    db.session.commit()

    return jsonify({"id": user.id, "username": user.username, "email": user.email}), 200


@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    payload = get_token_payload()
    if payload is None:
        return jsonify({"error": "token ausente, inválido ou expirado"}), 401

    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "usuário não encontrado"}), 404

    if int(payload["sub"]) != user.id:
        return jsonify({"error": "você só pode remover o seu próprio usuário"}), 403

    # nao apaga se o usuario ja fez movimentacao
    movimentacao = Movement.query.filter_by(user_id=user.id).first()
    if movimentacao is not None:
        return jsonify({"error": "usuário possui movimentações e não pode ser removido"}), 409

    db.session.delete(user)
    db.session.commit()

    return "", 204
