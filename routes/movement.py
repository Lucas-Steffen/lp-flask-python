from app import app, db
from flask import request, jsonify

from jwt import get_token_payload
from model.movement import Movement
from model.product import Product


@app.route("/movements", methods=["POST"])
def create_movement():
    payload = get_token_payload()
    if payload is None:
        return jsonify({"error": "token ausente, inválido ou expirado"}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "corpo JSON obrigatório"}), 400

    product_id = data.get("product_id")
    tipo = data.get("type")
    quantity = data.get("quantity")

    if not isinstance(product_id, int) or isinstance(product_id, bool):
        return jsonify({"error": "product_id deve ser um inteiro"}), 400

    if tipo not in ("IN", "OUT"):
        return jsonify({"error": "type deve ser IN ou OUT"}), 400

    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        return jsonify({"error": "quantity deve ser um inteiro maior que 0"}), 400

    product = db.session.get(Product, product_id)
    if product is None:
        return jsonify({"error": "produto não encontrado"}), 404

    # regra de negócio: uma saída não pode deixar o estoque negativo
    if tipo == "OUT" and quantity > product.quantity:
        return jsonify({
            "error": "estoque insuficiente",
            "available": product.quantity,
        }), 400

    if tipo == "IN":
        product.quantity += quantity
    else:
        product.quantity -= quantity

    movement = Movement(product_id=product.id, user_id=int(payload["sub"]),
                        type=tipo, quantity=quantity)
    db.session.add(movement)

    # o commit grava a movimentação e a nova quantidade juntas
    db.session.commit()

    result = movement.to_dict()
    result["product_quantity"] = product.quantity
    return jsonify(result), 201


@app.route("/movements", methods=["GET"])
def list_movements():
    if get_token_payload() is None:
        return jsonify({"error": "token ausente, inválido ou expirado"}), 401

    query = Movement.query

    # filtro opcional: /movements?product_id=1
    if "product_id" in request.args:
        product_id = request.args.get("product_id", type=int)
        if product_id is None:
            return jsonify({"error": "product_id deve ser um inteiro"}), 400
        query = query.filter_by(product_id=product_id)

    movements = query.order_by(Movement.id).all()
    return jsonify([m.to_dict() for m in movements]), 200
