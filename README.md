# Smart Campus Issue Tracking & Resolution System

A full-stack, lightweight campus facilities service desk application built with **Python 3, Flask, SQLite, and Tailwind CSS**. Designed and developed following an **Agile Scrum methodology** over a two-week sprint cycle by a 5-member engineering team.

---

## 👥 Team & Epic Ownership

The project scope is partitioned into **8 Epics** evenly distributed among our 5 team members:

| Team Member | Engineering Role | Assigned Epics | Key Deliverables |
| :--- | :--- | :--- | :--- |
| **Member 1** | Backend & Security Lead | **Epic 1**: User Authentication & Role Management | SQLite database schema, session management, SHA-256 password hashing, RBAC decorators (`@login_required`, `@admin_required`, `@technician_required`). |
| **Member 2** | Student Experience & SLA Lead | **Epic 2**: Student Issue Management<br>**Epic 5**: SLA Management | Complaint filing form, category & location picker, personal dashboard, 4-tier SLA calculation engine (`24h`, `48h`, `72h`, `120h`), overdue ticket detection. |
| **Member 3** | Admin & Workflow Lead | **Epic 3**: Admin Dashboard & Management<br>**Epic 6**: Kanban Board | Administrative KPI dashboard (aggregates, average ratings), maintenance team assignment, interactive 3-column drag-and-drop Kanban board with asynchronous REST API updates. |
| **Member 4** | Field Operations Lead | **Epic 4**: Technician Management<br>*(Co-owner on Epic 7)* | Technician portal ("My Tasks"), field work order execution, status progression (`Open` &rarr; `In Progress` &rarr; `Resolved`), maintenance staff roster & contact cards. |
| **Member 5** | QA, Analytics & Audit Lead | **Epic 7**: Feedback & Activity Tracking<br>**Epic 8**: Testing & Documentation | 5-star resolution rating system, feedback forms, audit log history, 30 automated unit test cases (`test_app.py`), and documentation. |

---

## 🗺️ Epics & User Stories Breakdown

### **Epic 1: User Authentication & Role Management**
* **Goal:** Provide secure account access and role-specific experiences.
* **Scope:** Student registration and login, role-based access for students, admins, and technicians, secure logout and session handling.
* **Related User Stories:** `US-01` (Student Registration), `US-02` (Technician Registration with Team & Phone), `US-03` (Session Login & Hashing), `US-04` (Role-based Navigation & Route Guards).

### **Epic 2: Student Issue Management**
* **Goal:** Allow students to report campus issues and follow their resolution.
* **Scope:** Submit issues with title, description, category, location, and priority; view submitted issues and issue details/status.
* **Related User Stories:** `US-05` (Submit Issue Form), `US-06` (Category & Location Validation), `US-07` (Student Personal Issue Tracker), `US-08` (View Ticket Details & Assigned Staff).

### **Epic 3: Admin Dashboard & Management**
* **Goal:** Give admins visibility and control over campus maintenance requests.
* **Scope:** View and monitor all campus issues; assign maintenance teams and technicians; update issue priority; view dashboard statistics.
* **Related User Stories:** `US-09` (Campus KPI Metrics & Summary Cards), `US-10` (Master Issue Table), `US-11` (Maintenance Team Routing), `US-12` (Dynamic Technician Assignment), `US-13` (Priority & Deadline Override).

### **Epic 4: Technician Management**
* **Goal:** Help technicians manage and resolve their assigned work orders.
* **Scope:** View assigned work orders; view issue and reporter details where permitted; update issue status; review issue activity history.
* **Related User Stories:** `US-14` (Technician Task Workspace), `US-15` (Direct Student Contact Information), `US-16` (Task Status Progression), `US-17` (Staff Directory & Capacity Monitoring).

### **Epic 5: SLA Management**
* **Goal:** Track expected resolution times and highlight SLA breaches.
* **Scope:** Priority-based SLA targets (Critical: 24h, High: 48h, Medium: 72h, Low: 120h); calculate and update issue deadlines; identify overdue unresolved issues.
* **Related User Stories:** `US-18` (Auto-SLA Calculation Engine), `US-19` (Client-side Live SLA Preview), `US-20` (Overdue Badge & Breach Alerting).

