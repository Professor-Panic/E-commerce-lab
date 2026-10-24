"""
Unit tests for app.py

Run with:
    pytest test_app.py -v

Covers:
    - GET /inventory
    - GET /get (local hit, OpenFoodFacts fallback, not found, bad request)
    - POST /inventory (success, missing fields, duplicate barcode)
    - PATCH /update (success, not found)
    - DELETE /delete (success, not found)
"""

import pytest
from unittest.mock import patch, Mock

import app as app_module
from app import app, Item


@pytest.fixture
def client():
    """Flask test client with a fresh, known inventory for every test."""
    app.config["TESTING"] = True

    # Reset the in-memory "database" before each test so tests
    # don't leak state into one another.
    app_module.items.clear()
    app_module.items.append(
        Item(3017624010701, "Nutella", "Ferrero, test", "400.0g")
    )

    with app.test_client() as test_client:
        yield test_client


# ---------------------------------------------------------------------
# GET /inventory
# ---------------------------------------------------------------------
def test_get_inventory_returns_all_items(client):
    response = client.get("/inventory")
    data = response.get_json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["barcode"] == 3017624010701
    assert data[0]["name"] == "Nutella"
    assert data[0]["status"] == "in_house"


def test_get_inventory_empty(client):
    app_module.items.clear()
    response = client.get("/inventory")

    assert response.status_code == 200
    assert response.get_json() == []


# ---------------------------------------------------------------------
# GET /get
# ---------------------------------------------------------------------
def test_get_item_no_params_returns_400(client):
    response = client.get("/get")
    data = response.get_json()

    assert response.status_code == 400
    assert "error" in data


def test_get_item_found_locally_by_barcode(client):
    response = client.get("/get", query_string={"barcode": "3017624010701"})
    data = response.get_json()

    assert response.status_code == 200
    assert data["name"] == "Nutella"
    assert data["status"] == "in_house"


def test_get_item_found_locally_by_name(client):
    response = client.get("/get", query_string={"name": "nutella"})
    data = response.get_json()

    assert response.status_code == 200
    assert data["barcode"] == 3017624010701
    assert data["status"] == "in_house"


@patch("app.requests.get")
def test_get_item_falls_back_to_openfoodfacts(mock_get, client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": 1,
        "product": {
            "product_name": "Peanut Butter",
            "brands": "Skippy",
            "quantity": "500g",
        },
    }
    mock_get.return_value = mock_response

    response = client.get("/get", query_string={"barcode": "1234567890123"})
    data = response.get_json()

    assert response.status_code == 200
    assert data["name"] == "Peanut Butter"
    assert data["brand"] == "Skippy"
    assert data["status"] == "out_house"
    mock_get.assert_called_once()

    # Item should now be cached locally too
    assert any(i.barcode == 1234567890123 for i in app_module.items)


@patch("app.requests.get")
def test_get_item_not_found_on_openfoodfacts(mock_get, client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": 0}
    mock_get.return_value = mock_response

    response = client.get("/get", query_string={"barcode": "0000000000000"})
    data = response.get_json()

    assert response.status_code == 404
    assert "error" in data


@patch("app.requests.get")
def test_get_item_external_service_down(mock_get, client):
    mock_response = Mock()
    mock_response.status_code = 503
    mock_get.return_value = mock_response

    response = client.get("/get", query_string={"barcode": "9999999999999"})
    data = response.get_json()

    assert response.status_code == 502
    assert "error" in data


def test_get_item_not_found_by_name_without_barcode(client):
    # No barcode given, so there's nothing to fall back to externally
    response = client.get("/get", query_string={"name": "Nonexistent Item"})
    data = response.get_json()

    assert response.status_code == 404
    assert "error" in data


# ---------------------------------------------------------------------
# POST /inventory
# ---------------------------------------------------------------------
def test_add_item_success(client):
    payload = {
        "barcode": "1111111111111",
        "name": "Test Snack",
        "brand": "Test Brand",
        "weight": "100g",
    }
    response = client.post("/inventory", json=payload)
    data = response.get_json()

    assert response.status_code == 201
    assert data["name"] == "Test Snack"
    assert any(i.barcode == "1111111111111" for i in app_module.items)


def test_add_item_missing_required_fields(client):
    response = client.post("/inventory", json={"brand": "No Name Or Barcode"})
    data = response.get_json()

    assert response.status_code == 400
    assert "error" in data


def test_add_item_duplicate_barcode(client):
    payload = {"barcode": "3017624010701", "name": "Duplicate Nutella"}
    response = client.post("/inventory", json=payload)
    data = response.get_json()

    assert response.status_code == 409
    assert "error" in data


# ---------------------------------------------------------------------
# PATCH /update
# ---------------------------------------------------------------------
def test_update_item_success(client):
    response = client.patch(
        "/update",
        query_string={"barcode": "3017624010701"},
        json={"name": "Nutella Updated", "weight": "750.0g"},
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["name"] == "Nutella Updated"
    assert data["weight"] == "750.0g"
    # Unspecified field should stay unchanged
    assert data["brand"] == "Ferrero, test"


def test_update_item_not_found(client):
    response = client.patch(
        "/update",
        query_string={"barcode": "0000000000000"},
        json={"name": "Doesn't Matter"},
    )
    data = response.get_json()

    assert response.status_code == 404
    assert "error" in data


def test_update_item_no_params(client):
    response = client.patch("/update", json={"name": "No Identifier Given"})
    data = response.get_json()

    assert response.status_code == 404
    assert "error" in data


# ---------------------------------------------------------------------
# DELETE /delete
# ---------------------------------------------------------------------
def test_delete_item_success(client):
    response = client.delete("/delete", query_string={"barcode": "3017624010701"})
    data = response.get_json()

    assert response.status_code == 200
    assert data["barcode"] == 3017624010701
    assert not any(i.barcode == 3017624010701 for i in app_module.items)


def test_delete_item_not_found(client):
    response = client.delete("/delete", query_string={"barcode": "0000000000000"})
    data = response.get_json()

    assert response.status_code == 404
    assert "error" in data


def test_delete_item_by_name(client):
    response = client.delete("/delete", query_string={"name": "Nutella"})
    data = response.get_json()

    assert response.status_code == 200
    assert not any(i.name == "Nutella" for i in app_module.items)