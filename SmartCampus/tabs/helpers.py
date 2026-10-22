"""Small shared GUI helpers so the tab modules stay short and consistent."""
import tkinter as tk
from tkinter import ttk

import rules


def make_title(parent, text):
    """Large heading at the top of a tab."""
    label = tk.Label(parent, text=text, font=("Arial", 16, "bold"), bg="white")
    label.pack(pady=(12, 6))
    return label


def make_tree(parent, columns, widths=None, height=10):
    """Treeview with a vertical scrollbar. Returns the Treeview."""
    frame = tk.Frame(parent, bg="white")
    frame.pack(fill="both", expand=True, padx=15, pady=8)
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=height)
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)
    for i, col in enumerate(columns):
        tree.heading(col, text=col)
        width = widths[i] if widths else 110
        tree.column(col, width=width, anchor="center")
    return tree


def fill_tree(tree, rows):
    """Replace everything in a Treeview with the given rows (list of tuples)."""
    for item in tree.get_children():
        tree.delete(item)
    for row in rows:
        tree.insert("", "end", values=row)


def make_button(parent, text, command, color="#3498db", width=16, bold=False):
    """Coloured button used across all tabs."""
    font = ("Arial", 11, "bold") if bold else ("Arial", 11)
    return tk.Button(parent, text=text, font=font, bg=color, fg="white", width=width, command=command)


def availability_rows(availability):
    """Convert database.get_availability() output into Treeview rows."""
    return [(a["id"], a["name"], rules.format_ranges(a["booked"]), rules.format_ranges(a["free"]))
            for a in availability]
