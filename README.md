# St Francis Mercy Community Center — LMS

A Learning Management System for **St Francis Mercy Community Center**,
Kiptere, Kericho. Built with Flask + PostgreSQL.

---

## Features

- **Public portal** — course listing, course detail, registration
- **Student portal** — dashboard, browse & enrol, payment history, profile
- **Admin/Instructor portal** — full CRUD for users, courses, enrollments, payments, announcements, categories
- **Security** — CSRF protection on all forms, bcrypt password hashing, audit log, account activation control
- **M-Pesa ready** — payment records UI in place; Daraja API integration to be added
- **PostgreSQL** backend with Flask-Migrate for schema versioning

---

## Project Structure

```
sfmcc_lms/
├── app.py              # Entry point & CLI commands
├── __init__.py         # App factory
├── config.py           # Config classes (dev / prod)
├── models.py           # SQLAlchemy models
├── forms.py            # WTForms form definitions
├── utils.py            # Decorators & helpers
├── routes/
│   ├── auth.py         # Login, register, change password
│   ├── main.py         # Public pages
│   ├── admin.py        # Admin & instructor routes
│   └── student.py      # Student portal routes
├── templates/
│   ├── base.html
│   ├── layout_app.html   # Sidebar layout (app pages)
│   ├── layout_public.html
│   ├── auth/
│   ├── main/
│   ├── admin/
│   ├── student/
│   ├── errors/
│   └── partials/
├── static/
│   ├── css/main.css
│   └── js/main.js
├── requirements.txt
└── .env.example
```

---

## Setup

### 1. Prerequisites

- Python 3.10+
- PostgreSQL 14+

### 2. Clone & create virtual environment

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — set SECRET_KEY and DATABASE_URL
```

### 4. Create PostgreSQL database

```sql
CREATE DATABASE sfmcc_lms;
CREATE USER sfmcc_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE sfmcc_lms TO sfmcc_user;
```

Update `DATABASE_URL` in `.env` accordingly.

### 5. Initialise & seed database

```bash
flask db init
flask db migrate -m "initial"
flask db upgrade
flask seed
```

The `seed` command creates:
- Admin account: `admin@sfmcc.ac.ke` / `Admin@1234`
- 6 course categories
- 8 sample courses

**Change the admin password immediately after first login.**

### 6. Run development server

```bash
flask run
# Visit http://127.0.0.1:5000
```

---

## Production Deployment

```bash
# Set in .env
FLASK_ENV=production
SECRET_KEY=<long-random-string>
SESSION_COOKIE_SECURE=True   # requires HTTPS

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:app"
```

Put Nginx in front of Gunicorn and enable SSL (Let's Encrypt).

---

## User Roles

| Role       | Access                                              |
|------------|-----------------------------------------------------|
| Admin      | Full access — users, courses, payments, audit log   |
| Instructor | Courses, enrollments, announcements (read/create)   |
| Student    | Browse courses, enrol, view own payments & profile  |

---

## Security Notes

- All forms are CSRF-protected via Flask-WTF
- Passwords hashed with Werkzeug (bcrypt-compatible)
- `SESSION_COOKIE_HTTPONLY = True`, `SAMESITE = Lax`
- `SESSION_COOKIE_SECURE = True` in production (requires HTTPS)
- Audit log records every significant action with IP address
- Role-based access enforced with decorators on every route

---

## Adding M-Pesa (Daraja) — Future Step

The payment recording UI is ready. To add Daraja:
1. Create `routes/mpesa.py` with STK Push and callback handlers
2. Register the blueprint in `__init__.py`
3. Add `MPESA_*` keys to `.env` and `config.py`
4. Update `student/payments.html` to show the Pay Now button

---

## School Details

| Field    | Value                              |
|----------|------------------------------------|
| Name     | St Francis Mercy Community Center  |
| Location | Kiptere, Kericho County, Kenya     |
| Email    | info@sfmcc.ac.ke                   |
| Phone    | +254 700 000 000                   |

Update `config.py` with the real phone and email before going live.
