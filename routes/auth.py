from datetime import datetime, timedelta, timezone

from app import app, db
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from jwt import generate_jwt
from model.user import User


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "campos obrigatórios: username, email, password"}), 400

    # pega o dado da request
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    # valida os campos da request (Existe DTO em python?)
    if username is None or username == "":
        return jsonify({"error": "username é obrigatório"}), 400

    if email is None or email == "":
        return jsonify({"error": "email é obrigatório"}), 400

    if password is None or password == "":
        return jsonify({"error": "password é obrigatório"}), 400

    # Se já existir alguém com esse e-mail e/ou username, skippa
    user_existente = User.query.filter_by(username=username).first()
    if user_existente is not None:
        return jsonify({"error": "username já cadastrado"}), 409

    email_existente = User.query.filter_by(email=email).first()
    if email_existente is not None:
        return jsonify({"error": "email já cadastrado"}), 409

    senha_hash = generate_password_hash(password)

    novo_user = User(username=username, email=email, password=senha_hash)
    db.session.add(novo_user)
    db.session.commit()

    # Desestruturação da resposta para nn devolver a senha
    return jsonify({"id": novo_user.id, "username": novo_user.username, "email": novo_user.email}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "corpo JSON obrigatório"}), 400

    username = data.get("username")
    password = data.get("password")

    if username is None or username == "":
        return jsonify({"error": "username é obrigatório"}), 400

    if password is None or password == "":
        return jsonify({"error": "password é obrigatório"}), 400

    # procura o usuario no banco
    user = User.query.filter_by(username=username).first()

    if user is None:
        return jsonify({"error": "credenciais inválidas"}), 401

    # compara a senha digitada com o hash que esta no banco
    senha_correta = check_password_hash(user.password, password)

    if senha_correta == False:
        return jsonify({"error": "credenciais inválidas"}), 401

    # dados que vao dentro do token (o token vale por 1 hora)
    expira = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {"sub": str(user.id), "username": user.username, "exp": expira}

    token = generate_jwt(payload)

    return jsonify({"token": token}), 200