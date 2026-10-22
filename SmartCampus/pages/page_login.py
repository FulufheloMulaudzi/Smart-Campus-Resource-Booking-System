"""Page 1: LOGIN / REGISTER"""
import tkinter as tk
from tkinter import messagebox

import database
import models


def show(app):
    main_frame = tk.Frame(app.container, bg="#f0f0f0")
    main_frame.pack(fill="both", expand=True)
    app.add_header_labels(main_frame)

    content = tk.Frame(main_frame, bg="#f0f0f0")
    content.pack(expand=True)

    tk.Label(content, text=f"Login as {app.selected_role}", font=("Arial", 20, "bold"),
             bg="#f0f0f0", fg="#2c3e50").pack(pady=25)

    form = tk.Frame(content, bg="#ffffff", padx=40, pady=30, relief="ridge", bd=2)
    form.pack(pady=20)

    tk.Label(form, text="Username:", font=("Arial", 12), bg="white").grid(row=0, column=0, sticky="e", pady=8)
    app.login_username = tk.Entry(form, font=("Arial", 12), width=25)
    app.login_username.grid(row=0, column=1, pady=8, padx=10)

    tk.Label(form, text="Password:", font=("Arial", 12), bg="white").grid(row=1, column=0, sticky="e", pady=8)
    app.login_password = tk.Entry(form, font=("Arial", 12), width=25, show="*")
    app.login_password.grid(row=1, column=1, pady=8, padx=10)
    app.login_password.bind("<Return>", lambda e: do_login(app))   # Enter key logs in

    btn_frame = tk.Frame(form, bg="white")
    btn_frame.grid(row=2, column=0, columnspan=2, pady=20)

    tk.Button(btn_frame, text="Login", font=("Arial", 12, "bold"), bg="#27ae60", fg="white",
              width=12, command=lambda: do_login(app)).pack(side="left", padx=5)

    if app.selected_role == "Lecturer":          # only lecturers can self-register
        tk.Button(btn_frame, text="Register", font=("Arial", 12, "bold"), bg="#3498db", fg="white",
                  width=12, command=lambda: do_register(app)).pack(side="left", padx=5)

    tk.Button(content, text="← Back to Role Selection", font=("Arial", 10), bg="#f0f0f0",
              fg="#7f8c8d", command=lambda: app.show_page("welcome")).pack(pady=15)

    hints = {
        "Lecturer": "Demo account: lecturer1 / lect123\n"
                    "New lecturers: type a username (3-20 letters/digits/_) + password (4+), then Register",
        "CampusAdmin": "Admin accounts are pre-created in the database.\n"
                       "admin_centurion / admin123\nadmin_pretoria / admin123\nadmin_durban / admin123",
        "SystemOperator": "Operator accounts are pre-created in the database.\nOperator: operator1 / op123",
    }
    tk.Label(content, text=hints.get(app.selected_role, ""), font=("Arial", 9),
             bg="#f0f0f0", fg="#95a5a6", justify="center").pack()


def do_login(app):
    """Authenticate and move to the next page - Section 4.1."""
    username = app.login_username.get().strip()
    password = app.login_password.get().strip()

    if not username or not password:
        messagebox.showerror("Error", "Please enter username and password")
        return

    user_data = database.authenticate(username, password, app.selected_role)
    if user_data is None:
        messagebox.showerror("Login Failed", "Invalid username or password for this role")
        return

    # Create the right User subclass (OOP polymorphism)
    if app.selected_role == "Lecturer":
        app.current_user = models.Lecturer(
            user_data["id"], user_data["username"], user_data["password"], user_data["campus"])
    elif app.selected_role == "CampusAdmin":
        app.current_user = models.CampusAdmin(
            user_data["id"], user_data["username"], user_data["password"], user_data["campus"])
    else:
        app.current_user = models.SystemOperator(
            user_data["id"], user_data["username"], user_data["password"])

    if app.selected_role == "SystemOperator":
        app.active_campus = "ALL"
        app.show_page("dashboard")
    elif app.selected_role == "CampusAdmin":
        app.active_campus = app.current_user.getCampus()   # locked to their campus
        app.show_page("dashboard")
    else:
        app.show_page("campus")                            # lecturers pick a campus


def do_register(app):
    """Register a new lecturer account."""
    username = app.login_username.get().strip()
    password = app.login_password.get().strip()

    if not username or not password:
        messagebox.showerror("Error", "Please enter username and password")
        return

    success, msg, _user_id = database.register_user(username, password, "Lecturer", "None")
    if success:
        messagebox.showinfo("Success", f"Account '{username}' registered! You can now login.")
        app.login_username.delete(0, tk.END)
        app.login_password.delete(0, tk.END)
    else:
        messagebox.showerror("Registration Failed", msg)
