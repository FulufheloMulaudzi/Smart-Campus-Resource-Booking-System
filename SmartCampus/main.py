"""
main.py - starting point of the Smart Campus Resource Booking System.
Initialises the database (tables, seed data, campus rules) and launches the GUI.

Run with:   python main.py
"""

import database
import gui


if __name__ == "__main__":
    print("Initializing database...")
    if not database.init_db():
        raise SystemExit("Could not initialise the database - see the message above.")
    print("Database ready.")

    print("Launching Smart Campus Resource Booking System...")
    app = gui.SmartCampusApp()
    app.mainloop()
