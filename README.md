# 🧪 LabNexa

A modern, role-based **Laboratory Equipment Management System** built using **Flask** and **MySQL**. LabNexa streamlines laboratory equipment booking, approval workflows, inventory management, analytics, and PDF report generation through a clean and responsive web interface.

---

# 📌 Overview

LabNexa is a full-stack web application developed to simplify the management of laboratory equipment in educational institutions.

The system provides separate dashboards and permissions for **Students**, **Faculty**, and **Administrators**, ensuring secure and organized management of laboratory resources.

---

# 🌟 Project Highlights

- 🔐 Secure Authentication with Password Hashing
- 👥 Role-Based Access Control
- 📦 Equipment Management (CRUD)
- 👤 User Management (CRUD)
- 🔍 Equipment Search & Smart Filters
- 📊 Interactive Booking Analytics Dashboard
- 📄 Downloadable PDF Reports
- 📱 Responsive User Interface
- 🛡️ Session-Based Authentication

---

# ✨ Features

## 👨‍🎓 Student Module

- Secure Registration & Login
- Browse Available Equipment
- Search Equipment
- Filter by Category
- Filter by Availability
- Book Laboratory Equipment
- View Booking History
- Track Booking Status

---

## 👨‍🏫 Faculty Module

- Secure Login
- View Equipment Requests
- Approve Booking Requests
- Reject Booking Requests

---

## 👨‍💼 Admin Module

- Admin Dashboard
- Equipment Management (CRUD)
- User Management (CRUD)
- Inventory Management
- View System Reports
- Booking Analytics Dashboard
- Generate PDF Reports

---

# 🔐 Security Features

- Password Hashing using Werkzeug
- Session-Based Authentication
- Role-Based Access Control
- Protected Routes
- Secure Login System

---

# 🛠️ Technology Stack

| Category | Technology |
|----------|------------|
| Backend | Python, Flask |
| Frontend | HTML5, CSS3, Bootstrap 5 |
| Database | MySQL |
| Template Engine | Jinja2 |
| Charts | Chart.js |
| PDF Generation | ReportLab |
| Version Control | Git & GitHub |

---

# 📂 Project Structure

```text
LabNexa
│
├── static
│   ├── css
│   ├── images
│   ├── screenshots
│
├── templates
│
├── app.py
├── schema.sql
├── requirements.txt
├── .gitignore
└── README.md
```

---

# 📸 Application Screenshots

## 🏠 Homepage

![Homepage](screenshots/home_page.png)

---

## 👨‍🎓 Student Dashboard

![Student Dashboard](screenshots/student_dashboard.png)

---

## 👨‍🏫 Faculty Dashboard

![Faculty Dashboard](screenshots/faculty_dashboard.png)

---

## 👨‍💼 Admin Dashboard

![Admin Dashboard](screenshots/admin_dashboard.png)

---

## 📦 Equipment Management

![Equipment Management](screenshots/manage_equipment.png)

---

## 👥 User Management

![User Management](screenshots/manage_users.png)

---

## 🔍 Equipment Search & Filters

![Equipment Search](screenshots/equipment_search_filter.png)

---

## 📊 Reports Dashboard

![Reports Dashboard](screenshots/reports_dashboard.png)

---

## 📈 Booking Analytics Dashboard

![Booking Analytics](screenshots/booking_analytics_chart.png)

---

## 📄 PDF Report Generation

![PDF Report](screenshots/pdf_report.png)

---

# 👥 User Roles

| Role | Responsibilities |
|------|------------------|
| Student | Register, Login, Search Equipment, Book Equipment, View Booking History |
| Faculty | View Requests, Approve Bookings, Reject Bookings |
| Administrator | Manage Users, Equipment, Inventory, Reports & Analytics |

---

# 🚀 Installation

### Clone the repository

```bash
git clone https://github.com/yashnandwani202-ops/labnexa.git
```

### Navigate to the project

```bash
cd labnexa
```

### Create a virtual environment

```bash
python -m venv venv
```

### Activate the virtual environment

**Windows**

```bash
venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Import the database

Import the `schema.sql` file into MySQL.

### Run the application

```bash
python app.py
```

### Open in your browser

```text
http://127.0.0.1:5000
```

---

# 🔮 Future Enhancements

- QR Code Based Equipment Checkout
- Email Notifications
- Equipment Image Upload
- Equipment Maintenance Module
- Equipment Reservation Calendar
- REST API for Mobile Application
- Automatic Database Backup

---

# 👨‍💻 Developer

**Yash Nandwani**

B.Tech Electronics & Computer Engineering (ECM)

GitHub: https://github.com/yashnandwani202-ops

---

# ⭐ Support

If you found this project useful, consider giving it a ⭐ on GitHub.

Thank you for visiting **LabNexa**!
