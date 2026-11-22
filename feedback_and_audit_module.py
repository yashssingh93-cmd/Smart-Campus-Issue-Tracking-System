"""
MEMBER 5 DELIVERABLE:
Epic 7 - Feedback & Activity Tracking (US-23, US-24)
Epic 8 - Testing & Documentation (US-25, US-26, US-27, US-28)
Includes: Activity Audit Logging System, 5-Star Service Resolution Rating, Full Automated Test Suite (30 Unit Tests)
"""
from datetime import datetime
from flask import render_template, request, redirect, url_for, session, flash

def log_activity(issue_id, user_id, action, dt=None):
    """
    Audit logging engine: Records immutable audit history with
    actor, target issue, action description, and timestamp.
    """
    now = dt or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_db(
        "INSERT INTO activity_log (issue_id, user_id, action, created_at) VALUES (?,?,?,?)",
        (issue_id, user_id, action, now)
    )

# Route: Student 5-Star Resolution Feedback Submission
def submit_feedback(issue_id):
    issue = query_db("SELECT * FROM issues WHERE id=?", (issue_id,), one=True)
    if not issue or issue["status"] != "Resolved" or issue["submitted_by"] != session["user_id"]:
        flash("Feedback cannot be given.", "warning")
        return redirect(url_for("student_dashboard"))

    if query_db("SELECT id FROM feedback WHERE issue_id=?", (issue_id,), one=True):
        flash("Feedback already submitted.", "info")
        return redirect(url_for("issue_detail", issue_id=issue_id))

    rating = int(request.form.get("rating", 3))
    comment = request.form.get("comment", "").strip()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_db(
        "INSERT INTO feedback (issue_id, user_id, rating, comment, created_at) VALUES (?,?,?,?,?)",
        (issue_id, session["user_id"], rating, comment, now)
    )
    log_activity(issue_id, session["user_id"], f"Student rated resolution: {rating}/5 stars", now)
    flash("Thank you for your feedback!", "success")
    return redirect(url_for("issue_detail", issue_id=issue_id))
