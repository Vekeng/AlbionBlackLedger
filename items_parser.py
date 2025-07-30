import json

def load_items(): 
    # Load JSON data from file
    with open("items.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    # Safely build dictionary
    items_map = {}

    for item in data:
        # Check that item has both UniqueName and LocalizedNames
        if "UniqueName" in item and "LocalizedNames" in item:
            localized = item["LocalizedNames"]
            if isinstance(localized, dict) and "EN-US" in localized:
                items_map[item["UniqueName"]] = localized["EN-US"]
    return items_map