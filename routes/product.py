from app import app, db
from flask import request, jsonify

from jwt import get_token_payload
from model.movement import Movement
from model.product import Product


@app.route("/products", methods=["POST"])
def create_product():
    # confere o token antes de tudo
    payload = get_token_payload()
    if payload is None:
        return jsonify({"error": "token ausente, inválido ou expirado"}), 401

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "corpo JSON obrigatório"}), 400

    name = data.get("name")
    sku = data.get("sku")
    price = data.get("price")
    quantity = data.get("quantity", 0)
    min_quantity = data.get("min_quantity", 0)

    # valida os campos
    if name is None or name == "":
        return jsonify({"error": "name é obrigatório"}), 400

    if sku is None or sku == "":
        return jsonify({"error": "sku é obrigatório"}), 400

    if price is None:
        return jsonify({"error": "price é obrigatório"}), 400

    if price < 0:
        return jsonify({"error": "price não pode ser negativo"}), 400

    if quantity < 0:
        return jsonify({"error": "quantity não pode ser negativo"}), 400

    if min_quantity < 0:
        return jsonify({"error": "min_quantity não pode ser negativo"}), 400

    # nao deixa cadastrar dois produtos com o mesmo sku
    sku_existente = Product.query.filter_by(sku=sku).first()
    if sku_existente is not None:
        return jsonify({"error": "sku já cadastrado"}), 409

    product = Product(name=name, sku=sku, price=price, quantity=quantity, min_quantity=min_quantity)
    db.session.add(product)
    db.session.commit()

    return jsonify(product.to_dict()), 201


@app.route("/products", methods=["GET"])
def list_products():
    payload = get_token_payload()
    if payload is None:
        return jsonify({"error": "token ausente, inválido ou expirado"}), 401

    products = Product.query.all()

    # transforma cada produto em dicionario
    result = []
    for product in products:
        result.append(product.to_dict())

    return jsonify(result), 200


@app.route("/products/low-stock", methods=["GET"])
def list_low_stock():
    payload = get_token_payload()
    if payload is None:
        return jsonify({"error": "token ausente, inválido ou expirado"}), 401

    # produtos com quantidade menor ou igual ao minimo
    products = Product.query.filter(Product.quantity <= Product.min_quantity).all()

    result = []
    for product in products:
        result.append(product.to_dict())

    return jsonify(result), 200


@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    payload = get_token_payload()
    if payload is None:
        return jsonify({"error": "token ausente, inválido ou expirado"}), 401

    product = Product.query.get(product_id)
    if product is None:
        return jsonify({"error": "produto não encontrado"}), 404

    return jsonify(product.to_dict()), 200


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    payload = get_token_payload()
    if payload is None:
        return jsonify({"error": "token ausente, inválido ou expirado"}), 401

    product = Product.query.get(product_id)
    if product is None:
        return jsonify({"error": "produto não encontrado"}), 404

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "corpo JSON obrigatório"}), 400

    # so altera o que veio no json
    if "name" in data:
        if data["name"] == "":
            return jsonify({"error": "name inválido"}), 400
        product.name = data["name"]

    if "sku" in data:
        if data["sku"] == "":
            return jsonify({"error": "sku inválido"}), 400

        # ve se outro produto ja usa esse sku
        outro = Product.query.filter_by(sku=data["sku"]).first()
        if outro is not None and outro.id != product.id:
            return jsonify({"error": "sku já cadastrado"}), 409
        product.sku = data["sku"]

    if "price" in data:
        if data["price"] < 0:
            return jsonify({"error": "price não pode ser negativo"}), 400
        product.price = data["price"]

    if "quantity" in data:
        if data["quantity"] < 0:
            return jsonify({"error": "quantity não pode ser negativo"}), 400
        product.quantity = data["quantity"]

    if "min_quantity" in data:
        if data["min_quantity"] < 0:
            return jsonify({"error": "min_quantity não pode ser negativo"}), 400
        product.min_quantity = data["min_quantity"]

    db.session.commit()

    return jsonify(product.to_dict()), 200


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    payload = get_token_payload()
    if payload is None:
        return jsonify({"error": "token ausente, inválido ou expirado"}), 401

    product = Product.query.get(product_id)
    if product is None:
        return jsonify({"error": "produto não encontrado"}), 404

    # não apaga produto que já tem movimentações (preserva o histórico)
    if Movement.query.filter_by(product_id=product.id).first() is not None:
        return jsonify({"error": "produto possui movimentações e não pode ser removido"}), 409

    db.session.delete(product)
    db.session.commit()

    return "", 204
