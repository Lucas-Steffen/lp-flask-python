from flask import request
from jose import jwt, JWTError
from app import app


# cria o token com os dados que a gente passar
def generate_jwt(payload):
    secret = app.config['SECRET_KEY']
    algoritmo = app.config['ALGORITHM']

    token = jwt.encode(payload, secret, algorithm=algoritmo)
    return token


# confere se o token é valido, se nao for retorna None
def verify_jwt(token):
    secret = app.config['SECRET_KEY']
    algoritmo = app.config['ALGORITHM']

    try:
        payload = jwt.decode(token, secret, algorithms=[algoritmo])
        return payload
    except JWTError:
        return None


# le o header Authorization e devolve o payload do token, ou None se nao der
def get_token_payload():
    auth = request.headers.get("Authorization", "")

    if not auth.startswith("Bearer "):
        return None

    token = auth.split(" ")[1]
    return verify_jwt(token)
