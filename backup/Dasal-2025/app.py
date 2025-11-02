import base64
import csv
import io
import os
import qrcode
import smtplib
import time
import uuid
from email.message import EmailMessage
from flask import Flask, render_template, render_template_string, request, redirect, url_for
from flask import jsonify
from flask import send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import desc
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
#from app import app, db, Attendee  # adjust if in different module
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import asc
from reportlab.lib.pagesizes import A4
from utils.pdf_utils import generate_attendee_list

# --- Flask & DB setup ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diwali-attendees.db'
db = SQLAlchemy(app)

class Attendee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    party_count = db.Column(db.Integer, default=1)   # <--- added
    qr_id = db.Column(db.String(120), unique=True)
    checked_in = db.Column(db.Boolean, default=False)
    checked_in_at = db.Column(db.DateTime)


# --- QR code folder ---
QR_FOLDER = "static/qr_codes"
os.makedirs(QR_FOLDER, exist_ok=True)

# --- SMTP settings ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "mahadhasal@gmail.com"
SMTP_PASSWORD = "aaum bekp ijhj cway"

# --- Functions ---
def generate_qr(qr_text, filename):
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    qr.add_data(qr_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)

def send_email_qr(to_email, subject, body, attachment_path):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    msg.set_content(body)

    with open(attachment_path, 'rb') as f:
        msg.add_attachment(f.read(), maintype='image', subtype='png', filename=os.path.basename(attachment_path))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        print(f"Email sent to {to_email}")

def send_email(to_email, subject, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    msg.set_content(body)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        print(f"Email sent to {to_email}")

def send_email_qr_party_count(attendee, qr_base64):
    """Send QR code email with name and party count displayed."""
    msg = MIMEMultipart("related")
    msg["Subject"] = f"Your Event QR Code - {attendee.name}"
    msg["From"] = SMTP_USER
    msg["To"] = attendee.email

    # Inline HTML with embedded image
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; text-align:center;">
        <h2>Hello {attendee.name},</h2>
        <p>Please find your QR code below for event check-in.</p>
        <img src="cid:qrimage" style="width:220px;height:220px;"><br>
        <p><strong>Party Count:</strong> {attendee.party_count}</p>
        <p>Show this QR at the registration desk.</p>
        <p>– Event Team</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_content, "html"))

    # Attach QR image
    qr_bytes = base64.b64decode(qr_base64)
    img = MIMEImage(qr_bytes, name="qrcode.png")
    img.add_header("Content-ID", "<qrimage>")
    msg.attach(img)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, attendee.email, msg.as_string())
    print(f"✅ Email sent to {attendee.name} ({attendee.email})")

# Routes
'''
@app.route("/")
def index():
    attendees = Attendee.query.all()
    return render_template("index-v0.html", attendees=attendees)
'''

#@app.route("/")
def index_v1():
    total_attendees = Attendee.query.count()
    checked_in_count = Attendee.query.filter(Attendee.checked_in_at.isnot(None)).count()
    return render_template(
        "index-v1.html",
        total_attendees=total_attendees,
        checked_in_count=checked_in_count
    )

#@app.route("/")
def index_v2():
    total_attendees = Attendee.query.count()
    checked_in_count = Attendee.query.filter(Attendee.checked_in_at.isnot(None)).count()
    total_party_count = db.session.query(db.func.sum(Attendee.party_count)).scalar() or 0
    checked_in_party_count = db.session.query(db.func.sum(Attendee.party_count)).filter(
        Attendee.checked_in_at.isnot(None)
    ).scalar() or 0

    return render_template(
        "index-v2.html",
        total_attendees=total_attendees,
        total_party_count=total_party_count,
        checked_in_count=checked_in_count,
        checked_in_party_count=checked_in_party_count
    )

