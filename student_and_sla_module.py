"""
MEMBER 2 DELIVERABLE:
Epic 2 - Student Issue Management (US-05, US-06, US-07, US-08)
Epic 5 - SLA Management (US-18, US-19, US-20)
Includes: SLA Policy Engine, Deadline Calculation, Overdue Detection, Student Routes
"""
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, session, flash

# 4-Tier SLA Policy (in hours)
SLA_HOURS = {
    "Critical": 24,
    "High": 48,
    "Medium": 72,
    "Low": 120
}

def is_overdue(issue):
    """Detects if an unresolved issue has passed its SLA target deadline."""
    if issue["status"] == "Resolved":
        return False
    try:
        return datetime.now() > datetime.strptime(issue["sla_deadline"], "%Y-%m-%d %H:%M:%S")
    except:
        return False

# Route: Student Personal Dashboard
def student_dashboard():
    uid = session["user_id"]
    issues = query_db("SELECT * FROM issues WHERE submitted_by=? ORDER BY created_at DESC", (uid,))
    notifications = query_db(
        "SELECT al.*, i.title, u.username as actor FROM activity_log al JOIN issues i ON al.issue_id=i.id JOIN users u ON al.user_id=u.id WHERE i.submitted_by=? ORDER BY al.created_at DESC LIMIT 10",
        (uid,)
    )
    return render_template(
        "student_dashboard.html",
        issues=issues,
        total=len(issues),
        open_c=sum(1 for i in issues if i["status"] == "Open"),
        prog_c=sum(1 for i in issues if i["status"] == "In Progress"),
        res_c=sum(1 for i in issues if i["status"] == "Resolved"),
        overdue_c=sum(1 for i in issues if is_overdue(i)),
        notifications=notifications
    )

# Route: Submit New Campus Issue with Auto-SLA Calculation
def submit_issue():
    if request.method == "POST":
        t = request.form.get("title", "").strip()
        desc = request.form.get("description", "").strip()
        cat = request.form.get("category", "")
        loc = request.form.get("location", "").strip()
        prio = request.form.get("priority", "Medium")

        if not (t and desc and cat and loc):
            flash("All fields are required.", "danger")
            return render_template("submit_issue.html")

        now = datetime.now()
        # Compute SLA target deadline based on priority tier
        dl = now + timedelta(hours=SLA_HOURS.get(prio, 72))
        fmt = "%Y-%m-%d %H:%M:%S"
        iid = execute_db(
            "INSERT INTO issues (title, description, category, location, priority, status, submitted_by, sla_deadline, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (t, desc, cat, loc, prio, "Open", session["user_id"], dl.strftime(fmt), now.strftime(fmt))
        )
        log_activity(iid, session["user_id"], "Issue submitted by student", now.strftime(fmt))
        flash("Issue submitted successfully!", "success")
        return redirect(url_for("student_dashboard"))
    return render_template("submit_issue.html")

# Route: Detailed Issue View for Student
def issue_detail(issue_id):
    issue = query_db("SELECT * FROM issues WHERE id=?", (issue_id,), one=True)
    if not issue or (session["role"] == "student" and issue["submitted_by"] != session["user_id"]):
        flash("Access denied or issue not found.", "danger")
        return redirect(url_for("student_dashboard"))

    logs = query_db("SELECT al.*, u.username as actor FROM activity_log al JOIN users u ON al.user_id=u.id WHERE al.issue_id=? ORDER BY al.created_at DESC", (issue_id,))
    fb = query_db("SELECT * FROM feedback WHERE issue_id=?", (issue_id,), one=True)
    tech = query_db("SELECT username, email, phone, team FROM users WHERE id=?", (issue["assigned_technician"],), one=True) if issue["assigned_technician"] else None
    return render_template("issue_detail.html", issue=issue, logs=logs, feedback=fb, overdue=is_overdue(issue), technician=tech)
