import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.tableview import Tableview
from tkinter import ttk
import tkinter as tk
from db import truncate
from PIL import Image, ImageTk
import sys
import os

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
    "ItemTypeId", "buy_location", "buy_quality", "buy_enchantment",
    "buy_price", "sell_location", "sell_quality", "sell_enchantment",
    "sell_price", "enchantment", "profit", "tax"
]

HEADINGS = [
    "Buy Item",
    "Buy Location",
    "Buy Quality",
    "Buy Enchantment",
    "Buy Price",
    "Sell Location",
    "Sell Quality",
    "Sell Iten",
    "Sell Price",
    "Enchantment",
    "Profit",
    "Tax"
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

def show_table(initial_data, data_fetch_fn):
    global root, tree, current_data

    root = tb.Window(themename="darkly")
    root.title("Albion Online Black Ledger")
    icon_path = os.path.join(base_path,"blackledger.png")
    photo = ImageTk.PhotoImage(file=icon_path)
    root.wm_iconphoto(False, photo)

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

    def on_clear(): 
        truncate()
        on_refresh()

    def on_refresh():
        selected_from = LOCATIONS[from_var.get()]
        selected_to = LOCATIONS[to_var.get()]
        new_data = data_fetch_fn(selected_from, selected_to)
        update_table(new_data)

    tb.Button(control_frame, text="Refresh", command=on_refresh, bootstyle="primary").pack(side=tk.LEFT, padx=10)
    tb.Button(control_frame, text="Clear data", command=on_clear, bootstyle="danger").pack(side=tk.LEFT, padx=10)

    # === Table ===
    frame = tb.Frame(root, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)
    style = tb.Style()
    style.configure("dark.Treeview", rowheight=140)
    tree = ttk.Treeview(frame, columns=COLUMNS, show="headings", style="dark.Treeview")
    for col,heading in zip(COLUMNS, HEADINGS):
        tree.heading(col, text=heading, command=lambda c=col: sort_column(tree, c, False))
        tree.column(col, anchor="center", width=100)

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview, bootstyle="secondary")
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)

    current_data = initial_data
    update_table(current_data)

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