@app.route("/")
def index():
    total_attendees = db.session.query(db.func.count(Attendee.id)).scalar() or 0
    total_checked_in = (
        db.session.query(db.func.count(Attendee.id))
        .filter(Attendee.checked_in_at.isnot(None))
        .scalar()
        or 0
    )
    total_pending = total_attendees - total_checked_in

    total_party_count = (
        db.session.query(db.func.coalesce(db.func.sum(Attendee.party_count), 0)).scalar()
    )
    checked_in_party_count = (
        db.session.query(db.func.coalesce(db.func.sum(Attendee.party_count), 0))
        .filter(Attendee.checked_in_at.isnot(None))
        .scalar()
    )
    pending_party_count = total_party_count - checked_in_party_count

    return render_template(
        "index-v2-working.html",
        total_attendees=total_attendees,
        total_checked_in=total_checked_in,
        total_pending=total_pending,
        total_party_count=total_party_count,
        checked_in_party_count=checked_in_party_count,
        pending_party_count=pending_party_count,
    )

@app.route("/scan")
def scan():
    return render_template("scan-v3.html")

#s@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    email = request.form["email"]

    # Generate unique QR ID
    qr_id = str(uuid.uuid4())
    attendee = Attendee(qr_id=qr_id, name=name, email=email)
    db.session.add(attendee)
    db.session.commit()

    # Generate QR code
    qr_bytes, qr_b64, verify_url = generate_qr(qr_id)

    # Prepare email
    msg = Message(
        subject="Your Event QR Code",
        recipients=[email],
        body=f"Hello {name},\n\nThanks for registering. Scan this QR at the event.\nCheck-in link: {verify_url}"
    )

    # Attach QR as downloadable file
    msg.attach(
        filename="qrcode.png",         # file name
        content_type="image/png",       # MIME type
        data=qr_bytes                   # raw bytes
    )

    # Send email
    mail.send(msg)

    # Return success page with inline preview
    return render_template("success.html", attendee=attendee, qr_code=qr_b64)

def send_checkin_email(to_email, attendee_name):
    msg = EmailMessage()
    msg["Subject"] = "Maha Dasal 2025 Check-In Confirmation"
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg.set_content(
        f"Dear {attendee_name},\n\n"
        "We’ve successfully checked you in at Maha Dasal 2025.\n"
        "Govidhachaem Govindha!\n\n"
        "— Maha Dasal Team"
    )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

@app.route("/verify")
def verify():
    qr_id = request.args.get("qr_id")
    if not qr_id:
        return jsonify({"status": "error", "message": "No QR ID provided"}), 400

    attendee = Attendee.query.filter_by(qr_id=qr_id).first()
    if not attendee:
        return jsonify({"status": "error", "message": "Invalid QR"}), 404

    if not attendee.checked_in_at:
        attendee.checked_in_at = datetime.now()
        db.session.commit()

        # Send confirmation email (don’t block check-in if it fails)
        try:
            send_checkin_email(attendee.email, attendee.name)
            email_status = "confirmation email sent"
        except Exception as e:
            email_status = f"email failed: {e}"

        return jsonify({
            "status": "success",
            "name": attendee.name,
            "party_count": attendee.party_count,
            "checked_in_at": attendee.checked_in_at.strftime("%Y-%m-%d %H:%M:%S"),
            "message": f"{attendee.name} checked in ({attendee.party_count} in party), {email_status}"
        })
    else:
        return jsonify({
            "status": "info",
            "name": attendee.name,
            "party_count": attendee.party_count,
            "checked_in_at": attendee.checked_in_at.strftime("%Y-%m-%d %H:%M:%S"),
            "message": f"{attendee.name} already checked in at {attendee.checked_in_at}"
        })

#@app.route("/verify")
def verify_v3():
    qr_id = request.args.get("qr_id")
    if not qr_id:
        return jsonify({"status": "error", "message": "No QR ID provided"}), 400

    attendee = Attendee.query.filter_by(qr_id=qr_id).first()
    if attendee:
        # Mark check-in time if not already checked in
        if not attendee.checked_in_at:
            attendee.checked_in_at = datetime.now()
            db.session.commit()

            # Send email confirmation
            try:
                send_checkin_email(attendee.email, attendee.name)
            except Exception as e:
                return jsonify({
                    "status": "success",
                    "message": f"{attendee.name} checked in, but email failed: {e}"
                })

            return jsonify({
                "status": "success",
                "message": f"{attendee.name} checked in, confirmation email sent"
            })
        else:
            return jsonify({
                "status": "info",
                "message": f"{attendee.name} already checked in at {attendee.checked_in_at}"
            })
    else:
        return jsonify({"status": "error", "message": "Invalid QR"})


