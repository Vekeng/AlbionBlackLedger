import json
import sys
import os

def load_items(): 
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    items_path = os.path.join(base_path, "items.json")
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
    return items_map