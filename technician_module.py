"""
MEMBER 4 DELIVERABLE:
Epic 4 - Technician Management (US-14, US-15, US-16, US-17)
Includes: Technician Task Workspace ("My Tasks"), Direct Student Contact Channel, Status Progression, Staff Capacity Roster
"""
from datetime import datetime
from flask import render_template, request, redirect, url_for, session, flash

# Route: Admin Technician Roster with Aggregated Capacity
def admin_technicians():
    techs = query_db("""
        SELECT u.*, COUNT(i.id) AS total_assigned,
               SUM(CASE WHEN i.status='Resolved' THEN 1 ELSE 0 END) AS resolved_count,
               SUM(CASE WHEN i.status='In Progress' THEN 1 ELSE 0 END) AS inprog_count,
               SUM(CASE WHEN i.status='Open' THEN 1 ELSE 0 END) AS open_count
        FROM users u LEFT JOIN issues i ON i.assigned_technician=u.id
        WHERE u.role='technician' GROUP BY u.id ORDER BY u.team, u.username
    """)
    return render_template("admin_technicians.html", technicians=techs)

# Route: Technician Personal Portal ("My Tasks")
def technician_dashboard():
    uid = session["user_id"]
    prof = query_db("SELECT * FROM users WHERE id=?", (uid,), one=True)
    issues = query_db("SELECT i.*, u.username AS reporter FROM issues i JOIN users u ON i.submitted_by=u.id WHERE i.assigned_technician=? ORDER BY i.created_at DESC", (uid,))
    logs = query_db("SELECT al.*, i.title, u.username as actor FROM activity_log al JOIN issues i ON al.issue_id=i.id JOIN users u ON al.user_id=u.id WHERE i.assigned_technician=? ORDER BY al.created_at DESC LIMIT 10", (uid,))
    return render_template(
        "technician_dashboard.html",
        tech=prof,
        issues=issues,
        total=len(issues),
        open_c=sum(1 for i in issues if i["status"] == "Open"),
        prog_c=sum(1 for i in issues if i["status"] == "In Progress"),
        res_c=sum(1 for i in issues if i["status"] == "Resolved"),
        recent_logs=logs
    )

# Route: Work Order Details with Student Contact Details
def technician_issue_detail(issue_id):
    issue = query_db("SELECT * FROM issues WHERE id=? AND assigned_technician=?", (issue_id, session["user_id"]), one=True)
    if not issue:
        flash("Task not found or not assigned to you.", "danger")
        return redirect(url_for("technician_dashboard"))
    logs = query_db("SELECT al.*, u.username as actor FROM activity_log al JOIN users u ON al.user_id=u.id WHERE al.issue_id=? ORDER BY al.created_at DESC", (issue_id,))
    rep = query_db("SELECT username, email FROM users WHERE id=?", (issue["submitted_by"],), one=True)
    fb = query_db("SELECT * FROM feedback WHERE issue_id=?", (issue_id,), one=True)
    return render_template("technician_issue.html", issue=issue, logs=logs, reporter=rep, feedback=fb, overdue=is_overdue(issue))

# Route: Work Order Status Progression (Open -> In Progress -> Resolved)
def technician_update_status(issue_id):
    issue = query_db("SELECT * FROM issues WHERE id=? AND assigned_technician=?", (issue_id, session["user_id"]), one=True)
    if not issue:
        flash("Task not found or not assigned to you.", "danger")
        return redirect(url_for("technician_dashboard"))
    st = request.form.get("status", "").strip()
    if st not in ("Open", "In Progress", "Resolved"):
        flash("Invalid status.", "danger")
        return redirect(url_for("technician_issue_detail", issue_id=issue_id))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    res_at = now if (st == "Resolved" and issue["status"] != "Resolved") else None
    execute_db("UPDATE issues SET status=?, resolved_at=COALESCE(?,resolved_at) WHERE id=?", (st, res_at, issue_id))
    log_activity(issue_id, session["user_id"], f"Technician updated status to '{st}'", now)
    flash(f"Status updated to '{st}'.", "success")
    return redirect(url_for("technician_issue_detail", issue_id=issue_id))