#@app.route("/verify")
def verify_v1():
    qr_id = request.args.get("qr_id")
    if not qr_id:
        return {"status": "error", "message": "No QR ID provided"}, 400

    attendee = Attendee.query.filter_by(qr_id=qr_id).first()
    if attendee:
        attendee.checked_in_at = datetime.now()
        db.session.commit()
        return {"status": "success", "message": f"{attendee.name} verified"}
    else:
        return {"status": "error", "message": "Invalid QR"}

#@app.route("/verify/<qr_id>")
def verify_v3(qr_id):
    attendee = Attendee.query.filter_by(qr_id=qr_id).first()
    if attendee:
        if attendee.checked_in_at:
            return render_template("verify.html", attendee=attendee, status="already")
        else:
            attendee.checked_in_at = datetime.now()
            db.session.commit()
            return render_template("verify.html", attendee=attendee, status="valid")
    else:
        return render_template("verify.html", attendee=None, status="invalid")

#@app.route("/verify_api/<qr_id>")
def verify_api(qr_id):
    attendee = Attendee.query.filter_by(qr_id=qr_id).first()
    if attendee:
        if attendee.checked_in_at:
            return jsonify({
                "status": "already",
                "name": attendee.name,
                "checked_in_at": attendee.checked_in_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            attendee.checked_in_at = datetime.now()
            db.session.commit()
            return jsonify({
                "status": "valid",
                "name": attendee.name,
                "checked_in_at": attendee.checked_in_at.strftime("%Y-%m-%d %H:%M:%S")
            })
    else:
        return jsonify({"status": "invalid"})

#@app.route("/admin")
def admin_page():
    # Query all attendees
    attendees = Attendee.query.all()

    # Count totals
    total_attendees = len(attendees)
    checked_in_count = Attendee.query.filter_by(checked_in=True).count()

    return render_template(
        "admin-v2.html",
        attendees=attendees,
        total_attendees=total_attendees,
        checked_in_count=checked_in_count
    )


@app.route("/admin")
def admin():
    attendees = Attendee.query.all()
    total_attendees = Attendee.query.count()
    checked_in_count = Attendee.query.filter(Attendee.checked_in_at.isnot(None)).count()
    total_party_count = db.session.query(db.func.sum(Attendee.party_count)).scalar() or 0
    checked_in_party_count = db.session.query(db.func.sum(Attendee.party_count)).filter(
        Attendee.checked_in_at.isnot(None)
    ).scalar() or 0

    return render_template(
        "admin.html",
        attendees=attendees,
        total_attendees=total_attendees,
        checked_in_count=checked_in_count,
        total_party_count=total_party_count,
        checked_in_party_count=checked_in_party_count
    )

# Standard/static admin page
@app.route("/admin_static")
def admin_static():
    attendees = Attendee.query.all()
    return render_template("admin-v0.html", attendees=attendees)

@app.route("/admin_api")
def admin_api():
    attendees = Attendee.query.all()
    result = []
    for a in attendees:
        result.append({
            "name": a.name,
            "email": a.email,
            "qr_id": a.qr_id,
            "checked_in_at": a.checked_in_at.strftime("%Y-%m-%d %H:%M:%S") if a.checked_in_at else None
        })
    return jsonify({"attendees": result})

@app.route("/stats")
def stats():
    total_attendees = Attendee.query.count()
    checked_in_count = Attendee.query.filter(Attendee.checked_in_at.isnot(None)).count()

    recent = (
        Attendee.query.filter(Attendee.checked_in_at.isnot(None))
        .order_by(desc(Attendee.checked_in_at))
        .limit(5)
        .all()
    )

    recent_list = [
        {
            "name": a.name,
            "email": a.email,
            "party_count": a.party_count,
            "checked_in_at": a.checked_in_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for a in recent
    ]

    return {
        "total_attendees": total_attendees,
        "checked_in_count": checked_in_count,
        "recent_checkins": recent_list
    }


@app.route("/recent_checkins")
def recent_checkins():
    attendees = Attendee.query.filter(Attendee.checked_in_at.isnot(None))\
                              .order_by(Attendee.checked_in_at.desc())\
                              .limit(10).all()
    return jsonify([
        {
            "name": a.name,
            "email": a.email,
            "party_count": a.party_count,
            "checked_in_at": a.checked_in_at.strftime("%Y-%m-%d %H:%M:%S")
        } for a in attendees
    ])


#@app.route("/api/recent-checkins")
def api_recent_checkins_unsorted():
    # Fetch last 10 check-ins
    recent_attendees = (
        Attendee.query.filter(Attendee.checked_in_at.isnot(None))
        .order_by(Attendee.checked_in_at.desc())
        .limit(10)
        .all()
    )

    # Convert into JSON-serializable format
    data = [
        {
            "name": att.name,
            "email": att.email,
            "party_count": att.party_count,
            "checked_in_at": att.checked_in_at.strftime("%Y-%m-%d %H:%M:%S")
            if att.checked_in_at else None,
        }
        for att in recent_attendees
    ]

    return jsonify({"recent_attendees": data})

def unsorted():
    attendees = Attendee.query.all()
    pdf_file = "attendees_qr.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    data = [["Name", "Email", "QR Code"]]

    for attendee in attendees:
        qr_path = os.path.join("static", "qrcodes", f"{attendee.qr_id}.png")
        if os.path.exists(qr_path):
            qr_img = Image(qr_path, width=80, height=80)
        else:
            qr_img = Paragraph("❌ Missing QR", styles["Normal"])
        data.append([
            attendee.name,
            attendee.email,
            qr_img
        ])

    table = Table(data, colWidths=[150, 200, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    return send_file(pdf_file, as_attachment=True)


@app.route("/printable_pdf")
def printable_pdf():
    attendees = Attendee.query.all()
    pdf_file = "attendees_qr.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    data = [["Name", "Email", "QR Code"]]

    for attendee in attendees:
        qr_path = os.path.join("static", "qr_codes", f"{attendee.qr_id}.png")
        if os.path.exists(qr_path):
            qr_img = Image(qr_path, width=20, height=20)
        else:
            qr_img = Paragraph("❌ Missing QR", styles["Normal"])
        data.append([
            attendee.name,
            attendee.email,
            qr_img
        ])

    table = Table(data, colWidths=[150, 200, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    return send_file(pdf_file, as_attachment=True)


@app.route("/download_attendee_list")
def download_attendee_list():
    attendees = Attendee.query.order_by(asc(Attendee.name)).all()
    filepath = "attendee_list.pdf"
    generate_attendee_list(attendees, filepath)
    return send_file(filepath, as_attachment=True)

# --- MAIN: all DB access inside app context ---s
if __name__ == "__main__":
    if not os.path.exists("diwali-attendees.db"):
        with app.app_context():
            db.create_all()  # create tables if not exists
            with open("diwali-attendees.csv", newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                headers = [h.strip().lower() for h in next(reader)]
                name_idx = headers.index("name")
                email_idx = headers.index("email")
                party_idx = headers.index("number in party") if "number in party" in headers else None

                for row in reader:
                    name = row[name_idx].strip()
                    email = row[email_idx].strip()
                    party_count = int(row[party_idx].strip()) if row[party_idx].strip() else 1

                    # Skip if already exists
                    if Attendee.query.filter_by(email=email).first():
                        print(f"{email} already exists, skipping...")
                        continue

                    # Generate QR
                    qr_id = str(uuid.uuid4())
                    qr_file = os.path.join(QR_FOLDER, f"{qr_id}.png")
                    generate_qr(qr_id, qr_file)

                    # Save to DB
                    attendee = Attendee(name=name, email=email, party_count=party_count, qr_id=qr_id)
                    db.session.add(attendee)
                    db.session.commit()

                    # Send email
                    subject = "Diwali 2025 Check-In QR Code"
                    body = f"Namaskar {name}s,\n\nPlease find your QR code attached for Diwali 2025 Check-In.\nShow this QR code and inform your number of headcounts at the registration desk. Your RSVP headcount is {party_count}. 🙏🙏\n— 2025 Diwali Team"
                    send_email_qr(email, subject, body, qr_file)
                    time.sleep(2)  # wait 1 second between sends
    app.run(host="0.0.0.0", port=5000, debug=False)