import base64
import csv
import io
import math
import os
import qrcode
import re
import smtplib
import time
import uuid
from email.message import EmailMessage
from xml.sax.saxutils import escape
from flask import Flask, render_template, request
from flask import jsonify
from flask import send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import asc
from sqlalchemy import func
from sqlalchemy import inspect, text
from reportlab.lib.pagesizes import A4
from utils.pdf_utils import generate_attendee_list

# --- Flask & DB setup ---
app = Flask(__name__)

# Database configuration - use environment variable if available (for Render/PostgreSQL)
# Otherwise use SQLite for local development
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Render provides postgres:// but SQLAlchemy needs postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Local development with SQLite
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "diwali-attendees.db")}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
db = SQLAlchemy(app)

class Attendee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    party_count = db.Column(db.Integer, default=1)   # <--- added
    sweet_karam = db.Column(db.Float, nullable=True)
    qr_id = db.Column(db.String(120), unique=True)
    #checked_in = db.Column(db.Boolean, default=False)
    checked_in_at = db.Column(db.DateTime, nullable=True)  # ✅ no default timestamp
    checked_in_party_count = db.Column(db.Integer, default=0)
    qr_email_sent_at = db.Column(db.DateTime, nullable=True)


# --- QR code folder ---
QR_FOLDER = "static/qr_codes"
os.makedirs(QR_FOLDER, exist_ok=True)

# --- SMTP settings ---
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
EMAIL_ADDRESS_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email_address(address):
    return bool(address and EMAIL_ADDRESS_RE.fullmatch(address.strip()))


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
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must be set in the environment before sending email.")

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


def ensure_database_schema():
    """Create missing tables and safely add columns used by current app versions."""
    db.create_all()
    column_names = {column["name"] for column in inspect(db.engine).get_columns(Attendee.__tablename__)}
    missing_columns = {
        "qr_email_sent_at": "TIMESTAMP",
        "sweet_karam": "FLOAT",
    }
    for column_name, sql_type in missing_columns.items():
        if column_name not in column_names:
            with db.engine.begin() as connection:
                connection.execute(text(
                    f"ALTER TABLE {Attendee.__tablename__} ADD COLUMN {column_name} {sql_type}"
                ))


