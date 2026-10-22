"""
gui.py - Main Tkinter window and page navigation
Sections 4.1, 5.1
4 pages: Welcome -> Login -> Campus Select (lecturers) -> Dashboard
"""

import tkinter as tk

import rules
from pages import page_welcome, page_login, page_campus, page_dashboard


class SmartCampusApp:
    """Main GUI application: owns the window, the session state and page switching."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Smart Campus Resource Booking System")
        self.root.geometry("1000x720")
        self.root.configure(bg="#f0f0f0")

        # Project title bar
        self.project_title = tk.Label(
            self.root, text="Smart Campus Resource Booking System",
            font=("Arial", 10, "bold"), bg="#2c3e50", fg="white", pady=6, wraplength=980)
        self.project_title.pack(fill="x", side="top")

        # Session state
        self.current_user = None
        self.selected_role = None
        self.active_campus = "NONE"

        # Container that holds the current page
        self.container = tk.Frame(self.root, bg="#f0f0f0")
        self.container.pack(fill="both", expand=True)

        # Page registry (page name -> function that draws it)
        self.pages = {
            "welcome": page_welcome.show,
            "login": page_login.show,
            "campus": page_campus.show,
            "dashboard": page_dashboard.show,
        }
        self.show_page("welcome")

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_page(self, page_name):
        """Switch to a page (the container is cleared first)."""
        self.clear_container()
        if page_name in self.pages:
            self.pages[page_name](self)

    def get_active_campus_label(self):
        """Section 4.1 - the active campus is always visible."""
        return f"Active Campus: {self.active_campus}"

    def get_policy_label(self):
        """Section 5.1 - the booking policy in effect is always visible."""
        if self.active_campus == "ALL":
            return "Policy: System Wide - All Campus Rules Apply"
        return rules.get_policy_label(self.active_campus)

    def add_header_labels(self, parent):
        """Active Campus + Policy banner shown at the top of every page."""
        header = tk.Frame(parent, bg="#2c3e50", pady=10)
        header.pack(fill="x")
        tk.Label(header, text=self.get_active_campus_label(),
                 font=("Arial", 12, "bold"), fg="white", bg="#2c3e50").pack(side="left", padx=20)
        tk.Label(header, text=self.get_policy_label(),
                 font=("Arial", 11), fg="#ecf0f1", bg="#2c3e50").pack(side="right", padx=20)

    def logout(self):
        self.current_user = None
        self.selected_role = None
        self.active_campus = "NONE"
        self.show_page("welcome")

    def mainloop(self):
        self.root.mainloop()
