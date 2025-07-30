import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk
import tkinter as tk
from db import truncate
import sys
import os
import sqlite3

if getattr(sys, 'frozen', False):
    # Running in bundle (PyInstaller)
    base_path = sys._MEIPASS
else:
    # Running in script
    base_path = os.path.dirname(__file__)

root = None
tree = None
current_data = []

# Predefined columns and mock location list
COLUMNS = [
    "ItemTypeId", "buy_location", "buy_quality",
    "buy_price", "sell_location", "sell_quality", "sell_enchantment",
    "sell_price", "enchantment", "profit"
]

HEADINGS = [
    "Buy Item",
    "Buy Location",
    "Buy Quality",
    "Buy Price",
    "Sell Location",
    "Sell Quality",
    "Sell Item",
    "Sell Price",
    "Enchantment",
    "Profit",
]

LOCATIONS = {
    "Bridgewatch": "2004",
    "Martlock": "3008",
    "Thetford": "0007",
    "Fort Sterling": "4002",
    "Lymhurst": "1002",
    "Caerleon": "3005",
    "Black Market": "3003"
}

def show_table(data_fetch_fn):
    global root, tree, current_data, price_vars

    root = tb.Window(themename="darkly")
    root.title("Albion Online Black Ledger")
    icon_path = os.path.join(base_path, "blackledger.ico")
    root.wm_iconbitmap(icon_path)

    # === Dropdown + Button Panel ===
    control_frame = tb.Frame(root, padding=10)
    control_frame.pack(fill=tk.X)

    from_var = tk.StringVar(value="Caerleon")
    to_var = tk.StringVar(value="Black Market")

    tb.Label(control_frame, text="From:", bootstyle="info").pack(side=tk.LEFT)
    from_menu = tb.Combobox(control_frame, textvariable=from_var, values=list(LOCATIONS.keys()), state="readonly", bootstyle="dark")
    from_menu.pack(side=tk.LEFT, padx=5)

    tb.Label(control_frame, text="To:", bootstyle="info").pack(side=tk.LEFT)
    to_menu = tb.Combobox(control_frame, textvariable=to_var, values=list(LOCATIONS.keys()), state="readonly", bootstyle="dark")
    to_menu.pack(side=tk.LEFT, padx=5)

    price_vars = {}

    def get_price_inputs():
        result = {"RUNE": {}, "SOUL": {}, "RELIC": {}}
        for key, var in price_vars.items():
            try:
                tier, mat = key.split("_")
                result[mat][tier] = int(var.get())
            except (ValueError, KeyError):
                continue
        return result

    def on_clear():
        truncate()
        on_refresh()

    def on_refresh():
        selected_from = LOCATIONS[from_var.get()]
        selected_to = LOCATIONS[to_var.get()]
        material_prices = get_price_inputs()
        new_data = data_fetch_fn(selected_from, selected_to, premium_var.get(), material_prices)
        if new_data: 
            label.pack_forget()
            update_table(new_data)
        else: 
            label.pack(pady=5)
            update_table([])

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
        return row[0] if row else 0

    
    premium_var = tk.BooleanVar(value=True)  # Checked by default
    tb.Checkbutton(control_frame, text="Premium", variable=premium_var, bootstyle="success-round-toggle").pack(side=tk.LEFT, padx=10)
    tb.Button(control_frame, text="Find Flips!", command=on_refresh, bootstyle="primary").pack(side=tk.LEFT, padx=10)
    tb.Button(control_frame, text="Clear data", command=on_clear, bootstyle="danger").pack(side=tk.LEFT, padx=10)
    label = tb.Label(
        control_frame,  # Replace with your actual parent frame (e.g., `root`, `control_frame`, etc.)
        text="⚠️ No profitable flips found.",
        foreground="orange",
        font=("Segoe UI", 10, "bold"),
        bootstyle="warning"
        )
    label.pack(pady=5)
    label.pack_forget()

    # === Main Content Frame ===
    content_frame = tb.Frame(root, padding=10)
    content_frame.pack(fill=tk.BOTH, expand=True)

    # Left: Table frame
    table_frame = tb.Frame(content_frame)
    table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    style = tb.Style()
    style.configure("dark.Treeview", rowheight=100)
    tree = ttk.Treeview(table_frame, columns=COLUMNS, show="headings", style="dark.Treeview")
    for col, heading in zip(COLUMNS, HEADINGS):
        tree.heading(col, text=heading, command=lambda c=col: sort_column(tree, c, False))
        if col in ("buy_price", "sell_price", "buy_quality", "sell_quality"):
            tree.column(col, anchor="center", width=20)
            print(col)
        elif col == "enchantment": 
            tree.column(col, anchor="center", width=220)
        else: 
            tree.column(col, anchor="center", width=100)
            

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview, bootstyle="secondary")
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)

    # Right: Material Prices in one vertical column grouped by tier
    price_frame = tb.Labelframe(content_frame, text="Material Prices", padding=10)
    price_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0), anchor="n")

    def populate_material_prices():
        selected_from = LOCATIONS[from_var.get()]
        for tier in tiers:
            for mat in materials:
                item_type = f"T{tier}_{mat}"
                avg_price = get_average_material_price(item_type, selected_from)
                key = f"T{tier}_{mat}"
                if key in price_vars:
                    price_vars[key].set(str(avg_price))


    

    tiers = range(4, 9)  # T4 to T8
    materials = ["RUNE", "SOUL", "RELIC"]

    for tier in tiers:
        tier_label = tb.Label(price_frame, text=f"T{tier}:", font=("Segoe UI", 10, "bold"))
        tier_label.pack(anchor="w", pady=(10, 2))

        for mat in materials:
            key = f"T{tier}_{mat}"
            price_vars[key] = tk.StringVar(value="0")

            mat_frame = tb.Frame(price_frame)
            mat_frame.pack(fill=tk.X, pady=1)

            tb.Label(mat_frame, text=mat + ":", width=8, anchor="w").pack(side=tk.LEFT)
            tb.Entry(mat_frame, textvariable=price_vars[key], width=10).pack(side=tk.LEFT)
    tb.Button(price_frame, text="Get Prices", command=populate_material_prices, bootstyle="success").pack(fill="x", pady=(10, 0))
    estimate = tb.Label(
        price_frame,
        text="Prices are approximate, calculated from the 2,000 cheapest materials",
        foreground="Orange",
        font=("Segoe UI", 10, "bold"),
        bootstyle="warning",
        wraplength=140,
        justify="center"
        )
    estimate.pack(pady=5)
    root.geometry("1280x900")
    root.minsize(width=1280, height=900)
    root.mainloop()



def update_table(data):
    global tree
    tree.delete(*tree.get_children())
    for row in data:
        values = [row.get(col, "") for col in tree["columns"]]
        tree.insert("", tk.END, values=values)

def sort_column(tv, col, reverse):
    try:
        items = [(float(tv.set(k, col)), k) for k in tv.get_children("")]
    except ValueError:
        items = [(tv.set(k, col), k) for k in tv.get_children("")]
    items.sort(reverse=reverse)
    for index, (_, k) in enumerate(items):
        tv.move(k, "", index)
    tv.heading(col, command=lambda: sort_column(tv, col, not reverse))
