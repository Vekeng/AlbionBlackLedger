import sqlite3
from items_parser import load_items
import re

items_map = load_items()

# N values based on item type
N_VALUES = {
    "MAIN": 288,
    "2H": 384,
    "ARMOR": 192,
    "BAG": 192,
    "HEAD": 96,
    "SHOES": 96,
    "CAPE": 96,
    "OFF": 96,
}

qualities = {
    1: "Normal", 
    2: "Good", 
    3: "Outstanding", 
    4: "Excellent", 
    5: "Masterpiece"
}



locations = {
    "2004": "Bridgewatch",
    "3008": "Martlock",
    "0007": "Thetford",
    "4002": "Fort Sterling",
    "1002": "Lymhurst",
    "3005": "Caerleon",
    "3003": "Black Market"
}



def get_n_value(item_group_type_id):
    for key in N_VALUES:
        if key in item_group_type_id:
            return N_VALUES[key]
    return None


def calculate_total_enchant_cost(item_group_type_id, tier, enchant_from, enchant_to, material_prices):
    n = get_n_value(item_group_type_id)
    if n is None:
        return None, []

    total_cost = 0
    materials_detailed = []

    for level in range(enchant_from, enchant_to):
        if level == 0:
            material = "RUNE"
        elif level == 1:
            material = "SOUL"
        elif level == 2:
            material = "RELIC"
        else:
            return None, []

        try:
            material_cost = material_prices[material][tier]
        except KeyError:
            material_cost = 0

        step_total = n * material_cost
        total_cost += step_total

        warning_icon = " ⚠️" if material_cost == 0 else ""
        materials_detailed.append(
            f"{n}x {tier}_{material} @ {material_cost:,} = {step_total:,}{warning_icon}"
        )

    return total_cost, materials_detailed

def find_flip(from_market="3005", to_market="3003", premium=True, material_prices=None):
    tax_rate = 0.96 if premium else 0.92
    connect = sqlite3.connect("marketdata.db")
    connect.row_factory = sqlite3.Row
    cursor = connect.cursor()

    rows = cursor.execute(
        """
        SELECT
            buy.ItemTypeId,
            buy.ItemGroupTypeId,
            buy.LocationId AS buy_location,
            buy.QualityLevel AS buy_quality,
            buy.EnchantmentLevel AS buy_enchantment,
            buy.MinPrice / 10000 AS buy_price,
            sell.LocationId AS sell_location,
            sell.QualityLevel AS sell_quality,
            sell.EnchantmentLevel AS sell_enchantment,
            sell.MaxPrice / 10000 AS sell_price
        FROM (
            SELECT 
                ItemTypeId,
                ItemGroupTypeId,
                LocationId,
                QualityLevel,
                EnchantmentLevel,
                MIN(UnitPriceSilver) AS MinPrice
            FROM 
                orders
            WHERE 
                AuctionType = 'offer' AND LocationId = ?
            GROUP BY 
                ItemGroupTypeId, LocationId, QualityLevel, EnchantmentLevel
        ) AS buy
        JOIN (
            SELECT 
                ItemTypeId,
                ItemGroupTypeId,
                LocationId,
                QualityLevel,
                EnchantmentLevel,
                MAX(UnitPriceSilver) AS MaxPrice
            FROM 
                orders
            WHERE 
                AuctionType = 'request' AND LocationId = ?
            GROUP BY 
                ItemGroupTypeId, LocationId, QualityLevel, EnchantmentLevel
        ) AS sell
        ON buy.ItemGroupTypeId = sell.ItemGroupTypeId
        AND buy.QualityLevel >= sell.QualityLevel
        AND buy.EnchantmentLevel <= sell.EnchantmentLevel
        """,
        [from_market, to_market],
    ).fetchall()

    cursor.close()
    result = []

    for row in rows:
        item = row["ItemTypeId"]  # with enchant suffix, for display
        item_group = row["ItemGroupTypeId"]  # base item without enchant suffix
        enchant_from = row["buy_enchantment"]
        enchant_to = row["sell_enchantment"]
        tier = item_group.split("_")[0]

        if enchant_from < enchant_to:
            enchant_cost, materials = calculate_total_enchant_cost(
                item_group, tier, enchant_from, enchant_to, material_prices
            )
            if enchant_cost is None:
                continue
            enchantment_str = "\n".join(materials)
            enchantment_str += f"\n(Total: {int(enchant_cost):,})"
        else:
            enchant_cost = 0
            enchantment_str = ""
        total_cost = row["buy_price"] + enchant_cost
        net_sell_price = row["sell_price"] * tax_rate
        profit = int(round(net_sell_price - total_cost))
        tax = int(round(row["sell_price"] * (1 - tax_rate)))
        
        match = re.match(r"T(\d)", item)
        if match:
            tier = int(match.group(1))
        else:
            tier = None  

        if profit > 0:
            result.append(
                {
                    "ItemTypeId": items_map[item] + " " + str(tier) + "." + str(enchant_from),
                    "buy_location": locations[str(row["buy_location"])],
                    "buy_quality": qualities[row["buy_quality"]],
                    "buy_price": round(row["buy_price"]),
                    "sell_location": locations[str(row["sell_location"])],
                    "sell_quality": qualities[row["sell_quality"]],
                    "sell_enchantment": items_map[item] + " " + str(tier) + "." + str(enchant_to),
                    "enchantment": enchantment_str,
                    "sell_price": round(row["sell_price"]),
                    "profit": profit,
                }
            )

    result.sort(key=lambda x: x["profit"], reverse=True)
    return result