import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk
import tkinter as tk
from db import truncate
import sys
import os
from flipper import get_average_material_price
from flipper import find_flip
from flipper import claim_flip
from flipper import delete_row


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
    "buy_id", "ItemTypeId", "buy_location", "buy_quality", "buy_amount", 
    "buy_price", "sell_id", "sell_location", "sell_quality", "sell_amount", "sell_enchantment",
    "sell_price", "enchantment", "profit"
]

HEADINGS = [
    "Buy Id",
    "Buy Item",
    "Buy Location",
    "Buy Quality",
    "Buy Amount", 
    "Buy Price",
    "Sell Id", 
    "Sell Location",
    "Sell Quality",
    "Sell Amount",
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

def show_table():
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
    order_var = tk.StringVar(value="Buy")

    #def to_change(event): 
    #    selected = to_menu.get()
    #    if selected == "Black Market": 
    #        order_menu.config(state="disabled")
    #        order_menu.set("Buy")
    #    else: 
    #        order_menu.config(state="readonly")

    tb.Label(control_frame, text="From:", bootstyle="info").pack(side=tk.LEFT)
    from_menu = tb.Combobox(control_frame, textvariable=from_var, values=list(k for k in LOCATIONS if k != "Black Market"), state="readonly", bootstyle="dark")
    from_menu.pack(side=tk.LEFT, padx=5)

    #tb.Label(control_frame, text="To:", bootstyle="info").pack(side=tk.LEFT)
    #to_menu = tb.Combobox(control_frame, textvariable=to_var, values=list(LOCATIONS.keys()), state="readonly", bootstyle="dark")
    #to_menu.pack(side=tk.LEFT, padx=5)
    #to_menu.bind("<<ComboboxSelected>>", to_change)
    
    #tb.Label(control_frame, text="Order Type", bootstyle="info").pack(side=tk.LEFT)
    #order_menu = tb.Combobox(control_frame, textvariable=order_var, values=list(['Buy','Sell']), state="readonly", bootstyle="dark")
    #order_menu.pack(side=tk.LEFT, padx=5)
    #to_change(None)

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
        order = order_var.get()
        material_prices = get_price_inputs()
        new_data = find_flip(selected_from, selected_to, premium_var.get(), material_prices, order)
        if new_data: 
            label.pack_forget()
            update_table(new_data)
        else: 
            label.pack(side=tk.LEFT, padx=10)
            update_table([])

    premium_var = tk.BooleanVar(value=True)  # Checked by default
    tb.Checkbutton(control_frame, text="Premium", variable=premium_var, bootstyle="success-round-toggle").pack(side=tk.LEFT, padx=10)
    tb.Button(control_frame, text="Find Flips!", command=on_refresh, bootstyle="primary").pack(side=tk.LEFT, padx=10)
    tb.Button(control_frame, text="Clear data", command=on_clear, bootstyle="danger").pack(side=tk.LEFT, padx=10)
    label = tb.Label(
        control_frame,
        text="⚠️ No profitable flips found.",
        foreground="orange",
        font=("Segoe UI", 10, "bold"),
        bootstyle="warning"
        )
    label.pack(side=tk.LEFT, padx=10)
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
        if col in ("buy_price", "sell_price", "buy_quality", "sell_quality", "buy_amount", "sell_amount", "buy_location", "sell_location", "profit"):
            tree.column(col, anchor="center", width=100, stretch=False)
        elif col == "enchantment": 
            tree.column(col, anchor="center", width=200)
        elif col in ("ItemTypeId", "sell_enchantment"):
            tree.column(col, anchor="center", width=160)
        else: 
            tree.column(col, anchor="center", width=100)
    tree.column("buy_id", width=0, stretch=False)
    tree.heading("buy_id", text="")  # hide heading
    tree.column("sell_id", width=0, stretch=False)
    tree.heading("sell_id", text="")  # hide heading

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview, bootstyle="secondary")
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)

    global popup
    popup = None  # Global reference

    def hide_popup(event=None):
        global popup
        if popup and popup.winfo_exists():
            # Check if click was inside popup
            widget = event.widget
            if widget is popup or str(widget).startswith(str(popup)):
                # Click inside popup — do nothing
                return
            popup.destroy()

    def show_custom_popup(event):
        global popup

        row_id = tree.identify_row(event.y)
        if not row_id:
            return

        tree.selection_set(row_id)
        tree.focus(row_id)

        # Destroy old popup if exists
        if popup and popup.winfo_exists():
            popup.destroy()

        #popup = tb.Frame(root, bootstyle="darkly", relief="raised", borderwidth=1)
        #btn = tb.Button(popup, text="Claim Flip", bootstyle="dark", command=lambda: claim_and_close_popup(row_id))
        #btn.pack(padx=5, pady=5)
        #popup.place(x=event.x_root - root.winfo_rootx(), y=event.y_root - root.winfo_rooty())

    def claim_and_close_popup(row_id):
        values = tree.item(row_id, "values")
        flip = {"item": values[1], "enchantment": values[9], "profit": values[10]}
        claim_flip(flip)
        delete_row(values[0], values[5])
        on_refresh()
        popup.destroy()

    tree.bind("<Button-3>", show_custom_popup)
    root.bind("<Button-1>", hide_popup)




    # Right: Material Prices in one vertical column grouped by tier
    price_frame = tb.Labelframe(content_frame, text="Material Prices", padding=10)
    price_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0), anchor="n")

    def populate_material_prices(reset=False):
        selected_from = LOCATIONS[from_var.get()]
        for tier in tiers:
            for mat in materials:
                item_type = f"T{tier}_{mat}"
                if not reset: 
                    avg_price = get_average_material_price(item_type, selected_from)
                else: 
                    avg_price = 0
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
    tb.Button(price_frame, text="Reset Prices", command=lambda: populate_material_prices(True), bootstyle="danger").pack(fill="x", pady=(10, 0))
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
    root.geometry("1600x900")
    #root.minsize(width=1280, height=900)
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
