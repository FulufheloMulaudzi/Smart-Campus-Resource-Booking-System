"""
rules.py - Data Structures and Core Logic (no GUI, no SQL)
Sections 2, 4.2, 4.3, 5.1, 5.2

Data structures used here:
  * DICTIONARY  - CAMPUS_RULES / CAMPUS_RULE_OBJECTS (campus -> rules)
  * SET         - resource_id_set (fast duplicate resource-ID detection)
  * LIST        - resources_list (resources shown in the GUI)

Section 5.2 (future expansion): to add a campus, add ONE line to
DEFAULT_CAMPUSES below (or insert a row into the `campuses` table).
Everything else - rule objects, GUI lists, reports - is built from it.
"""

import re
from datetime import date, datetime

# ============================================================
# CAMPUS CONFIGURATION - the single place campuses are defined
# ============================================================

# name: (max_hours per booking, opening hour, closing hour)
DEFAULT_CAMPUSES = {
    "Centurion": (2, 8, 17),
    "Pretoria": (4, 8, 18),
    "Durban": (3, 7, 16),
}

# DICTIONARY: campus -> {"max_hours", "open", "close"}   (filled by register_campus)
CAMPUS_RULES = {}
# DICTIONARY: campus -> BookingRule object               (filled by register_campus)
CAMPUS_RULE_OBJECTS = {}

# SET - duplicate resource-ID detection (Section 4.2)
resource_id_set = set()

# LIST - resources for display (Sections 4.3 / 6.2)
resources_list = []


def fmt_hour(hour):
    """8 -> '08:00' (used everywhere a time is shown)."""
    return f"{hour:02d}:00"


# ============================================================
# BOOKING RULE CLASS - Section 5.1
# ============================================================

class BookingRule:
    """One campus's booking policy (max duration + opening hours)."""

    def __init__(self, campus, max_hours, open_h, close_h):
        self.campus = campus
        self.max_hours = max_hours
        self.open_h = open_h
        self.close_h = close_h

    def check(self, duration, start_time):
        """Check a booking against this policy. Returns (bool, message)."""
        if not isinstance(duration, int) or not isinstance(start_time, int):
            return False, "Start time and duration must be whole numbers"
        if start_time < 0 or start_time > 23:
            return False, "Start time must be an hour between 0 and 23"
        if duration <= 0:
            return False, "Duration must be at least 1 hour"
        if duration > self.max_hours:
            return False, f"Maximum duration for {self.campus} is {self.max_hours}h"
        if start_time < self.open_h:
            return False, f"{self.campus} opens at {fmt_hour(self.open_h)}"
        end = start_time + duration
        if end > self.close_h:
            return False, (f"{self.campus} closes at {fmt_hour(self.close_h)} - "
                           f"this booking would end at {fmt_hour(end)}")
        return True, "OK"

    def __str__(self):
        return (f"{self.campus}: Max {self.max_hours}h, "
                f"{fmt_hour(self.open_h)}-{fmt_hour(self.close_h)}")


def register_campus(campus, max_hours, open_h, close_h):
    """
    Add (or replace) a campus. Keeps the dictionary and the rule objects in sync.
    Returns (bool, message).
    """
    if not campus or not str(campus).strip():
        return False, "Campus name is required"
    if not (0 <= open_h < close_h <= 24):
        return False, "Opening hour must be before closing hour (0-24)"
    if not (1 <= max_hours <= close_h - open_h):
        return False, "Max hours must fit inside the opening hours"
    campus = str(campus).strip()
    CAMPUS_RULES[campus] = {"max_hours": max_hours, "open": open_h, "close": close_h}
    CAMPUS_RULE_OBJECTS[campus] = BookingRule(campus, max_hours, open_h, close_h)
    return True, "OK"


# Load the default campuses at import time.
for _name, (_max, _open, _close) in DEFAULT_CAMPUSES.items():
    register_campus(_name, _max, _open, _close)


def get_campus_names():
    """Names of every registered campus (used by GUI and reports)."""
    return list(CAMPUS_RULES.keys())


# ============================================================
# POLICY + BOOKING VALIDATION - Sections 4.3, 5.1
# ============================================================

def get_rule(campus):
    """Return (BookingRule or None, message). Unknown campus gives an explicit error."""
    if campus not in CAMPUS_RULE_OBJECTS:
        return None, (f"ERROR: Unknown campus '{campus}'. "
                      f"Valid campuses: {get_campus_names()}")
    return CAMPUS_RULE_OBJECTS[campus], "OK"


def check_policy(campus, duration, start_time):
    """Does this booking meet the campus policy? Returns (bool, message)."""
    rule, msg = get_rule(campus)
    if rule is None:
        return False, msg
    return rule.check(duration, start_time)


