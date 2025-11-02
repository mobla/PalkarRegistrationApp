from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import asc
import os

def generate_attendee_list(attendees, filepath="attendee_list.pdf"):
    doc = SimpleDocTemplate(filepath, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph("Diwali Attendees Family List with QR Codes", styles['Title']))
    elements.append(Spacer(1, 12))

    # Table header
    data = [["#", "Name", "Email", "QR Code"]]

    # Fill rows
    for idx, attendee in enumerate(attendees, start=1):
        qr_path = f"static/qr_codes/{attendee.qr_id}.png"
        if os.path.exists(qr_path):
            qr_img = Image(qr_path, width=20, height=20)
        else:
            qr_img = Paragraph("Missing", styles['Normal'])

        data.append([str(idx), attendee.name, attendee.email, qr_img])

    # Create table
    table = Table(data, colWidths=[20, 250, 200, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)
    return filepath