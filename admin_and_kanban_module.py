"""
MEMBER 3 DELIVERABLE:
Epic 3 - Admin Dashboard & Management (US-09, US-10, US-11, US-12, US-13)
Epic 6 - Kanban Board (US-21, US-22)
Includes: Admin KPI Metrics, Team/Technician Assignment, Priority Overrides, 3-Column Kanban, Async Status REST API
"""
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, session, jsonify, flash

# Route: Admin Management Center with KPI Metrics
def admin_dashboard():
    issues = query_db("SELECT * FROM issues ORDER BY created_at DESC")
    ratings = query_db("SELECT AVG(rating) as avg_r FROM feedback")
    avg_r = round(ratings[0]["avg_r"] or 0, 1) if ratings else 0.0
    logs = query_db("SELECT al.*, i.title, u.username as actor FROM activity_log al JOIN issues i ON al.issue_id=i.id JOIN users u ON al.user_id=u.id ORDER BY al.created_at DESC LIMIT 15")
    return render_template(
        "admin_dashboard.html",
        issues=issues,
        total=len(issues),
        open_c=sum(1 for i in issues if i["status"] == "Open"),
        prog_c=sum(1 for i in issues if i["status"] == "In Progress"),
        res_c=sum(1 for i in issues if i["status"] == "Resolved"),
        overdue_c=sum(1 for i in issues if is_overdue(i)),
        avg_rating=avg_r,
        recent_logs=logs
    )

# Route: Admin Ticket Routing & Priority Overrides
def admin_issue(issue_id):
    issue = query_db("SELECT * FROM issues WHERE id=?", (issue_id,), one=True)
    if not issue:
        flash("Issue not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        team = request.form.get("assigned_team")
        prio = request.form.get("priority")
        st = request.form.get("status")
        tech_id = request.form.get("assigned_technician") or None
        now, fmt = datetime.now(), "%Y-%m-%d %H:%M:%S"
        res_at = now.strftime(fmt) if (st == "Resolved" and issue["status"] != "Resolved") else None
        new_sla = issue["sla_deadline"]
        if prio != issue["priority"]:
            cr = datetime.strptime(issue["created_at"], fmt)
            new_sla = (cr + timedelta(hours=SLA_HOURS.get(prio, 72))).strftime(fmt)

        execute_db(
            "UPDATE issues SET assigned_team=?, priority=?, status=?, sla_deadline=?, resolved_at=COALESCE(?,resolved_at), assigned_technician=? WHERE id=?",
            (team, prio, st, new_sla, res_at, tech_id, issue_id)
        )
        changes = []
        if team != issue["assigned_team"]: changes.append(f"assigned to '{team}'")
        if prio != issue["priority"]: changes.append(f"priority → {prio}")
        if st != issue["status"]: changes.append(f"status → {st}")
        if str(tech_id) != str(issue["assigned_technician"]):
            tech = query_db("SELECT username FROM users WHERE id=?", (tech_id,), one=True) if tech_id else None
            changes.append(f"technician → {tech['username'] if tech else 'unassigned'}")

        log_activity(issue_id, session["user_id"], "Admin updated: " + (", ".join(changes) if changes else "reviewed issue"), now.strftime(fmt))
        flash("Issue updated successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    logs = query_db("SELECT al.*, u.username as actor FROM activity_log al JOIN users u ON al.user_id=u.id WHERE al.issue_id=? ORDER BY al.created_at DESC", (issue_id,))
    fb = query_db("SELECT * FROM feedback WHERE issue_id=?", (issue_id,), one=True)
    techs = query_db("SELECT id, username, phone, team FROM users WHERE role='technician' ORDER BY team, username")
    atech = query_db("SELECT * FROM users WHERE id=?", (issue["assigned_technician"],), one=True) if issue["assigned_technician"] else None
    return render_template("admin_issue.html", issue=issue, logs=logs, feedback=fb, overdue=is_overdue(issue), technicians=techs, assigned_tech=atech)

# Route: Interactive 3-Column Kanban Workflow Board
def kanban():
    cols = {
        st: query_db("SELECT i.*, u.username as reporter FROM issues i JOIN users u ON i.submitted_by=u.id WHERE i.status=? ORDER BY i.created_at DESC", (st,))
        for st in ("Open", "In Progress", "Resolved")
    }
    return render_template("kanban.html", open_issues=cols["Open"], prog_issues=cols["In Progress"], res_issues=cols["Resolved"])

# Route: Asynchronous REST API for Kanban Drag-and-Drop Status Transitions
def update_status(issue_id):
    if session["role"] not in ("admin", "technician"):
        return jsonify({"error": "Access denied"}), 403
    status = (request.get_json(silent=True) or {}).get("status", "").strip()
    if status not in ("Open", "In Progress", "Resolved"):
        return jsonify({"error": "Invalid status"}), 400

    issue = query_db("SELECT * FROM issues WHERE id=?", (issue_id,), one=True)
    if not issue:
        return jsonify({"error": "Issue not found"}), 404
    if session["role"] == "technician" and issue["assigned_technician"] != session["user_id"]:
        return jsonify({"error": "Not assigned to you"}), 403

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    res_at = now if (status == "Resolved" and issue["status"] != "Resolved") else None
    execute_db("UPDATE issues SET status=?, resolved_at=COALESCE(?,resolved_at) WHERE id=?", (status, res_at, issue_id))
    actor = "Technician" if session["role"] == "technician" else "Admin"
    log_activity(issue_id, session["user_id"], f"{actor} changed status to '{status}'", now)
    return jsonify({"success": True, "new_status": status, "issue_id": issue_id})
