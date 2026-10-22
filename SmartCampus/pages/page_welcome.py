"""Page 0: WELCOME - choose a role"""
import tkinter as tk


def show(app):
    main_frame = tk.Frame(app.container, bg="#f0f0f0")
    main_frame.pack(fill="both", expand=True)
    app.add_header_labels(main_frame)

    content = tk.Frame(main_frame, bg="#f0f0f0")
    content.pack(expand=True)

    tk.Label(content, text="Smart Campus Resource Booking System",
             font=("Arial", 22, "bold"), bg="#f0f0f0", fg="#2c3e50").pack(pady=30)
    tk.Label(content, text="Richfield Graduate Institution",
             font=("Arial", 14), bg="#f0f0f0", fg="#7f8c8d").pack(pady=10)
    tk.Label(content, text="Select your role to continue:",
             font=("Arial", 14), bg="#f0f0f0", fg="#34495e").pack(pady=30)

    btn_frame = tk.Frame(content, bg="#f0f0f0")
    btn_frame.pack(pady=20)

    roles = [
        ("I'm a Lecturer", "Lecturer", "#3498db"),
        ("I'm a Campus Admin", "CampusAdmin", "#e67e22"),
        ("I'm a System Operator", "SystemOperator", "#9b59b6"),
    ]
    for text, role, color in roles:
        tk.Button(btn_frame, text=text, font=("Arial", 13, "bold"), bg=color, fg="white",
                  width=25, height=2,
                  command=lambda r=role: select_role(app, r)).pack(pady=8)


def select_role(app, role):
    """Remember the chosen role and go to the login page."""
    app.selected_role = role
    app.active_campus = "NONE"
    app.show_page("login")
