from flask import Flask, jsonify, request
import requests

app = Flask(__name__)


class Item:
    def __init__(self, barcode, name, brand, item_weight):
        self.barcode = barcode
        self.name = name
        self.brand = brand
        self.weight = item_weight


items = [Item(3017624010701, "Nutella", "Ferrero, test", "400.0g")]


def find_item(barcode=None, name=None):
    """Look up an item in local inventory by barcode or name."""
    if barcode:
        return next((i for i in items if str(i.barcode) == str(barcode)), None)
    if name:
        return next((i for i in items if i.name.lower() == name.lower()), None)
    return None


def get_item_data():
    """Pull barcode/name from query args and look the item up."""
    barcode = request.args.get("barcode")
    name = request.args.get("name")

    if not barcode and not name:
        return None

    return find_item(barcode=barcode, name=name)


def item_to_dict(item, status="in_house"):
    return {
        "barcode": item.barcode,
        "name": item.name,
        "brand": item.brand,
        "weight": item.weight,
        "status": status,
    }


# ---------------------------------------------------------------------
# GET /inventory  -> all items
# ---------------------------------------------------------------------
@app.route("/inventory", methods=["GET"])
def get_inventory():
    return jsonify([item_to_dict(i) for i in items]), 200


# ---------------------------------------------------------------------
# GET /get?barcode=... or ?name=...
#   Checks local inventory first, falls back to OpenFoodFacts by barcode
# ---------------------------------------------------------------------
@app.route("/get", methods=["GET"])
def get_item():
    barcode = request.args.get("barcode")
    name = request.args.get("name")

    if not barcode and not name:
        return jsonify({"error": "Provide a barcode or product name"}), 400

    item = find_item(barcode=barcode, name=name)
    if item is not None:
        return jsonify(item_to_dict(item, status="in_house")), 200

    if barcode:
        url = f"https://world.openfoodfacts.net/api/v2/product/{barcode}"
        try:
            response = requests.get(
                url,
                params={"fields": "product_name,brands,quantity"},
                timeout=10,
            )
        except requests.RequestException:
            return jsonify({"error": "Product service unavailable"}), 502

        if response.status_code != 200:
            return jsonify({"error": "Product service unavailable"}), 502

        data = response.json()

        if data.get("status") != 1:
            return jsonify({"error": "Product not found"}), 404

        product = data.get("product", {})
        product_name = product.get("product_name")
        product_brand = product.get("brands")
        product_weight = product.get("quantity")

        new_item = Item(int(barcode), product_name, product_brand, product_weight)
        items.append(new_item)

        return jsonify(item_to_dict(new_item, status="out_house")), 200

    return jsonify({"error": "Product not found in local inventory"}), 404


# ---------------------------------------------------------------------
# POST /inventory  -> add a new item
#   body: {"barcode": ..., "name": ..., "brand": ..., "weight": ...}
# ---------------------------------------------------------------------
@app.route("/inventory", methods=["POST"])
def add_item():
    payload = request.get_json(silent=True) or {}
    barcode = payload.get("barcode")
    name = payload.get("name")

    if not barcode or not name:
        return jsonify({"error": "barcode and name are required"}), 400

    if find_item(barcode=barcode) is not None:
        return jsonify({"error": "Item with that barcode already exists"}), 409

    new_item = Item(
        barcode,
        name,
        payload.get("brand"),
        payload.get("weight"),
    )
    items.append(new_item)

    return jsonify(item_to_dict(new_item)), 201

# ---------------------------------------------------------------------
# PATCH /update?barcode=...   (or ?name=...)
# ---------------------------------------------------------------------
@app.route("/update", methods=["PATCH"])
def update_item():
    item = get_item_data()
    if item is None:
        return jsonify({"error": "Item not found"}), 404

    changes = request.get_json(silent=True) or {}

    if "name" in changes:
        item.name = changes["name"]
    if "brand" in changes:
        item.brand = changes["brand"]
    if "weight" in changes:
        item.weight = changes["weight"]

    return jsonify(item_to_dict(item)), 200


# ---------------------------------------------------------------------
# DELETE /delete?barcode=...   (or ?name=...)
# ---------------------------------------------------------------------
@app.route("/delete", methods=["DELETE"])
def delete_item():
    item = get_item_data()
    if item is None:
        return jsonify({"error": "Item not found"}), 404

    items.remove(item)
    return jsonify({"message": "Item deleted", "barcode": item.barcode}), 200


if __name__ == "__main__":
    app.run(debug=True)