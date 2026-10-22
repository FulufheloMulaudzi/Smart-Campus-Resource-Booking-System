# Smart Campus Resource Booking System

**Student Name:** Fulufhelo Mulaudzi 
**Student Number:** 402601594  
**GitHub Repository:** [Enter Your GitHub Link Here]  
**Module:** Programming 512  
**Institution:** Richfield Graduate Institution  

---

## Project Overview
The Smart Campus Resource Booking System is a Python application developed to replace manual, fragmented booking processes (emails and spreadsheets) across multiple campuses. The system provides a centralized, GUI-based solution for managing shared academic resources (Computer Labs, Projectors, Seminar Rooms, and Equipment). It enforces campus-specific booking policies, prevents double bookings, and generates analytical reports.

## Features Implemented (100% Project Guide Coverage)

### 1. Object-Oriented Programming (Section 3)
*   **Encapsulation:** The `User` class hides the password attribute (`__password`) and provides controlled access via `get_password()`, `check_password()` and `set_password()`.
*   **Inheritance:** `Lecturer`, `CampusAdmin`, and `SystemOperator` inherit from the base `User` class using `User.__init__()`.
*   **Polymorphism:** The `Display()`, `view_dashboard()` and `build_dashboard_tabs()` methods behave differently depending on the user role that calls them.

### 2. Data Structures (Section 2)
*   **Dictionary:** `CAMPUS_RULES` stores the specific booking policies for Centurion, Pretoria, and Durban.
*   **Set:** `resource_id_set` is actively used for O(1) duplicate detection when adding new resources.
*   **List:** `resources_list` stores the loaded resources for display in the GUI.

### 3. Core Logic & Rules (Sections 4.2, 4.3, 5.1, 5.2)
*   **Policy Enforcement:** Bookings are automatically validated against the active campus's maximum duration and opening hours.
*   **Overlap Detection:** Mathematically prevents double bookings using the formula `NOT (new_end <= old_start OR new_start >= old_end)`.
*   **Duplicate Rejection:** Attempting to register an existing Resource ID is rejected by both the Python `SET` and the SQLite `PRIMARY KEY`.
*   **Future Expansion:** A new campus needs only one line in `rules.DEFAULT_CAMPUSES` (or one `database.add_campus()` call). Rules, GUI lists and reports update automatically.

### 4. Graphical User Interface (Section 4.1)
*   Built purely with **Tkinter** (using standard `tk` and `ttk` widgets).
*   **4 Main Pages:** Welcome (Role Selection) -> Login -> Campus Select (Lecturers only) -> Dashboard.
*   **Active Campus & Policy Labels:** Displayed prominently at the top of *every* page as required by the brief.
*   **Real-Time Availability:** The Lecturer booking tab displays live free/booked slots for the selected date.

### 5. Database Persistence (Section 8)
*   Uses **SQLite** (`campus.db`).
*   **4 Tables:** `users`, `campuses`, `resources`, and `bookings`.
*   Data automatically persists between program executions. Passwords are securely hashed using PBKDF2-SHA256.

### 6. Reporting (Section 7)
*   **Campus Admin:** Views total bookings, average duration, most used resources, availability, and daily trends.
*   **System Operator:** Views cross-campus comparisons, resource usage and system-wide booking trends.

---

## How to Run the Application

### Prerequisites
*   Python 3.8 or higher installed on your system.
*   Tkinter (comes pre-installed with standard Python on Windows and macOS; on some Linux systems install it with `sudo apt install python3-tk`).

### Step-by-Step Setup
1. **Clone the Repository:**
   ```bash
   git clone [Your GitHub Link Here]
   cd SmartCampus
   ```
2. **Run the Application:**
   ```bash
   python main.py
   ```

*(Note: On the first run, the database `campus.db` is created automatically and seeded with default users, campuses, and resources.)*

---

##  Default Login Credentials (For Testing)
The database is pre-seeded with the following accounts for evaluation purposes:

| Role | Username | Password | Campus Access |
| :--- | :--- | :--- | :--- |
| **Lecturer** | `lecturer1` | `lect123` | Can select any campus |
| **Campus Admin** | `admin_centurion` | `admin123` | Locked to Centurion |
| **Campus Admin** | `admin_pretoria` | `admin123` | Locked to Pretoria |
| **Campus Admin** | `admin_durban` | `admin123` | Locked to Durban |
| **System Operator** | `operator1` | `op123` | System-Wide (ALL) |

