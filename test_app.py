"""test_app.py – Smart Campus Issue Tracker Unit Tests (Sprint 4 Testing)"""
import unittest, json, os, tempfile
from datetime import datetime
from app import app, init_db, DATABASE, hash_password, execute_db, query_db, SLA_HOURS

class SmartCampusTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        app.config.update(TESTING=True, SECRET_KEY="test_secret")
        import app as m; m.DATABASE = self.db_path
        self.client = app.test_client()
        with app.app_context(): init_db()

    def tearDown(self):
        import app as m; m.DATABASE = os.path.join(os.path.dirname(__file__), "campus.db")
        os.close(self.db_fd); os.unlink(self.db_path)

    def login(self, u, p):
        return self.client.post("/login", data={"username": u, "password": p}, follow_redirects=True)

    def logout(self):
        return self.client.get("/logout", follow_redirects=True)

    def register(self, u, e, p):
        return self.client.post("/register", data={"username": u, "email": e, "password": p}, follow_redirects=True)

class TestAuthentication(SmartCampusTestCase):
    def test_01_login_page_loads(self):
        resp = self.client.get("/login")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Sign In", resp.data)

    def test_02_admin_login_success(self):
        resp = self.login("admin", "admin123")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Dashboard", resp.data)

    def test_03_student_login_success(self):
        resp = self.login("alice", "alice123")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Dashboard", resp.data)

    def test_04_login_wrong_password(self):
        self.assertIn(b"Invalid username or password", self.login("alice", "wrongpassword").data)

    def test_05_login_nonexistent_user(self):
        self.assertIn(b"Invalid username or password", self.login("ghost_user", "pass123").data)

    def test_06_register_new_student(self):
        resp = self.register("charlie", "charlie@campus.edu", "charlie123")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"account created", resp.data.lower())

    def test_07_register_duplicate_username(self):
        self.register("dave", "dave@campus.edu", "dave123")
        self.assertIn(b"already registered", self.register("dave", "dave2@campus.edu", "dave123").data)

    def test_08_logout(self):
        self.login("alice", "alice123")
        self.assertIn(b"Sign In", self.logout().data)

    def test_09_protected_route_requires_login(self):
        self.assertIn(b"Sign In", self.client.get("/student/dashboard", follow_redirects=True).data)

    def test_10_admin_route_requires_admin(self):
        self.login("alice", "alice123")
        self.assertNotIn(b"All Campus Issues", self.client.get("/admin/dashboard", follow_redirects=True).data)

class TestIssueSubmission(SmartCampusTestCase):
    def test_11_submit_issue_form_loads(self):
        self.login("alice", "alice123")
        resp = self.client.get("/student/submit")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Report a Campus Issue", resp.data)

    def test_12_submit_valid_issue(self):
        self.login("alice", "alice123")
        resp = self.client.post("/student/submit", data={
            "title": "Broken AC in Room 101", "description": "AC stopped working.",
            "category": "Classroom Maintenance", "location": "Block A Room 101", "priority": "High"
        }, follow_redirects=True)
        self.assertIn(b"Issue submitted successfully", resp.data)

    def test_13_sla_deadline_calculated_correctly(self):
        self.login("alice", "alice123")
        self.client.post("/student/submit", data={
            "title": "Critical Network Failure", "description": "Core switch down.",
            "category": "Wi-Fi / Network", "location": "Server Room", "priority": "Critical"
        })
        with app.app_context():
            issue = query_db("SELECT * FROM issues WHERE title='Critical Network Failure'", one=True)
        self.assertIsNotNone(issue)
        cr = datetime.strptime(issue["created_at"], "%Y-%m-%d %H:%M:%S")
        dl = datetime.strptime(issue["sla_deadline"], "%Y-%m-%d %H:%M:%S")
        self.assertAlmostEqual((dl - cr).total_seconds() / 3600, SLA_HOURS["Critical"], delta=0.1)

    def test_14_submit_issue_missing_fields(self):
        self.login("alice", "alice123")
        resp = self.client.post("/student/submit", data={"title": "", "description": "Desc", "category": "Hostel Complaints", "location": "H3-210", "priority": "Low"}, follow_redirects=True)
        self.assertNotIn(b"submitted successfully", resp.data)

    def test_15_all_sla_hours_mapping(self):
        for p, h in [("Critical", 24), ("High", 48), ("Medium", 72), ("Low", 120)]:
            self.assertEqual(SLA_HOURS[p], h)

class TestAdminFeatures(SmartCampusTestCase):
    def _get_first_issue_id(self):
        with app.app_context(): return query_db("SELECT id FROM issues LIMIT 1", one=True)["id"]

    def test_16_admin_dashboard_loads(self):
        self.login("admin", "admin123")
        resp = self.client.get("/admin/dashboard")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"All Campus Issues", resp.data)

    def test_17_admin_can_assign_team(self):
        self.login("admin", "admin123")
        iid = self._get_first_issue_id()
        resp = self.client.post(f"/admin/issue/{iid}", data={"assigned_team": "IT & Network Team", "priority": "High", "status": "In Progress"}, follow_redirects=True)
        self.assertIn(b"updated successfully", resp.data)
        with app.app_context():
            self.assertEqual(query_db("SELECT assigned_team FROM issues WHERE id=?", (iid,), one=True)["assigned_team"], "IT & Network Team")

    def test_18_admin_can_override_priority(self):
        self.login("admin", "admin123")
        iid = self._get_first_issue_id()
        self.client.post(f"/admin/issue/{iid}", data={"assigned_team": "Lab Support Team", "priority": "Critical", "status": "Open"}, follow_redirects=True)
        with app.app_context():
            self.assertEqual(query_db("SELECT priority FROM issues WHERE id=?", (iid,), one=True)["priority"], "Critical")

