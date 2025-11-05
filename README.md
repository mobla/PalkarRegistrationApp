🪪 PalkarRegistrationApp
A simple Flask-based QR code registration and check-in system for managing event attendees — built for Palkar community events.
Supports attendee registration, PDF QR code generation, real-time scanning, and admin reporting.

📋 Overview
PalkarRegistrationApp is a web-based system built with Flask that streamlines attendee management for community or family events.
It supports QR-code–based check-ins, real-time updates, admin dashboards, and CSV/PDF exports — all from a simple browser interface.

✨ Features
✅ Generate and scan unique QR codes for each attendee
✅ Real-time verification and check-in confirmation
✅ Headcount selection (for multi-member parties)
✅ Admin dashboard to view, sort, and export attendees
✅ CSV & PDF export of registration data
✅ Email notifications on check-in
✅ Fully mobile-friendly interface

🚀 Features
Attendee Registration
Add new attendees with name, email, and party count.
Generates unique QR code per registration.
QR Code Check-In
Scan QR codes via webcam or mobile camera.
Verify attendees instantly from the database.
Headcount Selection
Choose how many members of a party are checking in at once.
Admin Dashboard
View all registrations.
Download attendee list as PDF or CSV.
Sortable table with visual sort indicators (↑ / ↓).
Email Confirmation
Sends confirmation email automatically on successful check-in.


🧩 Tech Stack
| Component       | Technology              |
| --------------- | ----------------------- |
| Backend         | Python (Flask)          |
| Frontend        | HTML, CSS, JavaScript   |
| Database        | SQLite (SQLAlchemy ORM) |
| QR Generation   | `qrcode` Python library |
| Email           | Flask-Mail              |
| Exports         | ReportLab (PDF), CSV    |
| Template Engine | Jinja2                  |
| Component      | Technology                          |
| -------------- | ----------------------------------- |
| Backend        | Python (Flask)                      |
| Frontend       | HTML, CSS, JavaScript (vanilla)     |
| Database       | SQLite (via SQLAlchemy ORM)         |
| QR Codes       | `qrcode` Python library             |
| PDF Generation | `reportlab`                         |
| Email          | `smtplib` / Flask Mail              |
| Deployment     | Gunicorn / any WSGI-compatible host |


🏗️ Project Structure
PalkarRegistrationApp/
├── app.py                      # Flask app entry point
├── models.py                   # Database models (Attendee)
├── templates/
│   ├── register.html           # Registration page
│   ├── scan.html               # QR code scanning & check-in
│   ├── admin.html              # Admin dashboard
├── static/
│   ├── css/                    # Custom styles
│   ├── js/                     # Client-side scripts
├── migrations/                 # Flask-Migrate migration files
├── attendee_list.pdf           # Auto-generated attendee report
├── requirements.txt            # Python dependencies
└── README.md                   # This file

⚙️ Setup Instructions
1️⃣ Clone the Repository
git clone https://github.com/<your-username>/PalkarRegistrationApp.git
cd PalkarRegistrationApp

2️⃣ Create and Activate a Virtual Environment
python3 -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)

python3 -m venv .venv
source .venv/bin/activate   # (Mac/Linux)
.venv\Scripts\activate      # (Windows)

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Initialize Database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

Alternatively, to start fresh manually:
python
>>> from app import db
>>> db.create_all()
>>> exit()

5️⃣ Run the Application
flask run

Visit 👉 http://localhost:5000

🧾 Environment Variables
Create a .env file for configuration:
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password

📸 Screenshots
| Page                                         | Description                                                      |
| -------------------------------------------- | ---------------------------------------------------------------- |
| ![Scan Screen](docs/scan_page.png)           | **Scan Page** – QR code scanning and check-in confirmation       |
| ![Admin Dashboard](docs/admin_dashboard.png) | **Admin Dashboard** – sortable attendee list with export options |


🧠 Key Endpoints
| Endpoint                  | Method | Description                      |
| ------------------------- | ------ | -------------------------------- |
| `/`                       | GET    | Homepage or redirect to scanner  |
| `/scan`                   | GET    | QR scanner interface             |
| `/verify?qr_id=<id>`      | GET    | Verify attendee’s QR             |
| `/update_checkin`         | POST   | Update headcount & check-in time |
| `/admin`                  | GET    | Admin dashboard                  |
| `/download_csv`           | GET    | Download attendee data as CSV    |
| `/download_attendee_list` | GET    | Generate attendee PDF list       |


📤 Deployment
You can deploy this app easily on:
Render, Railway, or PythonAnywhere (Flask native)

Heroku (using Gunicorn)
AWS EC2 / Lightsail

