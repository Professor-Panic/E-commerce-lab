import requests

BASE_URL = "http://127.0.0.1:5000"


def list_inventory():
    response = requests.get(f"{BASE_URL}/inventory")
    if response.status_code != 200:
        print(f"Error fetching inventory: {response.status_code}")
        return

    inventory = response.json()
    if not inventory:
        print("Inventory is empty.")
        return

    print(f"\n{'Barcode':<16}{'Name':<25}{'Brand':<20}{'Weight':<10}")
    print("-" * 71)
    for item in inventory:
        print(
            f"{str(item['barcode']):<16}"
            f"{str(item['name']):<25}"
            f"{str(item['brand']):<20}"
            f"{str(item['weight']):<10}"
        )


def find_item():
    choice = input("Search by (b)arcode or (n)ame? ").strip().lower()
    params = {}
    if choice == "b":
        params["barcode"] = input("Enter barcode: ").strip()
    elif choice == "n":
        params["name"] = input("Enter product name: ").strip()
    else:
        print("Invalid choice.")
        return

    response = requests.get(f"{BASE_URL}/get", params=params)
    data = response.json()

    if response.status_code != 200:
        print(f"Error: {data.get('error', 'Unknown error')}")
        return

    print("\nItem found:")
    for key, value in data.items():
        print(f"  {key}: {value}")


def add_item():
    barcode = input("Barcode: ").strip()
    name = input("Name: ").strip()
    brand = input("Brand: ").strip()
    weight = input("Weight: ").strip()

    payload = {"barcode": barcode, "name": name, "brand": brand, "weight": weight}
    response = requests.post(f"{BASE_URL}/inventory", json=payload)
    data = response.json()

    if response.status_code == 201:
        print(f"Added: {data['name']} ({data['barcode']})")
    else:
        print(f"Error: {data.get('error', 'Unknown error')}")


def update_item():
    choice = input("Identify item by (b)arcode or (n)ame? ").strip().lower()
    params = {}
    if choice == "b":
        params["barcode"] = input("Enter barcode: ").strip()
    elif choice == "n":
        params["name"] = input("Enter product name: ").strip()
    else:
        print("Invalid choice.")
        return

    changes = {}
    new_name = input("New name (leave blank to skip): ").strip()
    new_brand = input("New brand (leave blank to skip): ").strip()
    new_weight = input("New weight (leave blank to skip): ").strip()

    if new_name:
        changes["name"] = new_name
    if new_brand:
        changes["brand"] = new_brand
    if new_weight:
        changes["weight"] = new_weight

    if not changes:
        print("No changes provided.")
        return

    response = requests.patch(f"{BASE_URL}/update", params=params, json=changes)
    data = response.json()

    if response.status_code == 200:
        print(f"Updated: {data}")
    else:
        print(f"Error: {data.get('error', 'Unknown error')}")


def delete_item():
    choice = input("Identify item by (b)arcode or (n)ame? ").strip().lower()
    params = {}
    if choice == "b":
        params["barcode"] = input("Enter barcode: ").strip()
    elif choice == "n":
        params["name"] = input("Enter product name: ").strip()
    else:
        print("Invalid choice.")
        return

    response = requests.delete(f"{BASE_URL}/delete", params=params)
    data = response.json()

    if response.status_code == 200:
        print(f"Deleted item with barcode {data['barcode']}")
    else:
        print(f"Error: {data.get('error', 'Unknown error')}")


def main_menu():
    menu = """
=== Inventory Management CLI ===
1. List all inventory
2. Find item (local or OpenFoodFacts by barcode)
3. Add new item
4. Update item
5. Delete item
6. Exit
"""
    while True:
        print(menu)
        choice = input("Choose an option: ").strip()

        if choice == "1":
            list_inventory()
        elif choice == "2":
            find_item()
        elif choice == "3":
            add_item()
        elif choice == "4":
            update_item()
        elif choice == "5":
            delete_item()
        elif choice == "6":
            print("Goodbye!")
            break
        else:
            print("Invalid option, try again.")


if __name__ == "__main__":
    try:
        main_menu()
    except requests.ConnectionError:
        print(f"\nCould not connect to {BASE_URL}. Is app.py running?")