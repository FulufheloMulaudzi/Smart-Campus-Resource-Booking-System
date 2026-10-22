"""LECTURER TABS - Sections 3.1, 4.3, 6.1, 6.2"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

import database
import rules
from tabs import helpers

BOOKING_COLUMNS = ("ID", "Resource", "Name", "Campus", "Date", "Start", "Duration")
BOOKING_WIDTHS = (50, 100, 190, 90, 100, 70, 80)


def build(app, notebook):
    """Build the lecturer dashboard tabs."""
    build_book_tab(app, notebook)
    build_upcoming_tab(app, notebook)
    build_history_tab(app, notebook)


# ------------------------------------------------------------
# TAB 1: Book Resource + real-time availability
# ------------------------------------------------------------
def build_book_tab(app, notebook):
    rule, _ = rules.get_rule(app.active_campus)

    frame = tk.Frame(notebook, bg="white")
    notebook.add(frame, text="Book Resource")
    helpers.make_title(frame, "Book a Resource")
    tk.Label(frame, text=rules.get_policy_label(app.active_campus), font=("Arial", 11, "bold"),
             bg="white", fg="#e67e22").pack()

    form = tk.Frame(frame, bg="white")
    form.pack(pady=8)

    tk.Label(form, text="Resource:", font=("Arial", 11), bg="white").grid(row=0, column=0, sticky="e", pady=4)
    app.book_resource_var = tk.StringVar()
    app.book_resource_combo = ttk.Combobox(form, textvariable=app.book_resource_var,
                                           state="readonly", width=40)
    app.book_resource_combo.grid(row=0, column=1, pady=4, padx=10)

    tk.Label(form, text="Date (YYYY-MM-DD):", font=("Arial", 11), bg="white").grid(row=1, column=0, sticky="e", pady=4)
    app.book_date = tk.Entry(form, font=("Arial", 11), width=42)
    app.book_date.grid(row=1, column=1, pady=4, padx=10)
    app.book_date.insert(0, date.today().isoformat())
    # availability follows the date typed in (Section 6.2 - real time)
    app.book_date.bind("<Return>", lambda e: refresh_availability(app))
    app.book_date.bind("<FocusOut>", lambda e: refresh_availability(app))

    # Start times and durations are limited to what this campus's policy allows
    start_values = [rules.fmt_hour(h) for h in range(rule.open_h, rule.close_h)] if rule else []
    duration_values = [str(h) for h in range(1, rule.max_hours + 1)] if rule else []

    tk.Label(form, text="Start Time:", font=("Arial", 11), bg="white").grid(row=2, column=0, sticky="e", pady=4)
    app.book_start_var = tk.StringVar()
    ttk.Combobox(form, textvariable=app.book_start_var, values=start_values,
                 state="readonly", width=40).grid(row=2, column=1, pady=4, padx=10)

    tk.Label(form, text="Duration (hours):", font=("Arial", 11), bg="white").grid(row=3, column=0, sticky="e", pady=4)
    app.book_duration_var = tk.StringVar()
    ttk.Combobox(form, textvariable=app.book_duration_var, values=duration_values,
                 state="readonly", width=40).grid(row=3, column=1, pady=4, padx=10)

    btns = tk.Frame(frame, bg="white")
    btns.pack(pady=8)
    helpers.make_button(btns, "Book Resource", lambda: do_booking(app), "#27ae60", 22, True).pack(side="left", padx=5)
    helpers.make_button(btns, "Check Availability", lambda: refresh_availability(app), "#3498db", 22).pack(side="left", padx=5)

    app.availability_label = tk.Label(frame, text="", font=("Arial", 10, "bold"), bg="white", fg="#7f8c8d")
    app.availability_label.pack()
    app.avail_tree = helpers.make_tree(frame, ("Resource", "Name", "Booked", "Free"),
                                       (110, 230, 230, 230), height=6)

    refresh_book_resources(app)
    refresh_availability(app)


def refresh_book_resources(app):
    """Fill the resource dropdown from the resources LIST (Section 6.2)."""
    resources = rules.get_resources_by_campus(app.active_campus)
    values = [f"{r['id']} - {r['name']}" for r in resources]
    app.book_resource_combo["values"] = values
    if values and app.book_resource_var.get() not in values:
        app.book_resource_combo.current(0)


def refresh_availability(app):
    """Show booked + free times for every resource on the chosen date (Section 6.2)."""
    if not hasattr(app, "avail_tree"):
        return
    chosen = app.book_date.get().strip()
    try:
        date.fromisoformat(chosen)
    except ValueError:
        app.availability_label.config(text="Enter a valid date (YYYY-MM-DD) to see availability")
        helpers.fill_tree(app.avail_tree, [])
        return
    app.availability_label.config(text=f"Live availability on {chosen} - {app.active_campus}")
    helpers.fill_tree(app.avail_tree,
                      helpers.availability_rows(database.get_availability(app.active_campus, chosen)))


def do_booking(app):
    """Read the form and ask the Lecturer object to book (policy + overlap checks inside)."""
    res_display = app.book_resource_var.get()
    if not res_display:
        messagebox.showerror("Error", "Please select a resource")
        return
    resource_id = res_display.split(" - ")[0]
    booking_date = app.book_date.get().strip()

    start_text = app.book_start_var.get()
    duration_text = app.book_duration_var.get()
    if not start_text or not duration_text:
        messagebox.showerror("Error", "Please choose a start time and a duration")
        return
    try:
        start_time = int(start_text.split(":")[0])
        duration = int(duration_text)
    except ValueError:
        messagebox.showerror("Error", "Start time and duration must be valid")
        return

    success, msg = app.current_user.book_resource(resource_id, booking_date, start_time, duration)
    if success:
        messagebox.showinfo("Success", f"Booking confirmed!\n{resource_id} on {booking_date} "
                                       f"at {rules.fmt_hour(start_time)} for {duration}h")
        refresh_availability(app)
        refresh_upcoming(app)
        refresh_history(app)
    else:
        messagebox.showerror("Booking Rejected", msg)


# ------------------------------------------------------------
# TAB 2: Active (upcoming) bookings + cancel
# ------------------------------------------------------------
def build_upcoming_tab(app, notebook):
    frame = tk.Frame(notebook, bg="white")
    notebook.add(frame, text="My Active Bookings")
    helpers.make_title(frame, "My Active Bookings")

    app.upcoming_tree = helpers.make_tree(frame, BOOKING_COLUMNS, BOOKING_WIDTHS)
    row = tk.Frame(frame, bg="white")
    row.pack(pady=8)
    helpers.make_button(row, "Refresh", lambda: refresh_upcoming(app)).pack(side="left", padx=5)
    helpers.make_button(row, "Cancel Selected", lambda: do_cancel_booking(app), "#e74c3c").pack(side="left", padx=5)
    refresh_upcoming(app)


def booking_rows(bookings):
    return [(b["id"], b["resource_id"], b["resource_name"], b["campus"], b["date"],
             rules.fmt_hour(b["start_time"]), f"{b['duration']}h") for b in bookings]


def refresh_upcoming(app):
    if hasattr(app, "upcoming_tree"):
        helpers.fill_tree(app.upcoming_tree, booking_rows(app.current_user.view_my_bookings("upcoming")))


def do_cancel_booking(app):
    """Cancel the selected future booking - Section 6.1."""
    selection = app.upcoming_tree.selection()
    if not selection:
        messagebox.showerror("Error", "Please select a booking to cancel")
        return
    booking_id = app.upcoming_tree.item(selection[0])["values"][0]
    if messagebox.askyesno("Confirm", f"Cancel booking #{booking_id}?"):
        success, msg = app.current_user.cancel_booking(booking_id)
        if success:
            messagebox.showinfo("Success", "Booking cancelled")
            refresh_upcoming(app)
            refresh_availability(app)
        else:
            messagebox.showerror("Error", msg)


# ------------------------------------------------------------
# TAB 3: Past booking history
# ------------------------------------------------------------
def build_history_tab(app, notebook):
    frame = tk.Frame(notebook, bg="white")
    notebook.add(frame, text="Booking History")
    helpers.make_title(frame, "Past Booking History")
    app.history_tree = helpers.make_tree(frame, BOOKING_COLUMNS, BOOKING_WIDTHS)
    helpers.make_button(frame, "Refresh", lambda: refresh_history(app)).pack(pady=8)
    refresh_history(app)


def refresh_history(app):
    if hasattr(app, "history_tree"):
        helpers.fill_tree(app.history_tree, booking_rows(app.current_user.view_my_bookings("past")))