def check_overlap(existing_bookings, new_start, new_duration):
    """
    Section 4.3 - overlap detection.
    existing_bookings: list of (start_time, duration) for the same resource + date.
    Returns True if there IS an overlap (booking must be rejected).
    A booking overlaps unless it ends before/at the old start or starts at/after the old end.
    """
    new_end = new_start + new_duration
    for old_start, old_duration in existing_bookings:
        old_end = old_start + old_duration
        if not (new_end <= old_start or new_start >= old_end):
            return True
    return False


def validate_booking(campus, booking_date, start_time, duration, existing,
                     today=None, now_hour=None):
    """
    Full booking validation: date -> campus policy -> overlap.
    Returns (bool, message). `today` / `now_hour` can be injected for testing.
    """
    try:
        booking_day = date.fromisoformat(booking_date)
    except (ValueError, TypeError):
        return False, "Date must be in YYYY-MM-DD format"

    today = today or date.today()
    if now_hour is None:
        now_hour = datetime.now().hour

    if booking_day < today:
        return False, "You cannot book a date in the past"

    ok, msg = check_policy(campus, duration, start_time)
    if not ok:
        return False, msg

    if booking_day == today and start_time <= now_hour:
        return False, "That start time has already begun or passed today"

    if check_overlap(existing, start_time, duration):
        return False, "Overlap detected - the resource is already booked at that time"

    return True, "OK"


def booking_has_started(booking_date, start_time, now=None):
    """True if the booking's start time is now or in the past."""
    now = now or datetime.now()
    booking_day = date.fromisoformat(booking_date)
    if booking_day != now.date():
        return booking_day < now.date()
    return start_time <= now.hour


def booking_has_ended(booking_date, start_time, duration, now=None):
    """True if the booking is completely finished (used for 'past history')."""
    now = now or datetime.now()
    booking_day = date.fromisoformat(booking_date)
    if booking_day != now.date():
        return booking_day < now.date()
    return (start_time + duration) <= now.hour


# ============================================================
# AVAILABILITY - Section 6.2
# ============================================================

def free_slots(campus, existing):
    """
    Free time ranges for one resource on one day, inside the campus's opening hours.
    existing: list of (start, duration). Returns list of (start_hour, end_hour).
    """
    rule, _ = get_rule(campus)
    if rule is None:
        return []
    free = []
    cursor = rule.open_h
    for start, duration in sorted(existing):
        if start > cursor:
            free.append((cursor, min(start, rule.close_h)))
        cursor = max(cursor, start + duration)
    if cursor < rule.close_h:
        free.append((cursor, rule.close_h))
    return free


def format_ranges(ranges):
    """[(8, 10), (12, 14)] -> '08:00-10:00, 12:00-14:00' (or 'None')."""
    if not ranges:
        return "None"
    return ", ".join(f"{fmt_hour(a)}-{fmt_hour(b)}" for a, b in ranges)


# ============================================================
# RESOURCE ID / SET + LIST FUNCTIONS - Section 4.2
# ============================================================

RESOURCE_ID_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]{2,19}$")


def normalise_resource_id(resource_id):
    """Trim + upper-case so 'lab-cen-01' and 'LAB-CEN-01' count as the same ID."""
    return (resource_id or "").strip().upper()


def validate_resource_id(resource_id):
    """Returns (True, normalised_id) or (False, error_message)."""
    rid = normalise_resource_id(resource_id)
    if not RESOURCE_ID_PATTERN.match(rid):
        return False, "Resource ID must be 3-20 characters: letters, digits, - or _"
    return True, rid


def is_duplicate_resource(resource_id):
    """SET lookup - O(1) duplicate detection."""
    return resource_id in resource_id_set


def add_resource_to_set(resource_id):
    """Add to the SET. Returns (bool, message) - False if it is a duplicate."""
    if resource_id in resource_id_set:
        return False, f"Duplicate resource ID: {resource_id}"
    resource_id_set.add(resource_id)
    return True, "Added to set"


def add_resource_to_list(resource):
    """Append a resource dict to the LIST."""
    resources_list.append(resource)
    return True


def get_resources_by_campus(campus):
    """Filter the LIST by campus ('ALL' returns every resource)."""
    if campus == "ALL":
        return list(resources_list)
    return [r for r in resources_list if r.get("campus") == campus]


def get_policy_label(campus):
    """Policy text shown on every GUI page - Section 5.1."""
    if campus in CAMPUS_RULES:
        rule = CAMPUS_RULES[campus]
        return (f"Policy: Max {rule['max_hours']}h per booking, "
                f"{fmt_hour(rule['open'])}-{fmt_hour(rule['close'])}")
    return "Policy: No campus selected"


def reset_resource_structures():
    """Clear SET and LIST (used when re-loading from the database)."""
    resource_id_set.clear()
    resources_list.clear()
