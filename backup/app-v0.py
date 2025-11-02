from flask import Flask, render_template, request
import qrcode
import io
import base64
import uuid
from datetime import datetime
from flask_mail import Mail, Message
from email.mime.application import MIMEApplication
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
import os

app = Flask(__name__)

# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///attendees.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Email config
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "mahadhasal@gmail.com"  # replace
app.config["MAIL_PASSWORD"] = "zzkc zsjl ctuq czgf"     # replace
app.config["MAIL_DEFAULT_SENDER"] = "mahadhasal@gmail.com"
mail = Mail(app)

# Model
class Attendee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    qr_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    checked_in_at = db.Column(db.DateTime, nullable=True)

# QR helper
def generate_qr(qr_id):
    verify_url = f"http://localhost:5000/verify/{qr_id}"
    qr = qrcode.make(verify_url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_bytes = buffer.getvalue()
    qr_b64 = base64.b64encode(qr_bytes).decode("utf-8")
    return qr_bytes, qr_b64, verify_url

# Routes
@app.route("/")
def index():
    attendees = Attendee.query.all()
    return render_template("index-v0.html", attendees=attendees)

@app.route("/scan")
def scan():
    return render_template("scan-v1.html")

@app.route("/register", methods=["POST"])
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

@app.route("/verify/<qr_id>")
def verify(qr_id):
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

@app.route("/verify_api/<qr_id>")
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

@app.route("/admin")
def admin():
    attendees = Attendee.query.all()
    return render_template("admin-v1.html", attendees=attendees)

# Standard/static admin page
@app.route("/admin_static")
def admin_static():
    attendees = Attendee.query.all()
    return render_template("admin-v0.html", attendees=attendees)

from flask import jsonify

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


if __name__ == "__main__":
    if not os.path.exists("attendees.db"):
        with app.app_context():
            db.create_all()
    app.run(debug=True)