def import_attendees_from_csv():
    """Sync attendee identity and headcounts from the 2026 CSV; never emails here."""
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diwali-attendees.csv")
    if not os.path.exists(csv_path):
        return {"imported": 0, "updated": 0, "skipped": 0, "errors": ["diwali-attendees.csv was not found."]}

    imported = 0
    skipped = 0
    errors = []
    warnings = []
    blank_sweet_karam_count = 0
    os.makedirs(QR_FOLDER, exist_ok=True)

    with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        if not reader.fieldnames:
            return {"imported": 0, "updated": 0, "skipped": 0, "errors": ["The CSV file has no header row."]}

        fieldnames = {field.strip().lower() for field in reader.fieldnames if field}
        if not {"name", "email"}.issubset(fieldnames):
            return {"imported": 0, "updated": 0, "skipped": 0, "errors": ["CSV must contain name and email columns."]}

        sweet_karam_column = next((
            field for field in fieldnames
            if field.replace("_", "-").replace(" ", "-") in (
                "sweet-karam", "sweetkaram", "sweet-kaaram", "sweetkaaram"
            )
        ), None)
        if sweet_karam_column is None:
            warnings.append("Sweet-Karam column is missing; Sweet-Karam values were not imported. Add the column to this CSV and sync again.")

        updated = 0
        for row_number, row in enumerate(reader, start=2):
            normalized = {}
            for key, value in row.items():
                # DictReader stores surplus columns under a None key as a list.
                # Ignore those columns; only consume named CSV fields.
                if not isinstance(key, str):
                    continue
                normalized[key.strip().lower()] = value.strip() if isinstance(value, str) else ""
            name = normalized.get("name", "")
            email = normalized.get("email", "")
            if not name or not email:
                skipped += 1
                continue
            if not is_valid_email_address(email):
                errors.append(f"Row {row_number}: invalid email address {email!r}; expected a full address such as name@example.com.")
                continue

            # The 2026 export has age-group columns instead of total_people.
            # Sum them for party_count, which remains the app's canonical total.
            adult_column = "adults" if "adults" in fieldnames else None
            child_6_12_column = next((key for key in ("kids 6-12", "children 6-12", "children_6_12") if key in fieldnames), None)
            child_under_5_column = next((key for key in ("kids 0-5", "children 0-5", "children_under_5") if key in fieldnames), None)
            try:
                if adult_column or child_6_12_column or child_under_5_column:
                    headcount_columns = (adult_column, child_6_12_column, child_under_5_column)
                    counts = [int(normalized.get(key, "") or "0") if key else 0 for key in headcount_columns]
                    if any(count < 0 for count in counts):
                        raise ValueError
                    party_count = sum(counts)
                else:
                    raw_party_count = normalized.get("total_people") or normalized.get("party_count") or "1"
                    party_count = int(raw_party_count)
                if party_count < 1:
                    raise ValueError
            except ValueError:
                errors.append(f"Row {row_number}: adult/child counts must be nonnegative whole numbers with a total above zero.")
                continue

            sweet_karam = None
            if sweet_karam_column:
                raw_sweet_karam = normalized.get(sweet_karam_column, "")
                if raw_sweet_karam:
                    try:
                        raw_sweet_karam = float(raw_sweet_karam)
                        if not math.isfinite(raw_sweet_karam) or raw_sweet_karam < 0:
                            raise ValueError
                        sweet_karam = raw_sweet_karam
                    except ValueError:
                        errors.append(f"Row {row_number}: Sweet-Karam must be a nonnegative number.")
                        continue
                else:
                    blank_sweet_karam_count += 1

            existing = Attendee.query.filter(func.lower(Attendee.email) == email.lower()).first()
            if not existing:
                # Repair a legacy row when a previously invalid email was corrected in the CSV.
                same_name = Attendee.query.filter(func.lower(Attendee.name) == name.lower()).all()
                stale_email_matches = [a for a in same_name if not is_valid_email_address(a.email)]
                if len(stale_email_matches) == 1:
                    existing = stale_email_matches[0]
                elif len(stale_email_matches) > 1:
                    errors.append(f"Row {row_number}: multiple attendees named {name!r} have invalid stored email addresses; resolve them manually.")
                    continue
            if existing:
                changed = existing.email.lower() != email.lower() or existing.name != name or existing.party_count != party_count
                existing.email = email
                existing.name = name
                existing.party_count = party_count
                if sweet_karam_column and existing.sweet_karam != sweet_karam:
                    existing.sweet_karam = sweet_karam
                    changed = True
                if changed:
                    try:
                        db.session.commit()
                        updated += 1
                    except Exception as exc:
                        db.session.rollback()
                        errors.append(f"Row {row_number}: could not update attendee ({type(exc).__name__}).")
                        app.logger.exception("CSV headcount update failed on row %s", row_number)
                else:
                    skipped += 1
                continue

            qr_id = str(uuid.uuid4())
            qr_file = os.path.join(QR_FOLDER, f"{qr_id}.png")
            try:
                generate_qr(qr_id, qr_file)
                db.session.add(Attendee(name=name, email=email, party_count=party_count,
                                        sweet_karam=sweet_karam, qr_id=qr_id))
                db.session.commit()
                imported += 1
            except Exception as exc:
                db.session.rollback()
                if os.path.exists(qr_file):
                    os.remove(qr_file)
                errors.append(f"Row {row_number}: could not import attendee ({type(exc).__name__}).")
                app.logger.exception("CSV attendee import failed on row %s", row_number)

    if blank_sweet_karam_count:
        warnings.append(
            f"Sweet-Karam is blank for {blank_sweet_karam_count} CSV row(s); those values display as '-'."
        )
    return {"imported": imported, "updated": updated, "skipped": skipped, "errors": errors, "warnings": warnings}


def send_attendee_qr_email(attendee):
    if not is_valid_email_address(attendee.email):
        raise ValueError(
            f"The stored recipient address {attendee.email!r} is invalid. Correct the Email cell in diwali-attendees.csv and sync again."
        )
    if not attendee.qr_id:
        attendee.qr_id = str(uuid.uuid4())

    os.makedirs(QR_FOLDER, exist_ok=True)
    qr_file = os.path.join(QR_FOLDER, f"{attendee.qr_id}.png")
    if not os.path.exists(qr_file):
        generate_qr(attendee.qr_id, qr_file)

    subject = "Diwali 2026 Check-In QR Code"
    body = (
        f"Namaskar {attendee.name}, \n"
        "Happy Diwali! Please find your QR code attached for Diwali 2026 Check-In.\n\n"
        "Kindly show this QR code and inform your number of headcounts at the registration desk. "
        f"Your registered headcount is {attendee.party_count}. Enjoy the event!\n\n"
        "— Dhannu🙏🙏,\n2026 Diwali Team"
    )
    send_email_qr(attendee.email, subject, body, qr_file)


