import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk
import tkinter as tk
from db import truncate_flips
from db import truncate_claimed
import sys
import os
from flipper import get_average_material_price
from flipper import find_flip
from flipper import claim_flip
from flipper import delete_row
import psutil
from flipper import get_all_claims
from flipper import get_profit
from flipper import delete_claim


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

CLAIMED_COLUMNS = [
    "id", "buy_id", "ItemTypeId", "buy_location", "buy_quality", "buy_amount", 
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

CLAIMED_HEADINGS = [
    "Id",
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

def is_process_running(name: str) -> bool:
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and name.lower() in proc.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

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

    profit = get_profit()
    global profit_var
    profit_var = tk.StringVar(value=profit)
    
    profit_label = tb.Label(
        control_frame,
        textvariable=profit_var,
        font=("Segoe UI", 10, "bold"),
        bootstyle="success"  # or "success-inverse" for green text on dark bg
    )
    profit_label.pack(side="right", fill="x", padx=10, pady=5)
    

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

    def clear_claimed():
        truncate_claimed()
        update_table([], claimed_tree)
        profit_var.set(get_profit())

    def clear_flips():
        truncate_flips()
        on_refresh()

    def on_refresh():
        selected_from = LOCATIONS[from_var.get()]
        selected_to = LOCATIONS[to_var.get()]
        order = order_var.get()
        material_prices = get_price_inputs()
        new_data = find_flip(selected_from, selected_to, premium_var.get(), material_prices, order)
        if new_data: 
            label.pack_forget()
            update_table(new_data, tree)
        else: 
            label.pack(side=tk.LEFT, padx=10)
            update_table([], tree)

    premium_var = tk.BooleanVar(value=True)  # Checked by default
    tb.Checkbutton(control_frame, text="Premium", variable=premium_var, bootstyle="success-round-toggle").pack(side=tk.LEFT, padx=10)
    tb.Button(control_frame, text="Find Flips!", command=on_refresh, bootstyle="primary").pack(side=tk.LEFT, padx=10)
    tb.Button(control_frame, text="Clear Flips", command=clear_flips, bootstyle="danger").pack(side=tk.LEFT, padx=10)
    tb.Button(control_frame, text="Clear Claimed", command=clear_claimed, bootstyle="danger").pack(side=tk.LEFT, padx=10)
    label = tb.Label(
        control_frame,
        text="⚠️ No profitable flips found.",
        foreground="orange",
        font=("Segoe UI", 10, "bold"),
        bootstyle="warning"
        )
    label.pack(side=tk.LEFT, padx=10)
    label.pack_forget()

    # === Status Label === 
    status_label = tk.Label(root, text="", font=("Segoe UI", 10), anchor="e", justify="right")
    status_label.pack(side="bottom", fill="x", padx=10)

    # === Main Content Frame ===
    content_frame = tb.Frame(root, padding=2)
    content_frame.pack(fill=tk.BOTH, expand=True)

    # === Notebook (Tabs) ===
    notebook = ttk.Notebook(content_frame)
    notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Tab 1: Available Flips
    available_tab = tb.Frame(notebook)
    notebook.add(available_tab, text="Available Flips")

    # Tab 2: Claimed Flips
    claimed_tab = tb.Frame(notebook)
    notebook.add(claimed_tab, text="Claimed Flips")

    # Left: Table frame
    table_frame = tb.Frame(available_tab)
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
        print(event)
        global popup

        row_id = tree.identify_row(event.y)
        if not row_id:
            return

        tree.selection_set(row_id)
        tree.focus(row_id)

        # Destroy old popup if exists
        if popup and popup.winfo_exists():
            popup.destroy()

        popup = tb.Frame(root, bootstyle="darkly", relief="raised", borderwidth=1)
        btn = tb.Button(popup, text="Claim Flip", bootstyle="dark", command=lambda: claim_and_close_popup(row_id))
        btn.pack(padx=5, pady=5)
        popup.place(x=event.x_root - root.winfo_rootx(), y=event.y_root - root.winfo_rooty())

    def get_row_as_dict(tree, row_id):
        row_values = tree.item(row_id)["values"]
        columns = tree["columns"]
        row_dict = dict(zip(columns, row_values))
        return row_dict

    def claim_and_close_popup(row):
        flip = get_row_as_dict(tree, row)
        claim_flip(flip)
        delete_row(flip['buy_id'], flip['sell_id'])
        on_refresh()
        data = get_all_claims()
        update_table(data, claimed_tree)
        profit_var.set(get_profit())
        popup.destroy()

    tree.bind("<Button-3>", show_custom_popup)
    root.bind("<Button-1>", hide_popup)

    # Right: Material Prices in one vertical column grouped by tier
    price_frame = tb.Labelframe(available_tab, text="Material Prices", padding=10)
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

    # Claimed Flips treeview
    claimed_tree = ttk.Treeview(claimed_tab, columns=CLAIMED_COLUMNS, show="headings", style="dark.Treeview")
    for col, heading in zip(CLAIMED_COLUMNS, CLAIMED_HEADINGS):
        claimed_tree.heading(col, text=heading, command=lambda c=col: sort_column(claimed_tree, c, False))
        if col in ("buy_price", "sell_price", "buy_quality", "sell_quality", "buy_amount", "sell_amount", "buy_location", "sell_location", "profit"):
            claimed_tree.column(col, anchor="center", width=100, stretch=False)
        elif col == "enchantment": 
            claimed_tree.column(col, anchor="center", width=200)
        elif col in ("ItemTypeId", "sell_enchantment"):
            claimed_tree.column(col, anchor="center", width=160)
        else: 
            claimed_tree.column(col, anchor="center", width=100)
    claimed_tree.column("id", width=0, stretch=False)
    claimed_tree.heading("id", text="")  # hide heading
    claimed_tree.column("buy_id", width=0, stretch=False)
    claimed_tree.heading("buy_id", text="")  # hide heading
    claimed_tree.column("sell_id", width=0, stretch=False)
    claimed_tree.heading("sell_id", text="")  # hide heading

    scrollbar_claimed = ttk.Scrollbar(claimed_tab, orient="vertical", command=claimed_tree.yview, bootstyle="secondary")
    claimed_tree.configure(yscroll=scrollbar_claimed.set)
    scrollbar_claimed.pack(side=tk.RIGHT, fill=tk.Y)
    claimed_tree.pack(fill=tk.BOTH, expand=True)
    
    global claimed_popup
    claimed_popup = None  # separate popup variable for claimed_tree

    def hide_claimed_popup(event=None):
        global claimed_popup
        if claimed_popup and claimed_popup.winfo_exists():
            widget = event.widget
            if widget is claimed_popup or str(widget).startswith(str(claimed_popup)):
                return
            claimed_popup.destroy()

    def show_claimed_popup(event):
        global claimed_popup
        row_id = claimed_tree.identify_row(event.y)
        if not row_id:
            return

        claimed_tree.selection_set(row_id)
        claimed_tree.focus(row_id)

        if claimed_popup and claimed_popup.winfo_exists():
            claimed_popup.destroy()

        claimed_popup = tb.Frame(root, bootstyle="darkly", relief="raised", borderwidth=1)
        btn = tb.Button(claimed_popup, text="Delete Claim", bootstyle="dark", command=lambda: delete_claim_and_close_popup(row_id))
        btn.pack(padx=5, pady=5)
        claimed_popup.place(x=event.x_root - root.winfo_rootx(), y=event.y_root - root.winfo_rooty())

    def delete_claim_and_close_popup(row_id):
        values = claimed_tree.item(row_id, "values")
        print(values)
        delete_claim(values[0])
        data = get_all_claims()
        update_table(data, claimed_tree)
        profit_var.set(get_profit())
        if claimed_popup:
            claimed_popup.destroy()

    # Bind the events on claimed_tree:
    claimed_tree.bind("<Button-3>", show_claimed_popup)
    root.bind("<Button-1>", hide_claimed_popup)

    root.geometry("1600x900")
    #root.minsize(width=1280, height=900)

    def update_status():
        if is_process_running("albiondata-client"):
            status_label.config(text="🟢 Data Client is running", fg="green")
        else:
            status_label.config(text="⭕ Data Client is NOT running", fg="red")
        root.after(3000, update_status)  # check again in 3 seconds

    update_status()
    claimed_data = get_all_claims()
    update_table(claimed_data, claimed_tree)
    root.mainloop()

def update_table(data, tree):
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
