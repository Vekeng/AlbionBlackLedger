import json

items_path = ("items.json")
# Load JSON data from file
with open(items_path, "r", encoding="utf-8") as file:
    data = json.load(file)

# Safely build dictionary
items_map = {}

for item in data:
    # Check that item has both UniqueName and LocalizedNames
    if "UniqueName" in item and "LocalizedNames" in item:
        localized = item["LocalizedNames"]
        if isinstance(localized, dict) and "EN-US" in localized:
            items_map[item["UniqueName"]] = localized["EN-US"]
with open("item_map.json", "w", encoding="utf-8") as f:
    json.dump(items_map, f, ensure_ascii=False, indent=2)