Example (Gunicorn):
gunicorn -w 4 app:app

📊 Admin Exportss
Download Attendee List (PDF)
/download_attendee_list

Export Database (CSV)
/export_csv

🧪 Future Enhancements
Admin login & authentication
Check-in analytics dashboard
Mobile responsive design
REST API for mobile apps


🗃️ Example Attendee Table Schema
| Field                    | Type     | Description             |
| ------------------------ | -------- | ----------------------- |
| `id`                     | Integer  | Primary key             |
| `name`                   | String   | Attendee’s name         |
| `email`                  | String   | Attendee’s email        |
| `qr_id`                  | String   | Unique QR code          |
| `party_count`            | Integer  | Total people registered |
| `checked_in_party_count` | Integer  | Checked-in headcount    |
| `checked_in_at`          | DateTime | Check-in timestamp      |

🤝 Contributing
Pull requests are welcome!
For major changes, please open an issue first to discuss what you’d like to modify.

📄 License
This project is licensed under the MIT License — feel free to use and adapt.

✉️ Email Notifications
On successful check-in, an email is sent to the attendee confirming attendance.
Make sure to configure these environment variables:
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password

📦 Export Options
Download as CSV: /download_csv
Download as PDF: /download_attendee_list

❤️ Acknowledgements
Developed by the Palkar Community Volunteers
With contributions and support from our amazing event organizers & tech leads.



# 🪔 PalkarRegistrationApp

A **Flask-based QR code registration and check-in dashboard** for managing Palkar community event attendees — built with love for the **Bay Area Diwali 2025** celebration 🎉

This app enables you to register families, generate unique QR codes, scan them at the event, track real-time check-ins, and export reports — all through a clean and festive web interface.

---

## ✨ Features

✅ **Attendee Registration**
- Add new families or individuals with party size.
- Automatically generates a unique QR code for each registration.

✅ **QR Code Check-In**
- Scan QR codes via webcam or phone camera.
- Instantly updates the check-in dashboard in real time.

✅ **Headcount Selection**
- Choose the number of people checking in from a family.

✅ **Admin Dashboard**
- View, sort, and manage all attendees.
- Download reports in **PDF** and **CSV** format.
- Sortable table with ascending/descending arrow indicators.

✅ **Email Notifications**
- Sends check-in confirmation emails automatically.

✅ **Responsive Design**
- Optimized for both desktop and mobile devices.

---

## 🧰 Tech Stack

| Layer | Technology |
|--------|-------------|
| Backend | Python (Flask) |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Database | SQLite (SQLAlchemy ORM) |
| QR Codes | `qrcode` |
| PDF Generation | `reportlab` |
| Email | `smtplib` / Flask Mail |
| Deployment | Gunicorn / Render / Railway / PythonAnywhere |

---

## 🏗️ Folder Structure

# 🪔 PalkarRegistrationApp

A **Flask-based QR code registration and check-in dashboard** for managing Palkar community event attendees — built with love for the **Bay Area Diwali 2025** celebration 🎉

This app enables you to register families, generate unique QR codes, scan them at the event, track real-time check-ins, and export reports — all through a clean and festive web interface.

---

## ✨ Features

✅ **Attendee Registration**
- Add new families or individuals with party size.
- Automatically generates a unique QR code for each registration.

✅ **QR Code Check-In**
- Scan QR codes via webcam or phone camera.
- Instantly updates the check-in dashboard in real time.

✅ **Headcount Selection**
- Choose the number of people checking in from a family.

✅ **Admin Dashboard**
- View, sort, and manage all attendees.
- Download reports in **PDF** and **CSV** format.
- Sortable table with ascending/descending arrow indicators.

✅ **Email Notifications**
- Sends check-in confirmation emails automatically.

✅ **Responsive Design**
- Optimized for both desktop and mobile devices.

---

## 🧰 Tech Stack

| Layer | Technology |
|--------|-------------|
| Backend | Python (Flask) |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Database | SQLite (SQLAlchemy ORM) |
| QR Codes | `qrcode` |
| PDF Generation | `reportlab` |
| Email | `smtplib` / Flask Mail |
| Deployment | Gunicorn / Render / Railway / PythonAnywhere |

---

## 🏗️ Folder Structure

# 🪔 PalkarRegistrationApp

A **Flask-based QR code registration and check-in dashboard** for managing Palkar community event attendees — built with love for the **Bay Area Diwali 2025** celebration 🎉

This app enables you to register families, generate unique QR codes, scan them at the event, track real-time check-ins, and export reports — all through a clean and festive web interface.

---

## ✨ Features

