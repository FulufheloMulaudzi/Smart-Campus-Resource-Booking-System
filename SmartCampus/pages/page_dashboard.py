"""Page 3: DASHBOARD - tabs are built by the logged-in user's own class (polymorphism)"""
import tkinter as tk
from tkinter import ttk, messagebox


def show(app):
    main_frame = tk.Frame(app.container, bg="#f0f0f0")
    main_frame.pack(fill="both", expand=True)
    app.add_header_labels(main_frame)

    info_frame = tk.Frame(main_frame, bg="#ecf0f1", pady=8)
    info_frame.pack(fill="x")
    tk.Label(info_frame, text=app.current_user.view_dashboard(), font=("Arial", 14, "bold"),
             bg="#ecf0f1", fg="#2c3e50").pack(side="left", padx=20)

    tk.Button(info_frame, text="My Profile", font=("Arial", 10), bg="#34495e", fg="white",
              command=lambda: messagebox.showinfo("My Profile", app.current_user.Display())
              ).pack(side="right", padx=10)

    if app.selected_role == "Lecturer":
        tk.Button(info_frame, text="Change Campus", font=("Arial", 10), bg="#e67e22", fg="white",
                  command=lambda: app.show_page("campus")).pack(side="right", padx=5)

    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # Polymorphism: Lecturer / CampusAdmin / SystemOperator each build their own tabs
    app.current_user.build_dashboard_tabs(app, notebook)

    tk.Button(main_frame, text="Logout", font=("Arial", 11, "bold"), bg="#e74c3c", fg="white",
              width=15, command=app.logout).pack(pady=8)
