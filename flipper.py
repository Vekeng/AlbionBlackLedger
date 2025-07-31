import sqlite3
import re
import json
import sys
import os

if getattr(sys, 'frozen', False):
    # Running in bundle (PyInstaller)
    base_path = sys._MEIPASS
else:
    # Running in script
    base_path = os.path.dirname(__file__)

items_path = os.path.join(base_path, "item_map.json")

with open(items_path, "r", encoding="utf-8") as file:
    items_map = json.load(file)

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

def delete_row(buy_id, sell_id): 
    cursor = sqlite3.connect("marketdata.db")
    query = "DELETE FROM orders WHERE Id = ? OR Id = ?"
    print(buy_id)
    print(sell_id)
    cursor.execute(query, [buy_id, sell_id])
    cursor.commit()
    cursor.close()

def claim_flip(flip): 
    cursor = sqlite3.connect("marketdata.db")
    query = """
            INSERT OR REPLACE INTO claimed (
                ItemTypeId, 
                Enchantment, 
                Profit
            ) VALUES (
                :item,
                :enchantment, 
                :profit
            )
    """
    cursor.execute(query, flip)
    cursor.commit()
    cursor.close()

def get_average_material_price(item_type_id, location_id="3003"):
    query = """
            WITH ordered_orders AS (
                SELECT
                    UnitPriceSilver,
                    Amount,
                    SUM(Amount) OVER (ORDER BY UnitPriceSilver) AS running_amount
                FROM orders
                WHERE AuctionType = 'offer'
                    AND LocationId = ?
                    AND ItemTypeId = ?
                ),
                limited_orders AS (
                SELECT
                    UnitPriceSilver,
                    CASE
                    WHEN running_amount <= 2000 THEN Amount
                    WHEN running_amount - Amount < 2000 THEN 2000 - (running_amount - Amount)
                    ELSE 0
                    END AS limited_amount
                FROM ordered_orders
                )
                SELECT
                CAST(SUM(UnitPriceSilver * limited_amount) * 1.0 / SUM(limited_amount) / 10000 AS INTEGER) AS average_price
                FROM limited_orders
                WHERE limited_amount > 0;
    """

    conn = sqlite3.connect("marketdata.db")
    cur = conn.cursor()
    cur.execute(query, (location_id, item_type_id))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row[0] else 0

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

def find_flip(from_market="3005", to_market="3003", premium=True, material_prices=None, order='Buy'):
    tax_rate = 0.96 if premium else 0.92
    connect = sqlite3.connect("marketdata.db")
    connect.row_factory = sqlite3.Row
    cursor = connect.cursor()

    order_type = {
        "Buy": "request",
        "Sell": "offer"
    }
    agg_func = "MIN" if order == "Sell" else "MAX"
    quality_join = "=" if order == "Sell" else ">="

    rows = cursor.execute(
        f"""
        SELECT
            buy.Id AS buy_id,
            buy.ItemTypeId,
            buy.ItemGroupTypeId,
            buy.LocationId AS buy_location,
            buy.QualityLevel AS buy_quality,
            buy.Amount AS buy_amount, 
            buy.EnchantmentLevel AS buy_enchantment,
            buy.MinPrice / 10000 AS buy_price,
            sell.Id AS sell_id,
            sell.LocationId AS sell_location,
            sell.QualityLevel AS sell_quality,
            sell.Amount AS sell_amount, 
            sell.EnchantmentLevel AS sell_enchantment,
            sell.MaxPrice / 10000 AS sell_price
        FROM (
            SELECT 
                Id, 
                ItemTypeId,
                ItemGroupTypeId,
                LocationId,
                QualityLevel,
                Amount, 
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
                Id,
                ItemTypeId,
                ItemGroupTypeId,
                LocationId,
                QualityLevel,
                Amount,
                EnchantmentLevel,
                {agg_func}(UnitPriceSilver) AS MaxPrice
            FROM 
                orders
            WHERE 
                AuctionType = ? AND LocationId = ?
            GROUP BY 
                ItemGroupTypeId, LocationId, QualityLevel, EnchantmentLevel
        ) AS sell
        ON buy.ItemGroupTypeId = sell.ItemGroupTypeId
        AND buy.QualityLevel {quality_join} sell.QualityLevel
        AND buy.EnchantmentLevel <= sell.EnchantmentLevel
        """,
        [from_market, order_type[order], to_market],
    ).fetchall()

    cursor.close()
    result = []

    for row in rows:
        buy_id = row["buy_id"]
        sell_id = row["sell_id"]
        buy_amount = row["buy_amount"]
        sell_amount = row["sell_amount"]
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

        item_name = items_map.get(item)
        if item_name is not None: 
            if profit > 0:
                result.append(
                    {
                        "buy_id": buy_id,
                        "ItemTypeId": item_name + " " + str(tier) + "." + str(enchant_from),
                        "buy_location": locations[str(row["buy_location"])],
                        "buy_quality": qualities[row["buy_quality"]],
                        "buy_amount": buy_amount, 
                        "buy_price": round(row["buy_price"]),
                        "sell_id": sell_id, 
                        "sell_location": locations[str(row["sell_location"])],
                        "sell_quality": qualities[row["sell_quality"]],
                        "sell_amount": sell_amount,
                        "sell_enchantment": item_name + " " + str(tier) + "." + str(enchant_to),
                        "enchantment": enchantment_str,
                        "sell_price": round(row["sell_price"]),
                        "profit": profit,
                    }
                )

    result.sort(key=lambda x: x["profit"], reverse=True)
    return result