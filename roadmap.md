# ROADMAP.md

A detailed development roadmap for **DoseDash** — the Medical Supplies & Medication Tracker web app, designed for caregivers in a single elderly care facility. This structured plan uses task checkboxes for each phase, clarifying both core features and admin management to guide developers or agentic AI.

---

## Caregiver Workflow Overview

Caregivers interact with **DoseDash** through the following daily workflow:

1. **Login**: Caregiver signs in and lands on their personalized dashboard.
2. **Resident Selection**: Select a resident to view their medication schedule and supply levels.
3. **Review Notifications**: Check the in-app notifications page for any low-stock, missed, or overdue-dose alerts.
4. **Log Doses**: For each scheduled time (morning, midday, after meal, night), mark medication as **Taken** or **Missed**, optionally attaching a voice note.
5. **Acknowledge Alerts****: Snooze or mark alerts as read once addressed.
6. **Generate Reports****: At week’s end or on demand, access and download usage and stock reports per resident.
7. **Logout****: Securely end the session.

Key points:
- **Schedule Variability**: Each `InventoryItem` defines its own `schedule_times`, `frequency`, and `relation_to_meals`, ensuring correct prompts for morning, night, or post-meal doses.
- **Centralized Logs**: All interactions (dose logs, voice notes, scans) feed into `UsageLog` for audit and reporting.

---

## Phase 1: Project Setup & Core Models

### 1.1 Repository & Environment
- [] Clone `hack4impact/flask-base` repository
- [X] Set up Python virtual environment and install dependencies
- [X] Configure `.env` for:
  - Database URI
  - Mail server credentials
  - Redis URL
  - Twilio API keys

### 1.2 Database Models (SQLAlchemy)
- [X] Define `User` model with roles: `admin`, `caregiver`
- [X] Define `Resident` model (patients) linked to `User`
  - Fields: `name`, `date_of_birth`, **`photo_url`** (required for UI)
  - Resident records created only by **Admin** to preserve data integrity
- [X] Define `InventoryItem` model for medications & supplies
  - Include fields for scheduling:
    - `schedule_times`: list of times (e.g., '08:00', '20:00')
    - `frequency`: ENUM('daily','weekly','custom') to specify interval
    - `relation_to_meals`: ENUM('before_meal','with_meal','after_meal','independent')
- [X] Define `UsageLog` model, with optional `voice_note_url`, and `scheduled_time` to record the intended dose slot
- [X] Create initial database migrations

### 1.3 Authentication & Permissions Authentication & Permissions Authentication & Permissions
- [X] Implement Flask-Login with role-based access:
  - **Admin**: full CRUD on `Caregiver` accounts and `Resident` records
  - **Caregiver**: manage `InventoryItem`, `UsageLog`, view notifications
- [X] Protect all routes by roles

---

## Phase 2: CRUD & Core Caregiver Workflows

### 2.1 Admin & User Management
- [X] Blueprint: `admin`
  - Admin dashboard for:
    - Creating/editing/deleting `Caregiver` accounts
    - Creating/editing/deleting `Resident` profiles
    - Assigning caregivers to residents

### 2.2 Inventory Management
- [X] Blueprint: `inventory`
  - CRUD routes for `InventoryItem`
  - Fields: name, type, quantity, threshold, daily usage, expiration
  - **Scheduling fields**: input UI for `schedule_times`, `frequency` selector, `relation_to_meals` dropdown
  - Voice note attachments when creating/editing items

### 2.3 Usage Logging
- [X] Blueprint: `usage`
  - Routes for marking `Taken` or `Missed` per resident schedule
  - Upload voice note attachments per log entry
  - Record timestamp, caregiver notes, and update `InventoryItem.quantity`

---

## Phase 3: Notifications & Chatbot

### 3.1 In-App Notifications Page
- [X] Blueprint: `notifications`
  - Dashboard listing all alerts:
    - **Low-stock**: when `InventoryItem.quantity` < `threshold`
    - **Missed-dose**: when a scheduled dose is not logged within an hour window
    - **Overdue-dose**: if not taken after configurable grace period
  - Options to **mark as read**, **snooze**, or **acknowledge**

### 3.2 SMS Push Notifications (Twilio)
- [X] Integrate Twilio REST API
- [X] Send SMS alerts to caregivers for:
  - Low-stock notifications
  - Repeated missed or overdue doses
- [X] Provide opt-in/opt-out settings per caregiver

### 3.3 Chatbot for Caregivers (RAG with Gemini API)
- [X] Blueprint: `chatbot`
- [X] Build Retrieval-Augmented Generation flow using Gemini API:
  - Index `Resident`, `InventoryItem`, and recent `UsageLog` data into memory context
  - Support natural-language queries like:
    - "When did Ms. Perez last miss a dose?"
    - "What supplies are low for Mr. Lee?"
  - Return retrieved context with Gemini-generated summary
- [X] Implement a simple chat UI (AJAX or SSE)

---

## Phase 4: Alerts & Asynchronous Tasks

### 4.1 Background Job Setup
- [X] Configure Redis Queue for scheduling tasks
- [X] Schedule periodic jobs to:
  - Check `InventoryItem` thresholds hourly/daily
  - Identify missed/overdue doses
  - Queue in-app, email, and SMS alerts

### 4.2 Email & Voice Email Templates
- [X] Design and implement email templates:
  - **Low-stock summary**
  - **Missed/overdue dose summary**
  - **Weekly caregiver digest**
- [X] Use Flask-Mail for sending emails

### 4.3 Snooze & Acknowledge Support
- [X] Persist snooze actions with timestamps
- [X] Avoid duplicate alerts within snooze interval

---

## Phase 5: Reporting, Exports & Accessibility

### 5.1 Weekly & Ad-hoc Reports
- [x] Generate reports (HTML and PDF via WeasyPrint) covering:
  - Usage logs (taken/missed)
  - Current stock levels
  - Alerts history
- [x] Provide download links and email delivery options

### 5.2 Frontend Styling (Bootstrap/MUI Core)
- [x] Integrate Bootstrap or MUI for responsive layouts
- [x] Global layout: navbar, main pane (detail views)
- [X] Responsive grid for tablets and mobile devices used in rounds

### 5.3 Accessibility Enhancements
- [ ] Add ARIA attributes on interactive elements
- [ ] Ensure full keyboard navigation and focus management

---

## Phase 6: Testing, Documentation & Deployment

### 6.1 Automated Testing
- [ ] Write pytest unit tests for:
  - Models and role-based permissions
  - Usage logging logic and threshold checks
  - RAG chatbot retrieval functions
- [ ] Integration tests for login, CRUD flows, notifications

### 6.2 Documentation
- [ ] Update `README.md` with:
  - Setup instructions and environment variables
  - Role definitions and permissions
  - Usage guide with screenshots (admin, caregiver, chatbot)
- [ ] Generate API docs for all blueprints

### 6.3 Deployment
- [ ] Create Dockerfile & `docker-compose.yml`
- [ ] Configure and test on Heroku or AWS Elastic Beanstalk
- [ ] Set up CI/CD for automated testing & deployment

---

## Stretch Goals
- [ ] Voice-to-text transcription for voice note attachments