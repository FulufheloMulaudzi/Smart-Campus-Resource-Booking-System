"""OPERATOR TABS - Sections 3.3, 7.2 (system-wide view)"""
import tkinter as tk
from tkinter import ttk

import database
import rules
from tabs import helpers


def build(app, notebook):
    """Build the system operator dashboard tabs."""
    build_comparison_tab(app, notebook)
    build_resources_tab(app, notebook)
    build_all_bookings_tab(app, notebook)
    build_trends_tab(app, notebook)


# ------------------------------------------------------------
# TAB 1: Cross-campus comparison - Section 7.2
# ------------------------------------------------------------
def build_comparison_tab(app, notebook):
    frame = tk.Frame(notebook, bg="white")
    notebook.add(frame, text="Campus Comparison")
    helpers.make_title(frame, "Cross-Campus Comparison")

    cols = ("Campus", "Max Hours", "Open Hours", "Resources", "Bookings",
            "Hours Booked", "Avg Duration", "Most Used", "Count")
    app.comp_tree = helpers.make_tree(frame, cols, (90, 75, 100, 75, 75, 90, 85, 100, 55), height=5)
    app.comp_insight = tk.Label(frame, text="", font=("Arial", 10), bg="white", fg="#2c3e50",
                                justify="left", wraplength=900)
    app.comp_insight.pack(pady=6)
    helpers.make_button(frame, "Refresh Comparison", lambda: refresh_comparison(app), "#9b59b6", 25, True).pack(pady=8)
    refresh_comparison(app)


def refresh_comparison(app):
    if not hasattr(app, "comp_tree"):
        return
    data = app.current_user.compare_campuses()
    helpers.fill_tree(app.comp_tree, [
        (d["campus"], f"{d['max_hours']}h", d["open_hours"], d["resources"], d["bookings"],
         f"{d['total_hours']}h", f"{d['average']}h", d["most_used"], d["most_used_count"])
        for d in data])
    app.comp_insight.config(text=build_insight(data))


def build_insight(data):
    """One-paragraph summary of how campus rules shape booking behaviour (Section 7.2)."""
    busy = [d for d in data if d["bookings"] > 0]
    if not busy:
        return "No bookings yet - make some bookings to see how campus rules affect usage."
    most = max(busy, key=lambda d: d["bookings"])
    longest = max(busy, key=lambda d: d["average"])
    return (f"Most bookings: {most['campus']} ({most['bookings']}). "
            f"Longest average booking: {longest['campus']} ({longest['average']}h, "
            f"policy limit {longest['max_hours']}h per booking). "
            f"Shorter limits and shorter opening hours cap how many hours a campus can book.")


# ------------------------------------------------------------
# TAB 2: Resources + usage across all campuses (Sections 3.3, 7.2)
# ------------------------------------------------------------
def build_resources_tab(app, notebook):
    frame = tk.Frame(notebook, bg="white")
    notebook.add(frame, text="Resources & Usage")
    helpers.make_title(frame, "Resources & Usage - All Campuses")

    row = tk.Frame(frame, bg="white")
    row.pack(pady=4)
    tk.Label(row, text="Campus filter:", font=("Arial", 11), bg="white").pack(side="left", padx=5)
    app.op_campus_filter = ttk.Combobox(row, values=["ALL"] + rules.get_campus_names(),
                                        state="readonly", width=15)
    app.op_campus_filter.set("ALL")
    app.op_campus_filter.pack(side="left", padx=5)
    app.op_campus_filter.bind("<<ComboboxSelected>>", lambda e: refresh_resources(app))
    helpers.make_button(row, "Refresh", lambda: refresh_resources(app), "#3498db", 10).pack(side="left", padx=5)

    app.op_resources_tree = helpers.make_tree(
        frame, ("Resource", "Name", "Type", "Campus", "Bookings", "Hours Booked"),
        (110, 230, 110, 100, 80, 100))
    refresh_resources(app)


def refresh_resources(app):
    if not hasattr(app, "op_resources_tree"):
        return
    usage = database.resource_usage(app.op_campus_filter.get() or "ALL")
    helpers.fill_tree(app.op_resources_tree,
                      [(u["id"], u["name"], u["type"], u["campus"], u["bookings"], f"{u['hours']}h")
                       for u in usage])


# ------------------------------------------------------------
# TAB 3: Every booking
# ------------------------------------------------------------
def build_all_bookings_tab(app, notebook):
    frame = tk.Frame(notebook, bg="white")
    notebook.add(frame, text="All Bookings")
    helpers.make_title(frame, "All Bookings - All Campuses")
    app.all_campus_tree = helpers.make_tree(
        frame, ("ID", "User", "Resource", "Date", "Start", "Duration", "Campus"),
        (60, 120, 120, 100, 70, 80, 100))
    helpers.make_button(frame, "Refresh", lambda: refresh_all_campus(app)).pack(pady=8)
    refresh_all_campus(app)


def refresh_all_campus(app):
    if not hasattr(app, "all_campus_tree"):
        return
    rows = [(b["id"], b["username"], b["resource_id"], b["date"],
             rules.fmt_hour(b["start_time"]), f"{b['duration']}h", b["campus"])
            for b in database.get_campus_bookings("ALL")]
    helpers.fill_tree(app.all_campus_tree, rows)


# ------------------------------------------------------------
# TAB 4: Booking trends - Section 7.2
# ------------------------------------------------------------
def build_trends_tab(app, notebook):
    frame = tk.Frame(notebook, bg="white")
    notebook.add(frame, text="Booking Trends")
    helpers.make_title(frame, "Booking Trends - by Date & Campus")
    app.trends_tree = helpers.make_tree(frame, ("Campus", "Date", "Bookings That Day"), (160, 160, 160))
    helpers.make_button(frame, "Refresh Trends", lambda: refresh_trends(app), "#9b59b6").pack(pady=8)
    refresh_trends(app)


def refresh_trends(app):
    if not hasattr(app, "trends_tree"):
        return
    helpers.fill_tree(app.trends_tree, database.booking_trends("ALL"))
