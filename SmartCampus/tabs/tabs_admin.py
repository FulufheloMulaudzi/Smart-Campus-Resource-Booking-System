"""ADMIN TABS - Section 3.2 (campus is locked to the admin's own campus)"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

import database
import rules
from tabs import helpers

RESOURCE_TYPES = ["Laboratory", "Projector", "Seminar Room", "Equipment"]


def build(app, notebook):
    """Build the campus admin dashboard tabs."""
    build_resources_tab(app, notebook)
    build_bookings_tab(app, notebook)
    build_availability_tab(app, notebook)
    build_usage_tab(app, notebook)
    build_reports_tab(app, notebook)


# ------------------------------------------------------------
# TAB 1: Manage resources - add / update / remove (Sections 3.2, 4.2)
# ------------------------------------------------------------
def build_resources_tab(app, notebook):
    frame = tk.Frame(notebook, bg="white")
    notebook.add(frame, text="Manage Resources")
    helpers.make_title(frame, f"Manage Resources - {app.active_campus}")

    form = tk.Frame(frame, bg="white")
    form.pack(pady=6)
    tk.Label(form, text="Resource ID:", font=("Arial", 11), bg="white").grid(row=0, column=0, sticky="e", pady=4)
    app.new_res_id = tk.Entry(form, font=("Arial", 11), width=35)
    app.new_res_id.grid(row=0, column=1, pady=4, padx=10)
    tk.Label(form, text="Name:", font=("Arial", 11), bg="white").grid(row=1, column=0, sticky="e", pady=4)
    app.new_res_name = tk.Entry(form, font=("Arial", 11), width=35)
    app.new_res_name.grid(row=1, column=1, pady=4, padx=10)
    tk.Label(form, text="Type:", font=("Arial", 11), bg="white").grid(row=2, column=0, sticky="e", pady=4)
    app.new_res_type = ttk.Combobox(form, values=RESOURCE_TYPES, width=33)
    app.new_res_type.grid(row=2, column=1, pady=4, padx=10)

    tk.Label(frame, text="Tip: select a row to edit it, then press 'Update Selected'. "
                         "The Resource ID cannot be changed.",
             font=("Arial", 9), bg="white", fg="#7f8c8d").pack()

    row = tk.Frame(frame, bg="white")
    row.pack(pady=8)
    helpers.make_button(row, "Add Resource", lambda: do_add_resource(app), "#27ae60", 15, True).pack(side="left", padx=4)
    helpers.make_button(row, "Update Selected", lambda: do_update_resource(app), "#f39c12", 15).pack(side="left", padx=4)
    helpers.make_button(row, "Remove Selected", lambda: do_remove_resource(app), "#e74c3c", 15).pack(side="left", padx=4)
    helpers.make_button(row, "Clear Form", lambda: clear_form(app), "#95a5a6", 12).pack(side="left", padx=4)
    helpers.make_button(row, "Refresh", lambda: refresh_resources_tree(app, reload=True), "#3498db", 10).pack(side="left", padx=4)

    app.resources_tree = helpers.make_tree(frame, ("ID", "Name", "Type", "Campus"), (130, 280, 140, 120), height=7)
    app.resources_tree.bind("<<TreeviewSelect>>", lambda e: on_resource_select(app))
    refresh_resources_tree(app)


def refresh_resources_tree(app, reload=False):
    """Show this campus's resources from the LIST (re-synced with the DB on request)."""
    if not hasattr(app, "resources_tree"):
        return
    if reload:
        database.reload_structures()
    rows = [(r["id"], r["name"], r["type"], r["campus"])
            for r in rules.get_resources_by_campus(app.active_campus)]
    helpers.fill_tree(app.resources_tree, rows)


def clear_form(app):
    app.new_res_id.delete(0, tk.END)
    app.new_res_name.delete(0, tk.END)
    app.new_res_type.set("")