### **Epic 6: Kanban Board**
* **Goal:** Make issue workflow progress visible through a status-based Kanban board.
* **Scope:** Display Open, In Progress, and Resolved columns; show issue cards in correct status column; move issues between statuses and persist updates.
* **Related User Stories:** `US-21` (Interactive 3-Column HTML5 Drag-and-Drop Board), `US-22` (Asynchronous Status Update API Endpoint).

### **Epic 7: Feedback & Activity Tracking**
* **Goal:** Capture service quality feedback and maintain traceability of issue changes.
* **Scope:** Record important issue actions with actor and timestamp; display activity history; collect student ratings/comments after resolution; show feedback information to admins.
* **Related User Stories:** `US-23` (Post-Resolution 5-Star Rating & Comment Form), `US-24` (Real-Time Activity Audit Trail).

### **Epic 8: Testing & Documentation**
* **Goal:** Verify core workflows and provide clear handover documentation.
* **Scope:** Test authentication and role access; test issue lifecycle, SLA, and feedback workflows; document setup, architecture, database, and test outcomes.
* **Related User Stories:** `US-25` (Auth & Permission Unit Tests), `US-26` (SLA & Issue Lifecycle Tests), `US-27` (Kanban API & Status Transition Tests), `US-28` (Feedback & Security Verification).

---

## 📅 Two-Week Agile Scrum Timeline

```
Week 1 (Sprint 1): Foundation, Core Architecture & Filing
├── Day 1-2: Epic 1 & Database setup (SQLite schema, connection pooling, seed script)
├── Day 3-4: Epic 1 & Epic 2 (User registration, login sessions, complaint submission form)
└── Day 5-7: Epic 2 & Epic 5 (Category/Location validation, dynamic SLA calculation & preview)

Week 2 (Sprint 2): Administration, Field Operations, Workflow & QA
├── Day 8-9:   Epic 3 & Epic 4 (Admin KPI dashboard, technician assignment, work order view)
├── Day 10-11: Epic 6 (Kanban drag-and-drop board & asynchronous JSON status API)
├── Day 12:    Epic 7 (Resolution feedback system, star ratings, activity logs)
└── Day 13-14: Epic 8 (Automated test suite with 30 unit tests, code cleanup, documentation)
```

---

## 🏗️ Architecture & Database Design

The application follows an **MVC (Model-View-Controller)** pattern with zero heavy external frameworks:
* **Backend:** Python 3 + Flask (`app.py`)
* **Database:** SQLite (`campus.db`) with 4 relational tables:
  * `users` &rarr; User accounts, hashed passwords, roles (`student`, `admin`, `technician`), phone, team.
  * `issues` &rarr; Ticket records, location, priority, status, assigned technician, SLA target.
  * `activity_log` &rarr; Audit history of transitions, assignments, and user actions.
  * `feedback` &rarr; Post-resolution student ratings (1–5 stars) and comments.
* **Frontend:** Jinja2 templates styled with Tailwind CSS (via CDN) and Vanilla JavaScript.

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.8 or higher installed on your system.

### 2. Installation
Clone the repository and install the sole dependency:
```bash
git clone https://github.com/<your-username>/smart-campus-tracker.git
cd smart-campus-tracker
pip install -r requirements.txt
```

### 3. Running the Server
```bash
python app.py
```
Open **`http://127.0.0.1:5000`** in your browser.

### 4. Pre-Seeded Demonstration Accounts

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Dashboard KPIs, staff assignment, Kanban board |
| **Student** | `alice` | `alice123` | Submit issues, live SLA calculation preview |
| **Student** | `bob` | `bob123` | Has a resolved ticket to test 5-star resolution rating |
| **Technician** | `rajesh` | `rajesh123` | IT & Network team work orders |
| **Technician** | `priya` | `priya123` | Electrical & AC team work orders |

---

## 🧪 Automated Testing

Run the built-in test suite to execute all **30 unit tests**:
```bash
python test_app.py
```

Expected output:
```text
Ran 30 tests in 0.450s

OK
```
Tests cover user authentication, role restrictions, SLA calculations, status state-machine transitions, and feedback submission constraints.