def email_failure_message(exc):
    if isinstance(exc, ValueError):
        return str(exc)
    if isinstance(exc, RuntimeError):
        return "Set SMTP_USER and SMTP_PASSWORD in the app environment. Use a Google App Password for Gmail SMTP."
    if isinstance(exc, smtplib.SMTPRecipientsRefused):
        refused = ", ".join(exc.recipients)
        return f"Gmail rejected recipient address(es): {refused}. Check the attendee Email field in diwali-attendees.csv."
    if isinstance(exc, (smtplib.SMTPAuthenticationError, smtplib.SMTPServerDisconnected)):
        return (
            "Gmail SMTP login failed. The Google App Password may be missing, invalid, or revoked. "
            "Create a new Google App Password and set it as SMTP_PASSWORD."
        )
    return (
        "Could not send through Gmail SMTP. Check SMTP_SERVER, SMTP_PORT, network access, "
        "SMTP_USER, and SMTP_PASSWORD."
    )

# Routes
#@app.route("/")
def index_v1():
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
        "index.html",
        total_attendees=total_attendees,
        total_checked_in=total_checked_in,
        total_pending=total_pending,
        total_party_count=total_party_count,
        checked_in_party_count=checked_in_party_count,
        pending_party_count=pending_party_count,
    )

@app.route("/")
def index():
    # Total families registered
    total_attendees = db.session.query(db.func.count(Attendee.id)).scalar() or 0

    # Total families checked in
    total_checked_in = (
        db.session.query(db.func.count(Attendee.id))
        .filter(Attendee.checked_in_at.isnot(None))
        .scalar()
        or 0
    )

    # Total registered headcount (sum of all families’ party_count)
    total_party_count = (
        db.session.query(db.func.coalesce(db.func.sum(Attendee.party_count), 0)).scalar()
    )

    # Total checked-in headcount (sum of actual checked_in_party_count)
    checked_in_party_count = (
        db.session.query(db.func.coalesce(db.func.sum(Attendee.checked_in_party_count), 0)).scalar()
    )

    # Optional derived metrics
    total_pending = total_attendees - total_checked_in
    pending_party_count = total_party_count - checked_in_party_count

    return render_template(
        "index.html",
        total_attendees=total_attendees,                # families registered
        total_party_count=total_party_count,            # total registered headcount
        total_checked_in=total_checked_in,              # families checked in
        checked_in_party_count=checked_in_party_count,  # headcount checked in
        total_pending=total_pending,                    # pending families
        pending_party_count=pending_party_count         # pending headcount
    )

@app.route("/scan")
def scan():
    return render_template("scan.html")

def send_checkin_email(to_email, attendee_name, checked_party_count, sweet_karam_issued=0):
    msg = EmailMessage()
    msg["Subject"] = "Diwali 2026 Check-In Confirmation"
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg.set_content(
        f"Dear {attendee_name},\n\n"
        f"We’ve successfully checked you in at Diwali 2026 with headcount {checked_party_count}.\n"
        f"Issued {sweet_karam_issued:g} Sweet-Karam.\n"
        "Happy Diwali and Enjoy the event!\n\n"
        "— Diwali Team"
    )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

#@app.route("/verify")
def verify_v1():
    qr_id = request.args.get("qr_id")
    if not qr_id:
        return jsonify({"status": "error", "message": "No QR ID provided"}), 400

    attendee = Attendee.query.filter_by(qr_id=qr_id).first()
    if not attendee:
        return jsonify({"status": "error", "message": "Invalid QR"}), 404

    if not attendee.checked_in_at:
        # remove later
        #print(f"[DEBUG] {attendee.name} checked_in_at before update:", attendee.checked_in_at)        
        attendee.checked_in_at = datetime.now()
        db.session.commit()

        # Send confirmation email (don’t block check-in if it fails)
        try:
            send_checkin_email(attendee.email, attendee.name, attendee.party_count, attendee.sweet_karam or 0)
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
    