def on_resource_select(app):
    """Copy the selected row into the form so it can be edited."""
    selection = app.resources_tree.selection()
    if not selection:
        return
    values = app.resources_tree.item(selection[0])["values"]
    clear_form(app)
    app.new_res_id.insert(0, values[0])
    app.new_res_name.insert(0, values[1])
    app.new_res_type.set(values[2])


def do_add_resource(app):
    """Add a resource - the SET detects duplicates (Section 4.2)."""
    success, msg = app.current_user.add_resource(
        app.new_res_id.get(), app.new_res_name.get(), app.new_res_type.get())
    if success:
        messagebox.showinfo("Success", msg)
        clear_form(app)
        refresh_resources_tree(app)
    else:
        messagebox.showerror("Resource Rejected", msg)


def do_update_resource(app):
    """Update the name/type of an existing resource (Section 3.2)."""
    if not app.resources_tree.selection():
        messagebox.showerror("Error", "Select a resource in the list first")
        return
    success, msg = app.current_user.update_resource(
        app.new_res_id.get(), app.new_res_name.get(), app.new_res_type.get())
    if success:
        messagebox.showinfo("Success", msg)
        refresh_resources_tree(app)
    else:
        messagebox.showerror("Update Failed", msg)


def do_remove_resource(app):
    """Remove the selected resource (refused if it still has bookings)."""
    selection = app.resources_tree.selection()
    if not selection:
        messagebox.showerror("Error", "Please select a resource to remove")
        return
    res_id = app.resources_tree.item(selection[0])["values"][0]
    if messagebox.askyesno("Confirm", f"Remove resource '{res_id}'?"):
        success, msg = app.current_user.remove_resource(res_id)
        if success:
            messagebox.showinfo("Success", msg)
            clear_form(app)
            refresh_resources_tree(app)
        else:
            messagebox.showerror("Cannot Remove", msg)


# ------------------------------------------------------------
# TAB 2: All bookings for this campus (Section 3.2)
# ------------------------------------------------------------
def build_bookings_tab(app, notebook):
    frame = tk.Frame(notebook, bg="white")
    notebook.add(frame, text="Campus Bookings")
    helpers.make_title(frame, f"All Bookings - {app.active_campus}")
    app.campus_bookings_tree = helpers.make_tree(
        frame, ("ID", "User", "Resource", "Date", "Start", "Duration"), (60, 140, 130, 110, 80, 80))
    helpers.make_button(frame, "Refresh", lambda: refresh_campus_bookings(app)).pack(pady=8)
    refresh_campus_bookings(app)


def refresh_campus_bookings(app):
    if not hasattr(app, "campus_bookings_tree"):
        return
    rows = [(b["id"], b["username"], b["resource_id"], b["date"],
             rules.fmt_hour(b["start_time"]), f"{b['duration']}h")
            for b in app.current_user.view_campus_bookings()]
    helpers.fill_tree(app.campus_bookings_tree, rows)


# ------------------------------------------------------------
# TAB 3: Resource availability on a chosen date (Section 3.2 - monitor availability)
# ------------------------------------------------------------
def build_availability_tab(app, notebook):
    frame = tk.Frame(notebook, bg="white")
    notebook.add(frame, text="Availability")
    helpers.make_title(frame, f"Resource Availability - {app.active_campus}")

    row = tk.Frame(frame, bg="white")
    row.pack(pady=6)
    tk.Label(row, text="Date (YYYY-MM-DD):", font=("Arial", 11), bg="white").pack(side="left", padx=5)
    app.admin_avail_date = tk.Entry(row, font=("Arial", 11), width=14)
    app.admin_avail_date.pack(side="left", padx=5)
    app.admin_avail_date.insert(0, date.today().isoformat())
    app.admin_avail_date.bind("<Return>", lambda e: refresh_admin_availability(app))
    helpers.make_button(row, "Check", lambda: refresh_admin_availability(app), "#3498db", 10).pack(side="left", padx=5)

    tk.Label(frame, text=rules.get_policy_label(app.active_campus), font=("Arial", 10),
             bg="white", fg="#e67e22").pack()
    app.admin_avail_tree = helpers.make_tree(frame, ("Resource", "Name", "Booked", "Free"), (110, 230, 250, 250))
    refresh_admin_availability(app)


