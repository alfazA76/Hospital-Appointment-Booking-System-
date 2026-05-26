# MedBook 🩺
### Hospital Appointment Booking System

Welcome to **MedBook**! This is a complete, secure, and production-ready healthcare management application built with **Flask**, **SQLAlchemy (SQLite)**, and **Bootstrap 5**.

We designed the system with a modern, premium **Teal & Mint** color palette, a robust database layer, strict role-based access control (RBAC), and a fully dynamic slot-scheduling system to prevent overbooking.

---

## ✨ Features

### 👤 Multi-Role Architecture
The system supports three user roles, each with a tailored dashboard:
- **Patients:** Can register, search for doctors by department/specialization, view available slots on a specific date, book appointments, and view their medical history and prescriptions.
- **Doctors:** Can view their daily schedule (filtered by date), accept or cancel appointment requests, and write/edit digital prescriptions.
- **Administrators:** Can monitor system metrics (active patients, doctor numbers, appointment states), list doctors, add new doctors with profile photos/specializations/availability schedules, and edit or delete existing doctors.

### 🔒 Security First
- **Zero Raw Passwords:** All passwords are salted and hashed with `bcrypt` before database storage.
- **Forms & CSRF Guardrails:** Every single form is fully guarded against CSRF attacks via `Flask-WTF`.
- **Role Enforcement:** Custom `@role_required` decorators block access to unauthorized pages and automatically handle session cleanup for malicious redirects.
- **No Overbooking:** The scheduling algorithm queries active, non-cancelled appointments in real-time before displaying open slots, making double-booking mathematically impossible.

### 🎨 Clean & Modern Design
- Built with custom CSS featuring curated HSL variables for instant transitions.
- Fully supports a beautiful **Light / Dark Mode** toggle that persists in local storage.
- Premium aesthetic using a calm, high-end healthcare color combo: **Pine Teal, Fresh Emerald Mint, and Soft Sage**.

---

## 📂 Project Structure

The project follows a clean, modular directory structure to separate concerns:

```
Hospital Appointment Booking System1/
├── app.py                  # App factory, error handlers, and initial database seeder
├── config.py               # Central environment configuration & secret key settings
├── database/
│   └── db.py               # Database engine initialization
├── models/                 # SQLAlchemy ORM database models
│   ├── user.py             # Unified credentials model (used for Patient/Doctor/Admin logins)
│   ├── patient.py          # Detailed patient records
│   ├── doctor.py           # Doctor specifications and availability schedules
│   ├── appointment.py      # Booking transactions and status trackers
│   └── prescription.py     # Medical prescriptions
├── routes/                 # Separated blueprints for each module
│   ├── auth.py             # Signup, secure login, logout, and RBAC utilities
│   ├── patient.py          # Doctor searches, calendar calculations, and booking APIs
│   ├── doctor.py           # Schedule lookups and prescription writers
│   └── admin.py            # System metrics and doctor management
├── static/                 # Custom CSS stylesheet and dark-mode script
│   ├── css/style.css       
│   └── js/app.js           
└── templates/              # HTML layout templates using Jinja2 inheritance
```

---

## ⚡ Quick Start

Get the application running locally in less than a minute.

### 1. Install Dependencies
Make sure you have Python 3.10+ installed. Then install the required packages:
```bash
pip install -r requirements.txt
```

### 2. Start the Server
Run the Flask application:
```bash
python app.py
```

### 3. Open MedBook
Open your browser and navigate to:
👉 **[http://localhost:5000](http://localhost:5000)**

---

## 🔑 Seeded Accounts (For Instant Testing)

On the first run, the database is automatically seeded with default credentials so you can start testing immediately:

### 🛠️ Administrator
- **Email:** `admin@hospital.com`
- **Password:** `Admin@123`

### 🥼 Doctor (Cardiology)
- **Email:** `dr.sharma@hospital.com`
- **Password:** `Doctor@123`

### 🤒 Patients
Patients can register themselves instantly via the **Register** link on the login page!

---

## 🧪 Integration Tests

We included a fully automated, dynamic integration test suite in `scratch/test_flow.py` that exercises the entire user journey:
1. **RBAC Check:** Blocks unauthenticated patient dashboard visits.
2. **Admin Flow:** Logs in as Admin and fetches the seeded doctor registry.
3. **Patient Registration:** Signs up a unique patient dynamically.
4. **Availability Calculation:** Fetches available slots, books an open appointment time, and verifies the slot is immediately removed from the availability list.
5. **Doctor Review:** Logs in as Doctor, checks the schedule, accepts the booking, and writes a prescription.
6. **Verification:** Logs back in as Patient to confirm the prescription is saved in history.

To run the integration tests while the Flask server is running:
```bash
python "scratch/test_flow.py"
```

---

*Made with 💚 for premium healthcare interfaces.*