✅ **Attendee Registration**
- Add new families or individuals with party size.
- Automatically generates a unique QR code for each registration.

✅ **QR Code Check-In**
- Scan QR codes via webcam or phone camera.
- Instantly updates the check-in dashboard in real time.

✅ **Headcount Selection**
- Choose the number of people checking in from a family.

✅ **Admin Dashboard**
- View, sort, and manage all attendees.
- Download reports in **PDF** and **CSV** format.
- Sortable table with ascending/descending arrow indicators.

✅ **Email Notifications**
- Sends check-in confirmation emails automatically.

✅ **Responsive Design**
- Optimized for both desktop and mobile devices.

---

## 🧰 Tech Stack

| Layer | Technology |
|--------|-------------|
| Backend | Python (Flask) |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Database | SQLite (SQLAlchemy ORM) |
| QR Codes | `qrcode` |
| PDF Generation | `reportlab` |
| Email | `smtplib` / Flask Mail |
| Deployment | Gunicorn / Render / Railway / PythonAnywhere |

---

## 🏗️ Folder Structure
# 🪔 PalkarRegistrationApp

A **Flask-based QR code registration and check-in dashboard** for managing Palkar community event attendees — built with love for the **Bay Area Diwali 2025** celebration 🎉

This app enables you to register families, generate unique QR codes, scan them at the event, track real-time check-ins, and export reports — all through a clean and festive web interface.

---

## ✨ Features

✅ **Attendee Registration**
- Add new families or individuals with party size.
- Automatically generates a unique QR code for each registration.

✅ **QR Code Check-In**
- Scan QR codes via webcam or phone camera.
- Instantly updates the check-in dashboard in real time.

✅ **Headcount Selection**
- Choose the number of people checking in from a family.

✅ **Admin Dashboard**
- View, sort, and manage all attendees.
- Download reports in **PDF** and **CSV** format.
- Sortable table with ascending/descending arrow indicators.

✅ **Email Notifications**
- Sends check-in confirmation emails automatically.

✅ **Responsive Design**
- Optimized for both desktop and mobile devices.

---

## 🧰 Tech Stack

| Layer | Technology |
|--------|-------------|
| Backend | Python (Flask) |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Database | SQLite (SQLAlchemy ORM) |
| QR Codes | `qrcode` |
| PDF Generation | `reportlab` |
| Email | `smtplib` / Flask Mail |
| Deployment | Gunicorn / Render / Railway / PythonAnywhere |

---

## 🏗️ Folder Structure
# 🪔 PalkarRegistrationApp

A **Flask-based QR code registration and check-in dashboard** for managing Palkar community event attendees — built with love for the **Bay Area Diwali 2025** celebration 🎉

This app enables you to register families, generate unique QR codes, scan them at the event, track real-time check-ins, and export reports — all through a clean and festive web interface.

---

## ✨ Features

✅ **Attendee Registration**
- Add new families or individuals with party size.
- Automatically generates a unique QR code for each registration.

✅ **QR Code Check-In**
- Scan QR codes via webcam or phone camera.
- Instantly updates the check-in dashboard in real time.

✅ **Headcount Selection**
- Choose the number of people checking in from a family.

✅ **Admin Dashboard**
- View, sort, and manage all attendees.
- Download reports in **PDF** and **CSV** format.
- Sortable table with ascending/descending arrow indicators.

✅ **Email Notifications**
- Sends check-in confirmation emails automatically.

✅ **Responsive Design**
- Optimized for both desktop and mobile devices.

---

## 🧰 Tech Stack

| Layer | Technology |
|--------|-------------|
| Backend | Python (Flask) |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Database | SQLite (SQLAlchemy ORM) |
| QR Codes | `qrcode` |
| PDF Generation | `reportlab` |
| Email | `smtplib` / Flask Mail |
| Deployment | Gunicorn / Render / Railway / PythonAnywhere |

---

## 🏗️ Folder Structure
PalkarRegistrationApp/
├── app.py # Main Flask app
├── models.py # SQLAlchemy models (Attendee)
├── templates/
│ ├── register.html # Registration form
│ ├── scan.html # QR code scanner
│ ├── admin.html # Admin dashboard
│ └── dashboard.html # Public stats dashboard
├── static/
│ ├── css/ # Styling
│ ├── js/ # Client scripts
│ └── images/ # Backgrounds and assets
├── migrations/ # Database migrations
├── attendee_list.pdf # Auto-generated report
├── requirements.txt # Dependencies
└── README.md # You are here :)


---

## 🧾 Setup Instructions

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/mobla/PalkarRegistrationApp.git
cd PalkarRegistrationApp

