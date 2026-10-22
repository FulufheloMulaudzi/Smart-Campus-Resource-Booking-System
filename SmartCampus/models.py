"""
models.py - Object-Oriented Programming Classes
Section 3

Demonstrates:
  * Classes + inheritance  : Lecturer, CampusAdmin, SystemOperator extend User
  * Encapsulation          : the password is a private attribute (__password)
  * Polymorphism           : Display(), view_dashboard() and build_dashboard_tabs()
                             behave differently in every subclass
"""

import database


class User:
    """Base user. The (hashed) password is private - Section 3 encapsulation."""

    def __init__(self, user_id, username, password, role, campus):
        self.user_id = user_id
        self.username = username
        self.__password = password      # private attribute
        self.role = role
        self.campus = campus

    # ---- accessors (controlled access to private data) ----
    def get_password(self):
        """Return the stored (hashed) password."""
        return self.__password

    def check_password(self, plain_text):
        """Verify a typed password without exposing the stored value."""
        return database.verify_password(plain_text, self.__password)

    def set_password(self, new_password):
        """Validate, hash, save to the database and store a new password."""
        if not new_password or len(new_password) < 4:
            return False
        hashed = database.hash_password(new_password)
        if database.update_password(self.user_id, hashed):
            self.__password = hashed
            return True
        return False

    def getUsername(self):
        return self.username

    def getUserId(self):
        return self.user_id

    def getCampus(self):
        return self.campus

    # ---- polymorphic behaviour ----
    def describe(self):
        return f"{self.role}: {self.username} (Campus: {self.campus})"

    def Display(self):
        """Profile text - overridden by every subclass."""
        return (f"USER PROFILE\n{self.describe()}\n"
                f"Username: {self.username}\nCampus: {self.campus}\nRole: {self.role}")

    def view_dashboard(self):
        """Dashboard heading - overridden by every subclass."""
        return f"Welcome {self.username} - Role: {self.role}"

    def build_dashboard_tabs(self, app, notebook):
        """Each role builds its own tabs (polymorphism)."""
        raise NotImplementedError("Each user role must define its own dashboard tabs")


class Lecturer(User):
    """Section 3.1 - registers, logs in, books resources, manages own bookings."""

    def __init__(self, user_id, username, password, campus="None"):
        User.__init__(self, user_id, username, password, "Lecturer", campus)

    def Display(self):
        campus = self.campus if self.campus != "None" else "Not Selected"
        return (f"LECTURER PROFILE\n{self.describe()}\n"
                f"Username: {self.username}\nCampus: {campus}\nRole: Lecturer")

    def view_dashboard(self):
        return f"LECTURER DASHBOARD - {self.username} | Campus: {self.campus}"

    def build_dashboard_tabs(self, app, notebook):
        from tabs import tabs_lecturer      # imported here so models has no GUI dependency
        tabs_lecturer.build(app, notebook)

    def book_resource(self, resource_id, booking_date, start_time, duration):
        """Validate + save a booking for this lecturer. Returns (success, message)."""
        return database.make_booking(self.user_id, resource_id, self.campus,
                                     booking_date, start_time, duration)

    def view_my_bookings(self, period="all"):
        """'upcoming', 'past' or 'all' bookings from the database."""
        return database.get_user_bookings(self.user_id, period)

    def cancel_booking(self, booking_id):
        return database.cancel_booking(booking_id, self.user_id)


class CampusAdmin(User):
    """Section 3.2 - locked to one campus; manages that campus's resources."""

    def __init__(self, user_id, username, password, campus):
        User.__init__(self, user_id, username, password, "CampusAdmin", campus)

    def Display(self):
        return (f"CAMPUS ADMIN PROFILE\n{self.describe()}\n"
                f"Username: {self.username}\nCampus: {self.campus} (LOCKED)\n"
                f"Role: Campus Administrator")

    def view_dashboard(self):
        return f"CAMPUS ADMIN DASHBOARD - {self.username} | Campus: {self.campus} (Locked)"

    def build_dashboard_tabs(self, app, notebook):
        from tabs import tabs_admin
        tabs_admin.build(app, notebook)

    def add_resource(self, resource_id, name, resource_type):
        return database.add_resource(resource_id, name, resource_type, self.campus)

    def update_resource(self, resource_id, name, resource_type):
        return database.update_resource(resource_id, name, resource_type, self.campus)

    def remove_resource(self, resource_id):
        return database.remove_resource(resource_id, self.campus)

    def view_campus_bookings(self):
        return database.get_campus_bookings(self.campus)


class SystemOperator(User):
    """Section 3.3 - system-wide access; campus is always 'ALL'."""

    def __init__(self, user_id, username, password):
        User.__init__(self, user_id, username, password, "SystemOperator", "ALL")

    def Display(self):
        return (f"SYSTEM OPERATOR PROFILE\n{self.describe()}\n"
                f"Username: {self.username}\nCampus: ALL CAMPUSES (System Wide)\n"
                f"Role: System Operator")

    def view_dashboard(self):
        return f"SYSTEM OPERATOR DASHBOARD - {self.username} | ALL CAMPUSES"

    def build_dashboard_tabs(self, app, notebook):
        from tabs import tabs_operator
        tabs_operator.build(app, notebook)

    def view_all_campuses(self):
        return database.get_campuses()

    def compare_campuses(self):
        return database.compare_campuses()