def refresh_admin_availability(app):
    if not hasattr(app, "admin_avail_tree"):
        return
    chosen = app.admin_avail_date.get().strip()
    try:
        date.fromisoformat(chosen)
    except ValueError:
        messagebox.showerror("Error", "Date must be in YYYY-MM-DD format")
        return
    helpers.fill_tree(app.admin_avail_tree,
                      helpers.availability_rows(database.get_availability(app.active_campus, chosen)))


# ------------------------------------------------------------
# TAB 4: Usage per resource + booking trends (Section 3.2 - usage trends)
# ------------------------------------------------------------
def build_usage_tab(app, notebook):
    frame = tk.Frame(notebook, bg="white")
    notebook.add(frame, text="Usage & Trends")
    helpers.make_title(frame, f"Usage & Trends - {app.active_campus}")

    tk.Label(frame, text="Usage per resource", font=("Arial", 12, "bold"), bg="white").pack()
    app.admin_usage_tree = helpers.make_tree(frame, ("Resource", "Name", "Type", "Bookings", "Hours Booked"),
                                             (110, 220, 120, 90, 110), height=5)
    tk.Label(frame, text="Bookings per day", font=("Arial", 12, "bold"), bg="white").pack()
    app.admin_trend_tree = helpers.make_tree(frame, ("Date", "Bookings That Day"), (200, 200), height=5)
    helpers.make_button(frame, "Refresh", lambda: refresh_usage(app)).pack(pady=6)
    refresh_usage(app)


def refresh_usage(app):
    if not hasattr(app, "admin_usage_tree"):
        return
    usage = database.resource_usage(app.active_campus)
    helpers.fill_tree(app.admin_usage_tree,
                      [(u["id"], u["name"], u["type"], u["bookings"], f"{u['hours']}h") for u in usage])
    trends = database.booking_trends(app.active_campus)
    helpers.fill_tree(app.admin_trend_tree, [(d, n) for _campus, d, n in trends])


# ------------------------------------------------------------
# TAB 5: Campus report - Section 7.1
# ------------------------------------------------------------
def build_reports_tab(app, notebook):
    frame = tk.Frame(notebook, bg="white")
    notebook.add(frame, text="Reports")
    helpers.make_title(frame, f"Campus Report - {app.active_campus}")
    app.admin_report_label = tk.Label(frame, text="", font=("Courier New", 11), bg="white", justify="left")
    app.admin_report_label.pack(pady=15)
    helpers.make_button(frame, "Generate Report", lambda: generate_admin_report(app), "#9b59b6", 20, True).pack(pady=8)
    generate_admin_report(app)


def generate_admin_report(app):
    """Total bookings, average duration and the top 3 resources - Section 7.1."""
    campus = app.active_campus
    top = database.most_used_resources(campus, 3)
    if top:
        top_lines = "\n".join(f"  {i}. {rid:<12} {count} booking(s), {hours}h"
                              for i, (rid, count, hours) in enumerate(top, 1))
    else:
        top_lines = "  None yet"

    report = (
        "========================================\n"
        f" CAMPUS REPORT: {campus}\n"
        f" {rules.get_policy_label(campus)}\n"
        "========================================\n"
        f" Total Bookings:      {database.count_bookings(campus)}\n"
        f" Total Hours Booked:  {database.total_booked_hours(campus)}h\n"
        f" Average Duration:    {database.average_duration(campus)} hours\n"
        " Most Used Resources:\n"
        f"{top_lines}\n"
        "========================================")
    app.admin_report_label.config(text=report)
