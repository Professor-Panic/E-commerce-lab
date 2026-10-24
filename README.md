# Inventory Management System

A Flask-based REST API for managing retail inventory, with a CLI client and
OpenFoodFacts integration for looking up product details by barcode.

## Features

- Full CRUD on inventory items (create, read, update, delete)
- Look up items by `id`, `barcode`, or `name`
- Falls back to the [OpenFoodFacts API](https://openfoodfacts.github.io/openfoodfacts-server/api/)
  when a barcode isn't in local inventory, then caches the result
- Command-line interface for interacting with the API without Postman/curl
- Unit tests (pytest) covering the API endpoints, including mocked external
  API calls

## Project Structure

```
.
├── app.py          # Flask REST API
├── cli.py          # Command-line client
├── test_app.py     # Unit tests for app.py
└── README.md
```

## Setup

### 1. Clone and enter the project

```bash
git clone <https://github.com/Professor-Panic/E-commerce-lab.git>
cd <E-commerce-lab>
```

### 2. Install dependencies

```bash
pip install flask requests pytest
```

### 3. Run the API

```bash
python app.py
```

The server starts at `http://127.0.0.1:5000` by default.

### 4. Run the CLI (in a separate terminal)

```bash
python cli.py
```

> The CLI expects `app.py` to already be running — it talks to it over HTTP.

### 5. Run the tests

```bash
pytest test_app.py -v
```

## API Endpoints

| Method | Endpoint      | Description                                                        |
|--------|---------------|---------------------------------------------------------------------|
| GET    | `/inventory`  | List all items in local inventory                                   |
| GET    | `/get`        | Find one item by `?id=`, `?barcode=`, or `?name=`. Falls back to OpenFoodFacts by barcode if not found locally |
| POST   | `/inventory`  | Add a new item. Body: `{"barcode", "name", "brand", "weight"}`      |
| PATCH  | `/update`     | Update an item identified by `?id=`, `?barcode=`, or `?name=`. Body: any subset of `{"name", "brand", "weight"}` |
| DELETE | `/delete`     | Delete an item identified by `?id=`, `?barcode=`, or `?name=`       |

### Example requests

```bash
# List everything
curl http://127.0.0.1:5000/inventory

# Look up an item already in local inventory
curl "http://127.0.0.1:5000/get?barcode=3017624010701"

# Look up a barcode not in local inventory (pulls from OpenFoodFacts)
curl "http://127.0.0.1:5000/get?barcode=737628064502"

# Add a new item
curl -X POST http://127.0.0.1:5000/inventory \
  -H "Content-Type: application/json" \
  -d '{"barcode": "1111111111111", "name": "Trail Mix", "brand": "Acme", "weight": "250g"}'

# Update an item by id
curl -X PATCH "http://127.0.0.1:5000/update?id=1" \
  -H "Content-Type: application/json" \
  -d '{"weight": "750g"}'

# Delete an item by barcode
curl -X DELETE "http://127.0.0.1:5000/delete?barcode=1111111111111"
```

## CLI Usage

Running `python cli.py` opens a menu:

```
=== Inventory Management CLI ===
1. List all inventory
2. Find item (by id, barcode, or name; falls back to OpenFoodFacts by barcode)
3. Add new item
4. Update item
5. Delete item
6. Exit
```

Each option prompts for the information it needs (identifier type, field
values, etc.) and prints the API's response.

## Notes

- Inventory is stored in memory (a Python list), so it resets every time
  `app.py` restarts. There's no persistent database in this version.
- Barcodes are stored as given (as strings where they contain leading
  zeros) to avoid data loss — e.g. `06792208` is not the same barcode as
  `6792208`.
- Each item gets an auto-incrementing `id` separate from its barcode, so
  items can always be looked up even if two products somehow share a
  barcode value.
