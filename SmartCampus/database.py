"""
database.py - SQLite persistence + reports
Section 8 (storage), Section 7 (reports), Sections 4.2, 4.3, 6.1, 6.2

Tables: users, campuses, resources, bookings.
Every query is parameterised and wrapped in try/except sqlite3.Error.
"""

import os
import re
import sqlite3
import hashlib
import secrets
from contextlib import closing
from datetime import date

import rules

# Absolute path so the app works no matter which folder it is launched from.
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "campus.db")

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,20}$")


# ============================================================
# CONNECTION + SMALL QUERY HELPERS
# ============================================================

def get_connection():
    """Open a connection with foreign-key enforcement switched on."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None


def _fetch_all(sql, params=()):
    """Run a SELECT and return all rows ([] on any error)."""
    conn = get_connection()
    if conn is None:
        return []
    try:
        with closing(conn):
            return conn.execute(sql, params).fetchall()
    except sqlite3.Error as e:
        print(f"Query error: {e}")
        return []


def _fetch_one(sql, params=()):
    """Run a SELECT and return the first row (None on error / no rows)."""
    rows = _fetch_all(sql, params)
    return rows[0] if rows else None


def _campus_filter(campus, column="campus"):
    """WHERE-clause helper: 'ALL' means no filter."""
    if campus == "ALL":
        return "", ()
    return f"WHERE {column}=?", (campus,)


# ============================================================
# PASSWORD HELPERS (passwords are never stored in plain text)
# ============================================================

def hash_password(password, salt=None):
    """Salted PBKDF2-SHA256 -> 'pbkdf2$<salt>$<hash>'."""
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"pbkdf2${salt}${digest}"


def verify_password(password, stored):
    """Check a typed password against the stored value."""
    if stored.startswith("pbkdf2$"):
        salt = stored.split("$")[1]
        return secrets.compare_digest(hash_password(password, salt), stored)
    return password == stored  # legacy plain-text value (migrated on start-up)


# ============================================================
# INITIALISATION + SEED DATA
# ============================================================

def init_db():
    """Create tables, seed data, migrate old data, load SET/LIST/rules."""
    conn = get_connection()
    if conn is None:
        return False
    try:
        with closing(conn):
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    campus TEXT
                )""")
            # Section 8: campus information is stored in the database
            conn.execute("""
                CREATE TABLE IF NOT EXISTS campuses (
                    name TEXT PRIMARY KEY,
                    max_hours INTEGER NOT NULL,
                    open_hour INTEGER NOT NULL,
                    close_hour INTEGER NOT NULL
                )""")
            # Section 4.2: resource id is the PRIMARY KEY (unique)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS resources (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    campus TEXT NOT NULL
                )""")
            # Section 4.3: booking linked to lecturer, resource and campus
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    resource_id TEXT NOT NULL,
                    campus TEXT NOT NULL,
                    date TEXT NOT NULL,
                    start_time INTEGER NOT NULL,
                    duration INTEGER NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(resource_id) REFERENCES resources(id)
                )""")
            conn.commit()

            seed_campuses(conn)
            seed_users(conn)
            seed_resources(conn)
            migrate_plain_passwords(conn)

            load_campuses_into_rules(conn)
            load_resources_into_structures(conn)
        return True
    except sqlite3.Error as e:
        print(f"Database init error: {e}")
        return False


def seed_campuses(conn):
    """Insert the default campuses (from rules.DEFAULT_CAMPUSES) if missing."""
    try:
        for name, (max_h, open_h, close_h) in rules.DEFAULT_CAMPUSES.items():
            conn.execute(
                "INSERT OR IGNORE INTO campuses (name, max_hours, open_hour, close_hour) "
                "VALUES (?, ?, ?, ?)", (name, max_h, open_h, close_h))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Seed campuses error: {e}")


def seed_users(conn):
    """Seed default accounts: 3 admins, 1 operator, 1 lecturer."""
    users = [
        ("admin_centurion", "admin123", "CampusAdmin", "Centurion"),
        ("admin_pretoria", "admin123", "CampusAdmin", "Pretoria"),
        ("admin_durban", "admin123", "CampusAdmin", "Durban"),
        ("operator1", "op123", "SystemOperator", "ALL"),
        ("lecturer1", "lect123", "Lecturer", "None"),
    ]
    try:
        for username, password, role, campus in users:
            conn.execute(
                "INSERT OR IGNORE INTO users (username, password, role, campus) "
                "VALUES (?, ?, ?, ?)", (username, hash_password(password), role, campus))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Seed users error: {e}")