New lecturers can also create an account with the **Register** button on the Lecturer login screen.

### Campus Booking Policies
| Campus | Max booking length | Opening hours |
| :--- | :--- | :--- |
| Centurion | 2 hours | 08:00 - 17:00 |
| Pretoria | 4 hours | 08:00 - 18:00 |
| Durban | 3 hours | 07:00 - 16:00 |

---

## Project Structure
The project follows a clean, modular 5-file architecture (plus supporting sub-packages):

```text
SmartCampus/
│
├── main.py                  # Entry point - initializes DB and launches GUI
├── database.py              # All SQLite queries, seed data, and password hashing
├── models.py                # OOP Classes (User, Lecturer, CampusAdmin, SystemOperator)
├── rules.py                 # Data structures, campus rules, and overlap logic
├── gui.py                   # Main Tkinter window and page navigation coordinator
├── campus.db                # Auto-generated SQLite database
│
├── pages/                   # Sub-package for GUI Pages
│   ├── __init__.py
│   ├── page_welcome.py      # Role selection screen
│   ├── page_login.py        # Login & Registration screen
│   ├── page_campus.py       # Campus selection screen
│   └── page_dashboard.py    # Dashboard router (loads tabs based on role)
│
└── tabs/                    # Sub-package for Dashboard Tabs
    ├── __init__.py
    ├── helpers.py           # Shared UI components (buttons, trees)
    ├── tabs_lecturer.py     # Booking, Availability, Active Bookings, History
    ├── tabs_admin.py        # Resource management, availability, usage, campus reports
    └── tabs_operator.py     # Cross-campus comparison, resources, system trends
```

---

##  Testing Checklist (For the Marker)

1. **Policy Validation:** Login as `lecturer1`, choose **Centurion**. On *Book Resource*, pick a Lab, any future date, start `09:00` and duration `3`. The system rejects it with *"Maximum duration for Centurion is 2h"* (the active policy is shown in the top banner). Start `16:00` with duration `2` is also rejected because Centurion closes at 17:00.
2. **Overlap Validation:** Using a future date (e.g. tomorrow), book a resource for `09:00` with duration `2` (09:00 - 11:00). Then try the same resource at `10:00` for `1` hour. The system rejects it as an overlap, while `11:00` is accepted because bookings may touch end-to-start.
3. **Duplicate Rejection:** Login as `admin_centurion`. On *Manage Resources*, try to add a resource with the ID `LAB-CEN-01`. The system rejects it via the SET (IDs are case-insensitive, so `lab-cen-01` is also rejected).
4. **Persistence:** Create a booking, close the application completely, and reopen it. The booking is still listed under *My Active Bookings*.
5. **Admin Locking:** Login as `admin_pretoria`. The header shows *Active Campus: Pretoria*, the dashboard title shows *Campus: Pretoria (Locked)*, and only Pretoria resources and bookings are visible. There is no way to change the campus.
6. **System Operator Access:** Login as `operator1` (password `op123`). The system skips campus selection and opens the dashboard directly. The header shows *Active Campus: ALL* and *Policy: System Wide - All Campus Rules Apply*, and the dashboard title shows *ALL CAMPUSES*.
7. **Cross-Campus Comparison:** On the *Campus Comparison* tab, all three campuses are listed side by side with their max booking length, opening hours, number of resources, total bookings, hours booked, average duration and most used resource. A summary sentence below the table explains how the campus rules shape usage. Make a booking as a lecturer, then press *Refresh Comparison* to see the figures update.
8. **Resource Data Across Campuses:** On the *Resources & Usage* tab, every resource from every campus is listed with its bookings and hours booked. Use the *Campus filter* (ALL, Centurion, Pretoria, Durban) to narrow the list.
9. **System-Wide Bookings:** On the *All Bookings* tab, bookings from all campuses appear in one list, including the user, resource, date, start time, duration and campus.
10. **Booking Trends:** On the *Booking Trends* tab, the number of bookings per campus per date is shown. Bookings made on different dates or campuses appear as separate rows.
11. **Operator is View-Only:** The operator tabs contain no booking, cancel, add, update or remove controls. Operators can only view and compare data.

> **Tip:** The booking date defaults to today. Bookings in the past are rejected, and for today the start time must be later than the current hour, so use tomorrow's date when testing.