@app.route("/verify")
def verify():
    qr_id = request.args.get("qr_id")
    if not qr_id:
        return jsonify({"status": "error", "message": "No QR ID provided"}), 400

    attendee = Attendee.query.filter_by(qr_id=qr_id).first()
    if not attendee:
        return jsonify({"status": "error", "message": "Invalid QR"}), 404

    # ✅ Do NOT modify the database here
    return jsonify({
        "status": "success",
        "name": attendee.name,
        "party_count": attendee.party_count,
        "sweet_karam": attendee.sweet_karam or 0,
        "checked_in": bool(attendee.checked_in_at),
        "checked_in_party_count": attendee.checked_in_party_count or 0,
        "checked_in_at": attendee.checked_in_at.strftime("%Y-%m-%d %H:%M:%S") if attendee.checked_in_at else None
    })
    
@app.route('/update_checkin', methods=['POST'])
def update_checkin():
    qr_id = request.args.get("qr_id")
    headcount = int(request.args.get('headcount'))

    if not qr_id:
        return jsonify({"status": "error", "message": "No QR ID provided"}), 400

    attendee = Attendee.query.filter_by(qr_id=qr_id).first()
    if not attendee:
        return jsonify({"status": "error", "message": "Invalid QR ID"}), 404

    if not attendee.checked_in_at:
        attendee.checked_in_party_count = headcount
        attendee.checked_in_at = datetime.now()
        db.session.commit()

        # Send confirmation email (don’t block check-in if it fails)
        try:
            send_checkin_email(
                attendee.email,
                attendee.name,
                attendee.checked_in_party_count,
                attendee.sweet_karam or 0,
            )
            email_status = "confirmation email sent"
        except Exception as e:
            email_status = f"email failed: {e}"

        return jsonify({
            "status": "success",
            "name": attendee.name,
            "checked_in_party_count": attendee.checked_in_party_count,
            "sweet_karam": attendee.sweet_karam or 0,
            "checked_in_at": attendee.checked_in_at.strftime("%Y-%m-%d %H:%M:%S"),
            "message": f"{attendee.name} checked in ({attendee.checked_in_party_count} in party), {email_status}"
        })
    else:
        return jsonify({
            "status": "info",
            "name": attendee.name,
            "checked_in_party_count": attendee.checked_in_party_count,
            "sweet_karam": attendee.sweet_karam or 0,
            "checked_in_at": attendee.checked_in_at.strftime("%Y-%m-%d %H:%M:%S"),
            "message": f"{attendee.name} already checked in at {attendee.checked_in_at}"
        })


@app.route("/dashboard")
def dashboard():
    attendees = Attendee.query.all()
    total_attendees = Attendee.query.count()
    checked_in_count = Attendee.query.filter(Attendee.checked_in_at.isnot(None)).count()
    total_party_count = db.session.query(db.func.sum(Attendee.party_count)).scalar() or 0
    checked_in_party_count = db.session.query(db.func.sum(Attendee.checked_in_party_count)).filter(
        Attendee.checked_in_at.isnot(None)
    ).scalar() or 0

    return render_template(
        "dashboard.html",
        attendees=attendees,
        total_attendees=total_attendees,
        checked_in_count=checked_in_count,
        total_party_count=total_party_count,
        checked_in_party_count=checked_in_party_count
    )


@app.route("/admin")
def admin():
    attendees = Attendee.query.order_by(Attendee.name.asc()).all()
    pending_email_count = Attendee.query.filter(Attendee.qr_email_sent_at.is_(None)).count()
    return render_template(
        "admin.html",
        attendees=attendees,
        pending_email_count=pending_email_count
    )

@app.route("/admin/import-csv", methods=["POST"])
def admin_import_csv():
    result = import_attendees_from_csv()
    status_code = 200 if not result["errors"] else 207
    if result["errors"] and result["imported"] == 0 and result["updated"] == 0:
        status_code = 400
    message = (
        f"Added {result['imported']} attendees; updated {result['updated']} headcounts; "
        f"skipped {result['skipped']} unchanged or blank rows."
    )
    if result["errors"]:
        message += f" {len(result['errors'])} row/file issue(s) need attention."
    if result.get("warnings"):
        message += " " + " ".join(result["warnings"])
    return jsonify({"status": "success" if result["imported"] or result["updated"] or not result["errors"] else "error",
                    "message": message, **result}), status_code