def seed_resources(conn):
    """Seed 4 default resources per campus (Section 4.2)."""
    resources = [
        ("LAB-CEN-01", "Centurion Computer Lab 1", "Laboratory", "Centurion"),
        ("PRJ-CEN-01", "Centurion Projector 1", "Projector", "Centurion"),
        ("SEM-CEN-01", "Centurion Seminar Room A", "Seminar Room", "Centurion"),
        ("EQU-CEN-01", "Centurion PA System", "Equipment", "Centurion"),
        ("LAB-PRE-01", "Pretoria Computer Lab 1", "Laboratory", "Pretoria"),
        ("PRJ-PRE-01", "Pretoria Projector 1", "Projector", "Pretoria"),
        ("SEM-PRE-01", "Pretoria Seminar Room A", "Seminar Room", "Pretoria"),
        ("EQU-PRE-01", "Pretoria PA System", "Equipment", "Pretoria"),
        ("LAB-DUR-01", "Durban Computer Lab 1", "Laboratory", "Durban"),
        ("PRJ-DUR-01", "Durban Projector 1", "Projector", "Durban"),
        ("SEM-DUR-01", "Durban Seminar Room A", "Seminar Room", "Durban"),
        ("EQU-DUR-01", "Durban PA System", "Equipment", "Durban"),
    ]
    try:
        for res in resources:
            conn.execute(
                "INSERT OR IGNORE INTO resources (id, name, type, campus) VALUES (?, ?, ?, ?)", res)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Seed resources error: {e}")