class TestStatusTransitions(SmartCampusTestCase):
    def _get_issue_id(self):
        with app.app_context(): return query_db("SELECT id FROM issues LIMIT 1", one=True)["id"]

    def test_19_kanban_board_loads(self):
        self.login("admin", "admin123")
        resp = self.client.get("/admin/kanban")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Kanban Board", resp.data)

    def test_20_api_status_update_to_in_progress(self):
        self.login("admin", "admin123")
        iid = self._get_issue_id()
        resp = self.client.post(f"/api/issue/{iid}/status", data=json.dumps({"status": "In Progress"}), content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(json.loads(resp.data)["success"])

    def test_21_api_status_update_to_resolved(self):
        self.login("admin", "admin123")
        iid = self._get_issue_id()
        resp = self.client.post(f"/api/issue/{iid}/status", data=json.dumps({"status": "Resolved"}), content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        with app.app_context():
            self.assertIsNotNone(query_db("SELECT resolved_at FROM issues WHERE id=?", (iid,), one=True)["resolved_at"])

    def test_22_api_invalid_status_rejected(self):
        self.login("admin", "admin123")
        resp = self.client.post(f"/api/issue/{self._get_issue_id()}/status", data=json.dumps({"status": "Invalid"}), content_type="application/json")
        self.assertEqual(resp.status_code, 400)

    def test_23_status_cycle_open_to_resolved(self):
        self.login("admin", "admin123")
        iid = self._get_issue_id()
        for s in ["In Progress", "Resolved"]:
            self.client.post(f"/api/issue/{iid}/status", data=json.dumps({"status": s}), content_type="application/json")
        with app.app_context():
            self.assertEqual(query_db("SELECT status FROM issues WHERE id=?", (iid,), one=True)["status"], "Resolved")

    def test_24_activity_log_recorded_on_status_change(self):
        self.login("admin", "admin123")
        iid = self._get_issue_id()
        with app.app_context():
            b = query_db("SELECT COUNT(*) as c FROM activity_log WHERE issue_id=?", (iid,), one=True)["c"]
        self.client.post(f"/api/issue/{iid}/status", data=json.dumps({"status": "In Progress"}), content_type="application/json")
        with app.app_context():
            a = query_db("SELECT COUNT(*) as c FROM activity_log WHERE issue_id=?", (iid,), one=True)["c"]
        self.assertGreater(a, b)

class TestFeedback(SmartCampusTestCase):
    def _resolve_bobs_issue(self):
        with app.app_context():
            iss = query_db("SELECT i.id FROM issues i JOIN users u ON i.submitted_by=u.id WHERE u.username='bob' LIMIT 1", one=True)
        if not iss: return None
        iid = iss["id"]
        self.login("admin", "admin123")
        self.client.post(f"/api/issue/{iid}/status", data=json.dumps({"status": "Resolved"}), content_type="application/json")
        self.logout()
        return iid

    def test_25_feedback_form_visible_after_resolve(self):
        iid = self._resolve_bobs_issue()
        self.login("bob", "bob123")
        self.assertIn(b"Rate the Resolution", self.client.get(f"/student/issue/{iid}").data)

    def test_26_submit_feedback_success(self):
        iid = self._resolve_bobs_issue()
        self.login("bob", "bob123")
        resp = self.client.post(f"/student/feedback/{iid}", data={"rating": "5", "comment": "Great!"}, follow_redirects=True)
        self.assertIn(b"Thank you for your feedback", resp.data)

    def test_27_feedback_stored_in_db(self):
        iid = self._resolve_bobs_issue()
        self.login("bob", "bob123")
        self.client.post(f"/student/feedback/{iid}", data={"rating": "4", "comment": "Good job."})
        with app.app_context():
            fb = query_db("SELECT * FROM feedback WHERE issue_id=?", (iid,), one=True)
        self.assertEqual(fb["rating"], 4)
        self.assertEqual(fb["comment"], "Good job.")

    def test_28_duplicate_feedback_rejected(self):
        iid = self._resolve_bobs_issue()
        self.login("bob", "bob123")
        self.client.post(f"/student/feedback/{iid}", data={"rating": "3", "comment": "OK."})
        resp = self.client.post(f"/student/feedback/{iid}", data={"rating": "5", "comment": "Again."}, follow_redirects=True)
        self.assertIn(b"already submitted", resp.data)

    def test_29_feedback_not_allowed_for_open_issues(self):
        with app.app_context(): iid = query_db("SELECT id FROM issues WHERE status='Open' LIMIT 1", one=True)["id"]
        self.login("alice", "alice123")
        resp = self.client.post(f"/student/feedback/{iid}", data={"rating": "5", "comment": "OK."}, follow_redirects=True)
        self.assertNotIn(b"Thank you for your feedback", resp.data)

    def test_30_password_hashing_deterministic(self):
        self.assertEqual(hash_password("test"), hash_password("test"))
        self.assertNotEqual(hash_password("test"), hash_password("other"))
        self.assertEqual(len(hash_password("test")), 64)

if __name__ == "__main__":
    unittest.main(verbosity=2)