@app.route("/admin/send-bulk-qr-emails", methods=["POST"])
def admin_send_bulk_qr_emails():
    pending = (
        Attendee.query.filter(Attendee.qr_email_sent_at.is_(None))
        .order_by(Attendee.id.asc())
        .all()
    )
    if not pending:
        return jsonify({"status": "success", "sent": 0, "remaining": 0,
                        "message": "No unsent QR emails are pending. Import the CSV first if needed."})
    if not SMTP_USER or not SMTP_PASSWORD:
        return jsonify({"status": "error", "sent": 0, "remaining": len(pending),
                        "message": email_failure_message(RuntimeError())}), 400

    sent = 0
    failure = None
    for attendee in pending:
        try:
            send_attendee_qr_email(attendee)
            attendee.qr_email_sent_at = datetime.now()
            db.session.commit()
            sent += 1
        except Exception as exc:
            db.session.rollback()
            app.logger.exception("Bulk QR email failed for attendee id %s", attendee.id)
            failure = email_failure_message(exc)
            break

        if sent < len(pending):
            time.sleep(2)

    remaining = Attendee.query.filter(Attendee.qr_email_sent_at.is_(None)).count()
    if failure:
        return jsonify({
            "status": "error",
            "sent": sent,
            "remaining": remaining,
            "message": f"Sent {sent} QR email(s). Sending stopped: {failure} {remaining} remain unsent."
        }), 502

    return jsonify({
        "status": "success",
        "sent": sent,
        "remaining": remaining,
        "message": f"Bulk email complete: sent {sent} QR email(s)."
    })


@app.route("/admin/resend-qr-email/<int:attendee_id>", methods=["POST"])
def admin_resend_qr_email(attendee_id):
    attendee = db.session.get(Attendee, attendee_id)
    if attendee is None:
        return jsonify({"status": "error", "message": "Attendee not found."}), 404

    try:
        send_attendee_qr_email(attendee)
        attendee.qr_email_sent_at = datetime.now()
        db.session.commit()
        return jsonify({"status": "success", "message": f"QR email sent to {attendee.email}."})
    except Exception as exc:
        db.session.rollback()
        app.logger.exception("QR email resend failed for attendee id %s", attendee_id)
        return jsonify({"status": "error", "message": email_failure_message(exc)}), 502


@app.route("/admin_static")
def admin_static():
    return admin()

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
            "party_count": a.checked_in_party_count,
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
            "checked_in_party_count": a.checked_in_party_count,
            "checked_in_at": a.checked_in_at.strftime("%Y-%m-%d %H:%M:%S")
        } for a in attendees
    ])

@app.route("/printable_pdf")
def printable_pdf():
    attendees = Attendee.query.order_by(func.lower(Attendee.name).asc()).all()
    pdf_file = "attendees_qr.pdf"
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=A4,
        leftMargin=38,
        rightMargin=38,
        topMargin=32,
        bottomMargin=32,
    )
    elements = []
    styles = getSampleStyleSheet()

    data = [["#", "Name", "Email", "QR Code"]]

    for serial_number, attendee in enumerate(attendees, start=1):
        qr_path = os.path.join("static", "qr_codes", f"{attendee.qr_id}.png")
        if os.path.exists(qr_path):
            qr_img = Image(qr_path, width=40, height=40)
        else:
            qr_img = Paragraph("❌ Missing QR", styles["Normal"])
        data.append([
            str(serial_number),
            Paragraph(escape(attendee.name or ""), styles["Normal"]),
            Paragraph(escape(attendee.email or ""), styles["Normal"]),
            qr_img
        ])

    table = Table(data, colWidths=[30, 145, 225, 85], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    return send_file(pdf_file, as_attachment=True)


@app.route("/download_attendee_list")
def download_attendee_list():
    # ✅ Case-insensitive ASC sort
    attendees = (
        Attendee.query
        .order_by(func.lower(Attendee.name).asc())
        .all()
    )
    # ✅ Convert display names to Title Case
    for a in attendees:
        a.name = a.name.title()    
    filepath = "attendee_list.pdf"
    generate_attendee_list(attendees, filepath)
    return send_file(filepath, as_attachment=True)

# --- MAIN: all DB access inside app context ---s
if __name__ == "__main__":
    with app.app_context():
        ensure_database_schema()
        import_result = import_attendees_from_csv()
        print(
            "CSV sync complete: "
            f"{import_result['imported']} added, {import_result['updated']} headcounts updated, "
            f"{import_result['skipped']} skipped, "
            f"{len(import_result['errors'])} issue(s)."
        )
        for import_error in import_result["errors"]:
            print(f"CSV import: {import_error}")
    
    # Get port from environment variable (Render sets this automatically)
    port = int(os.environ.get('PORT', 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