def migrate_plain_passwords(conn):
    """Older databases stored plain-text passwords - hash them once."""
    try:
        rows = conn.execute("SELECT id, password FROM users").fetchall()
        for user_id, stored in rows:
            if not stored.startswith("pbkdf2$"):
                conn.execute("UPDATE users SET password=? WHERE id=?",
                             (hash_password(stored), user_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Password migration error: {e}")


def load_campuses_into_rules(conn):
    """Load campuses from the DB into the rules dictionaries (Section 5.2)."""
    try:
        for name, max_h, open_h, close_h in conn.execute(
                "SELECT name, max_hours, open_hour, close_hour FROM campuses"):
            ok, msg = rules.register_campus(name, max_h, open_h, close_h)
            if not ok:
                print(f"Skipped campus '{name}': {msg}")
    except sqlite3.Error as e:
        print(f"Load campuses error: {e}")


def load_resources_into_structures(conn):
    """Fill the SET and LIST from the resources table."""
    try:
        rules.reset_resource_structures()
        for rid, name, rtype, campus in conn.execute(
                "SELECT id, name, type, campus FROM resources ORDER BY campus, id"):
            rules.resource_id_set.add(rid)
            rules.resources_list.append(
                {"id": rid, "name": name, "type": rtype, "campus": campus})
    except sqlite3.Error as e:
        print(f"Load resources error: {e}")


def reload_structures():
    """Re-sync the SET and LIST with the database."""
    conn = get_connection()
    if conn is not None:
        with closing(conn):
            load_resources_into_structures(conn)


# ============================================================
# CAMPUS OPERATIONS - Section 5.2
# ============================================================

def get_campuses():
    """All campuses stored in the database."""
    rows = _fetch_all("SELECT name, max_hours, open_hour, close_hour FROM campuses ORDER BY name")
    return [{"name": r[0], "max_hours": r[1], "open": r[2], "close": r[3]} for r in rows]


def add_campus(name, max_hours, open_hour, close_hour):
    """
    Add a brand-new campus without touching any other code (Section 5.2).
    Returns (success, message).
    """
    ok, msg = rules.register_campus(name, max_hours, open_hour, close_hour)
    if not ok:
        return False, msg
    conn = get_connection()
    if conn is None:
        return False, "Database connection failed"
    try:
        with closing(conn):
            conn.execute(
                "INSERT OR REPLACE INTO campuses (name, max_hours, open_hour, close_hour) "
                "VALUES (?, ?, ?, ?)", (name.strip(), max_hours, open_hour, close_hour))
            conn.commit()
        return True, f"Campus '{name}' added"
    except sqlite3.Error as e:
        return False, f"Database error: {e}"


# ============================================================
# USER OPERATIONS - Sections 3, 8
# ============================================================

def register_user(username, password, role="Lecturer", campus="None"):
    """Register an account. Returns (success, message, user_id)."""
    username = (username or "").strip()
    if not USERNAME_PATTERN.match(username):
        return False, "Username must be 3-20 characters: letters, digits or _", None
    if not password or len(password) < 4:
        return False, "Password must be at least 4 characters", None

    conn = get_connection()
    if conn is None:
        return False, "Database connection failed", None
    try:
        with closing(conn):
            taken = conn.execute(
                "SELECT 1 FROM users WHERE username=? COLLATE NOCASE", (username,)).fetchone()
            if taken:
                return False, "Username already exists", None
            cur = conn.execute(
                "INSERT INTO users (username, password, role, campus) VALUES (?, ?, ?, ?)",
                (username, hash_password(password), role, campus))
            conn.commit()
            return True, "Registration successful", cur.lastrowid
    except sqlite3.IntegrityError:
        return False, "Username already exists", None
    except sqlite3.Error as e:
        return False, f"Registration error: {e}", None


def authenticate(username, password, role):
    """Returns the user dict if credentials + role match, otherwise None."""
    row = _fetch_one(
        "SELECT id, username, password, role, campus FROM users "
        "WHERE username=? COLLATE NOCASE AND role=?", (username, role))
    if row and verify_password(password, row[2]):
        return {"id": row[0], "username": row[1], "password": row[2],
                "role": row[3], "campus": row[4]}
    return None


def update_password(user_id, hashed_password):
    """Store a new (already hashed) password."""
    conn = get_connection()
    if conn is None:
        return False
    try:
        with closing(conn):
            conn.execute("UPDATE users SET password=? WHERE id=?", (hashed_password, user_id))
            conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Update password error: {e}")
        return False


# ============================================================
# RESOURCE OPERATIONS - Section 4.2
# ============================================================

def add_resource(resource_id, name, resource_type, campus):
    """
    Register a resource for a campus. The SET rejects duplicates first,
    then the PRIMARY KEY is a second line of defence. Returns (success, message).
    """
    ok, result = rules.validate_resource_id(resource_id)
    if not ok:
        return False, result
    resource_id = result

    name, resource_type = (name or "").strip(), (resource_type or "").strip()
    if not name or not resource_type:
        return False, "Name and type are required"
    if campus not in rules.CAMPUS_RULES:
        return False, f"Unknown campus '{campus}'"

    # SET duplicate check (Section 4.2)
    if rules.is_duplicate_resource(resource_id):
        return False, f"REJECTED: Duplicate resource ID '{resource_id}' already exists"

    conn = get_connection()
    if conn is None:
        return False, "Database connection failed"
    try:
        with closing(conn):
            conn.execute(
                "INSERT INTO resources (id, name, type, campus) VALUES (?, ?, ?, ?)",
                (resource_id, name, resource_type, campus))
            conn.commit()
        rules.add_resource_to_set(resource_id)
        rules.add_resource_to_list(
            {"id": resource_id, "name": name, "type": resource_type, "campus": campus})
        return True, f"Resource '{resource_id}' added successfully"
    except sqlite3.IntegrityError:
        return False, f"REJECTED: Duplicate resource ID '{resource_id}' (database constraint)"
    except sqlite3.Error as e:
        return False, f"Database error: {e}"


def update_resource(resource_id, name, resource_type, campus="ALL"):
    """Update name/type. If a campus is given, only that campus's resource may change."""
    resource_id = rules.normalise_resource_id(resource_id)
    name, resource_type = (name or "").strip(), (resource_type or "").strip()
    if not name or not resource_type:
        return False, "Name and type are required"

    conn = get_connection()
    if conn is None:
        return False, "Database connection failed"
    try:
        with closing(conn):
            if campus == "ALL":
                cur = conn.execute("UPDATE resources SET name=?, type=? WHERE id=?",
                                   (name, resource_type, resource_id))
            else:
                cur = conn.execute(
                    "UPDATE resources SET name=?, type=? WHERE id=? AND campus=?",
                    (name, resource_type, resource_id, campus))
            if cur.rowcount == 0:
                return False, f"Resource '{resource_id}' not found on this campus"
            conn.commit()
        for r in rules.resources_list:
            if r["id"] == resource_id:
                r["name"], r["type"] = name, resource_type
                break
        return True, f"Resource '{resource_id}' updated"
    except sqlite3.Error as e:
        return False, f"Update error: {e}"


def remove_resource(resource_id, campus="ALL"):
    """Remove a resource. Refused while it still has bookings on record."""
    resource_id = rules.normalise_resource_id(resource_id)
    conn = get_connection()
    if conn is None:
        return False, "Database connection failed"
    try:
        with closing(conn):
            count = conn.execute(
                "SELECT COUNT(*) FROM bookings WHERE resource_id=?", (resource_id,)).fetchone()[0]
            if count > 0:
                return False, (f"Cannot remove '{resource_id}': it has {count} booking(s) "
                               f"on record. Cancel or archive them first.")
            if campus == "ALL":
                cur = conn.execute("DELETE FROM resources WHERE id=?", (resource_id,))
            else:
                cur = conn.execute("DELETE FROM resources WHERE id=? AND campus=?",
                                   (resource_id, campus))
            if cur.rowcount == 0:
                return False, f"Resource '{resource_id}' not found on this campus"
            conn.commit()
        rules.resource_id_set.discard(resource_id)
        rules.resources_list[:] = [r for r in rules.resources_list if r["id"] != resource_id]
        return True, f"Resource '{resource_id}' removed"
    except sqlite3.Error as e:
        return False, f"Remove error: {e}"


def get_resources(campus):
    """Resources straight from the database ('ALL' = every campus)."""
    where, params = _campus_filter(campus)
    rows = _fetch_all(f"SELECT id, name, type, campus FROM resources {where} ORDER BY campus, id", params)
    return [{"id": r[0], "name": r[1], "type": r[2], "campus": r[3]} for r in rows]


# ============================================================
# BOOKING OPERATIONS - Sections 4.3, 6.1, 6.2
# ============================================================

def get_existing_bookings(resource_id, booking_date):
    """(start_time, duration) tuples for one resource on one date."""
    rows = _fetch_all(
        "SELECT start_time, duration FROM bookings WHERE resource_id=? AND date=?",
        (resource_id, booking_date))
    return [(r[0], r[1]) for r in rows]


def create_booking(user_id, resource_id, campus, booking_date, start_time, duration):
    """Raw INSERT - call make_booking() instead so rules are always enforced."""
    conn = get_connection()
    if conn is None:
        return False, "Database connection failed"
    try:
        with closing(conn):
            conn.execute(
                "INSERT INTO bookings (user_id, resource_id, campus, date, start_time, duration) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, resource_id, campus, booking_date, start_time, duration))
            conn.commit()
        return True, "Booking created successfully"
    except sqlite3.Error as e:
        return False, f"Booking error: {e}"


def make_booking(user_id, resource_id, campus, booking_date, start_time, duration):
    """
    Validate then save a booking (Sections 4.3, 5.1, 6.2):
      1. the resource exists and belongs to the campus
      2. date is not in the past
      3. campus policy (rules.check_policy)
      4. no overlap (rules.check_overlap)
    Returns (success, message).
    """
    row = _fetch_one("SELECT campus FROM resources WHERE id=?", (resource_id,))
    if row is None:
        return False, f"Resource '{resource_id}' does not exist"
    if row[0] != campus:
        return False, f"Resource '{resource_id}' does not belong to {campus}"

    existing = get_existing_bookings(resource_id, booking_date)
    ok, msg = rules.validate_booking(campus, booking_date, start_time, duration, existing)
    if not ok:
        return False, msg
    return create_booking(user_id, resource_id, campus, booking_date, start_time, duration)


def get_user_bookings(user_id, period="all"):
    """
    A lecturer's bookings (Section 6.1).
    period: 'upcoming' (not yet finished), 'past' (finished) or 'all'.
    """
    rows = _fetch_all(
        """SELECT b.id, b.resource_id, r.name, b.campus, b.date, b.start_time, b.duration
           FROM bookings b LEFT JOIN resources r ON b.resource_id = r.id
           WHERE b.user_id=? ORDER BY b.date, b.start_time""", (user_id,))
    bookings = [{"id": r[0], "resource_id": r[1], "resource_name": r[2] or "(removed)",
                 "campus": r[3], "date": r[4], "start_time": r[5], "duration": r[6]}
                for r in rows]
    if period == "all":
        return bookings
    ended = [rules.booking_has_ended(b["date"], b["start_time"], b["duration"]) for b in bookings]
    if period == "upcoming":
        return [b for b, e in zip(bookings, ended) if not e]
    past = [b for b, e in zip(bookings, ended) if e]
    past.reverse()  # newest first
    return past


def cancel_booking(booking_id, user_id):
    """Cancel one of the user's bookings, only if it has not started yet (Section 6.1)."""
    row = _fetch_one("SELECT date, start_time FROM bookings WHERE id=? AND user_id=?",
                     (booking_id, user_id))
    if row is None:
        return False, "Booking not found"
    if rules.booking_has_started(row[0], row[1]):
        return False, "Only future bookings can be cancelled"

    conn = get_connection()
    if conn is None:
        return False, "Database connection failed"
    try:
        with closing(conn):
            conn.execute("DELETE FROM bookings WHERE id=? AND user_id=?", (booking_id, user_id))
            conn.commit()
        return True, "Booking cancelled"
    except sqlite3.Error as e:
        return False, f"Cancel error: {e}"


def get_campus_bookings(campus):
    """All bookings for a campus ('ALL' = every campus)."""
    where, params = _campus_filter(campus, "b.campus")
    rows = _fetch_all(
        f"""SELECT b.id, u.username, b.resource_id, b.date, b.start_time, b.duration, b.campus
            FROM bookings b JOIN users u ON b.user_id = u.id
            {where} ORDER BY b.campus, b.date, b.start_time""", params)
    return [{"id": r[0], "username": r[1], "resource_id": r[2], "date": r[3],
             "start_time": r[4], "duration": r[5], "campus": r[6]} for r in rows]


def get_availability(campus, booking_date):
    """
    Real-time availability (Section 6.2): for every resource on the campus
    list the booked and free time ranges on the given date.
    """
    result = []
    for res in rules.get_resources_by_campus(campus):
        existing = get_existing_bookings(res["id"], booking_date)
        result.append({
            "id": res["id"], "name": res["name"], "type": res["type"],
            "booked": [(s, s + d) for s, d in sorted(existing)],
            "free": rules.free_slots(campus, existing),
        })
    return result


# ============================================================
# REPORTS - Section 7
# ============================================================

def count_bookings(campus):
    where, params = _campus_filter(campus)
    row = _fetch_one(f"SELECT COUNT(*) FROM bookings {where}", params)
    return row[0] if row else 0


def total_booked_hours(campus):
    where, params = _campus_filter(campus)
    row = _fetch_one(f"SELECT COALESCE(SUM(duration), 0) FROM bookings {where}", params)
    return row[0] if row else 0


def average_duration(campus):
    where, params = _campus_filter(campus)
    row = _fetch_one(f"SELECT AVG(duration) FROM bookings {where}", params)
    return round(row[0], 2) if row and row[0] else 0.0


def most_used_resources(campus, limit=3):
    """Top resources by number of bookings: [(resource_id, bookings, hours)]."""
    where, params = _campus_filter(campus)
    rows = _fetch_all(
        f"""SELECT resource_id, COUNT(*) AS c, SUM(duration) FROM bookings {where}
            GROUP BY resource_id ORDER BY c DESC, resource_id LIMIT ?""", params + (limit,))
    return [(r[0], r[1], r[2]) for r in rows]


def most_used_resource(campus):
    """Single most-used resource as (resource_id, count)."""
    top = most_used_resources(campus, 1)
    return (top[0][0], top[0][1]) if top else (None, 0)


def resource_usage(campus="ALL"):
    """Usage per resource, including resources never booked (Sections 3.2, 7.2)."""
    where, params = _campus_filter(campus, "r.campus")
    rows = _fetch_all(
        f"""SELECT r.id, r.name, r.type, r.campus, COUNT(b.id), COALESCE(SUM(b.duration), 0)
            FROM resources r LEFT JOIN bookings b ON b.resource_id = r.id
            {where} GROUP BY r.id ORDER BY r.campus, COUNT(b.id) DESC, r.id""", params)
    return [{"id": r[0], "name": r[1], "type": r[2], "campus": r[3],
             "bookings": r[4], "hours": r[5]} for r in rows]


def booking_trends(campus="ALL"):
    """Bookings per campus per date: [(campus, date, count)]."""
    where, params = _campus_filter(campus)
    return _fetch_all(
        f"""SELECT campus, date, COUNT(*) FROM bookings {where}
            GROUP BY campus, date ORDER BY campus, date""", params)


def compare_campuses():
    """
    Cross-campus comparison (Section 7.2). Campuses come from the rules
    dictionary, so a new campus appears here automatically.
    """
    results = []
    for campus in rules.get_campus_names():
        rule = rules.CAMPUS_RULES[campus]
        most_id, most_count = most_used_resource(campus)
        results.append({
            "campus": campus,
            "max_hours": rule["max_hours"],
            "open_hours": f"{rules.fmt_hour(rule['open'])}-{rules.fmt_hour(rule['close'])}",
            "resources": len(rules.get_resources_by_campus(campus)),
            "bookings": count_bookings(campus),
            "total_hours": total_booked_hours(campus),
            "average": average_duration(campus),
            "most_used": most_id if most_id else "None",
            "most_used_count": most_count,
        })
    return results
