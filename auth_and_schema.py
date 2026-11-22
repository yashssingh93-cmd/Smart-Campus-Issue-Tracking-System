"""
Functionalities: Database Schema, SHA-256 Hashing, RBAC Decorators, Login/Register Routes
"""
import sqlite3
import hashlib
import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g

app = Flask(__name__)
app.secret_key = "campus_secret_key_2024"
DATABASE = os.path.join(os.path.dirname(__file__), "campus.db")

def get_db():
    if not hasattr(g, "_database"):
        g._database = sqlite3.connect(DATABASE)
        g._database.row_factory = sqlite3.Row
    return g._database

@app.teardown_appcontext
def close_connection(e):
    db = getattr(g, "_database", None)
    if db:
        db.close()

def query_db(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

def execute_db(sql, args=()):
    cur = get_db().execute(sql, args)
    get_db().commit()
    return cur.lastrowid

def hash_password(password):
    """SHA-256 password hashing for secure credential storage."""
    return hashlib.sha256(password.encode()).hexdigest()

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student',
    phone TEXT DEFAULT '',
    team TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    location TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Open',
    submitted_by INTEGER NOT NULL,
    assigned_team TEXT,
    assigned_technician INTEGER,
    sla_deadline TEXT NOT NULL,
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    FOREIGN KEY (submitted_by) REFERENCES users(id),
    FOREIGN KEY (assigned_technician) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (issue_id) REFERENCES issues(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id INTEGER NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (issue_id) REFERENCES issues(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""

# Role-Based Access Control Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("student_dashboard"))
        return f(*args, **kwargs)
    return decorated_function

def technician_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "technician":
            flash("Technician access required.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Authentication & Registration Routes
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        un = request.form.get("username", "").strip()
        pw = request.form.get("password", "")
        u = query_db("SELECT * FROM users WHERE username=? AND password=?", (un, hash_password(pw)), one=True)
        if u:
            session.update(user_id=u["id"], username=u["username"], role=u["role"])
            flash(f"Welcome back, {u['username']}!", "success")
            if u["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            elif u["role"] == "technician":
                return redirect(url_for("technician_dashboard"))
            return redirect(url_for("student_dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        un = request.form.get("username", "").strip()
        em = request.form.get("email", "").strip()
        pw = request.form.get("password", "")
        role = request.form.get("role", "student")
        if role not in ("student", "technician"):
            role = "student"
        phone = request.form.get("phone", "").strip()
        team = request.form.get("team", "").strip()

        if not (un and em and pw) or (role == "technician" and not phone):
            flash("All required fields must be filled.", "danger")
            return render_template("register.html")
        if query_db("SELECT id FROM users WHERE username=? OR email=?", (un, em), one=True):
            flash("Username or email already registered.", "danger")
            return render_template("register.html")

        execute_db(
            "INSERT INTO users (username, email, password, role, phone, team, created_at) VALUES (?,?,?,?,?,?,?)",
            (un, em, hash_password(pw), role, phone, team, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        flash(f"{'Technician' if role == 'technician' else 'Student'} account created! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))
