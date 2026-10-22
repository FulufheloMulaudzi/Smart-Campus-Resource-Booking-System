"""Page 2: CAMPUS SELECT - Section 4.1 (lecturers)"""
import tkinter as tk
from tkinter import messagebox

import rules


def show(app):
    main_frame = tk.Frame(app.container, bg="#f0f0f0")
    main_frame.pack(fill="both", expand=True)
    app.add_header_labels(main_frame)

    content = tk.Frame(main_frame, bg="#f0f0f0")
    content.pack(expand=True)

    tk.Label(content, text="Select Campus", font=("Arial", 22, "bold"),
             bg="#f0f0f0", fg="#2c3e50").pack(pady=25)
    tk.Label(content, text=f"Currently Active Campus: {app.active_campus}",
             font=("Arial", 14), bg="#f0f0f0", fg="#e74c3c").pack(pady=10)

    listbox_frame = tk.Frame(content, bg="white", relief="ridge", bd=2, padx=20, pady=15)
    listbox_frame.pack(pady=20)

    # Campuses come from the rules dictionary, so new campuses appear automatically
    campuses = rules.get_campus_names()
    app.campus_listbox = tk.Listbox(listbox_frame, font=("Arial", 13),
                                    height=max(5, len(campuses)), width=25, selectmode="single",
                                    exportselection=False)
    for c in campuses:
        app.campus_listbox.insert(tk.END, c)
    app.campus_listbox.pack()

    app.policy_preview = tk.Label(content, text="", font=("Arial", 11), bg="#f0f0f0", fg="#7f8c8d")
    app.policy_preview.pack(pady=10)

    # Pre-select the active campus when the lecturer is changing campus
    if app.active_campus in campuses:
        index = campuses.index(app.active_campus)
        app.campus_listbox.selection_set(index)
        on_campus_select(app)

    app.campus_listbox.bind("<<ListboxSelect>>", lambda e: on_campus_select(app))

    tk.Button(content, text="Confirm Campus", font=("Arial", 13, "bold"), bg="#27ae60",
              fg="white", width=20, height=2, command=lambda: confirm_campus(app)).pack(pady=20)

    back_target = "dashboard" if app.current_user and app.active_campus in campuses else "login"
    back_text = "← Back to Dashboard" if back_target == "dashboard" else "← Back to Login"
    tk.Button(content, text=back_text, font=("Arial", 10), bg="#f0f0f0", fg="#7f8c8d",
              command=lambda: app.show_page(back_target)).pack()


def on_campus_select(app):
    """Preview the booking policy of the highlighted campus."""
    selection = app.campus_listbox.curselection()
    if selection:
        campus = app.campus_listbox.get(selection[0])
        app.policy_preview.config(text=rules.get_policy_label(campus))


def confirm_campus(app):
    """Confirm the campus and open the dashboard."""
    selection = app.campus_listbox.curselection()
    if not selection:
        messagebox.showerror("Error", "Please select a campus")
        return
    app.active_campus = app.campus_listbox.get(selection[0])
    app.current_user.campus = app.active_campus      # lecturer's working campus
    app.show_page("dashboard")
