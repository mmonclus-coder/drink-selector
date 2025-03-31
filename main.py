from flask import Flask, render_template, request, redirect, url_for, send_file, session
import os
import random
import json
import pytz
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from gmail_auth import send_message  # Ensure this file is created correctly

app = Flask(__name__, template_folder='templates')
app.secret_key = 'something_secret_and_random'
ADMIN_PASSWORD = "1326"

TOKEN_FILE = "tokens.json"
machine_slot_counts = {
    'DN501E': 9,
    'Summit 300': 6,
    'Royal 660': 8
}

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return {}

def save_tokens(data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f)

tokens = load_tokens()

@app.route('/generate_token', methods=['POST'])
def generate_token():
    machine = request.form['machine']
    slots = machine_slot_counts.get(machine, 8)
    token = str(random.randint(100000, 999999))
    expires = datetime.now() + timedelta(hours=48)

    tokens[token] = {
        'machine': machine,
        'slots': slots,
        'expires': expires.isoformat()
    }

    save_tokens(tokens)

    return f"""
    <h3>✅ Token Created</h3>
    <p><strong>Token:</strong> {token}</p>
    <p><strong>Machine:</strong> {machine}</p>
    <p><strong>Slots:</strong> {slots}</p>
    <p><strong>Expires:</strong> {expires.strftime('%B %d, %Y at %I:%M %p')}</p>
    """

@app.route('/validate_token', methods=['POST'])
def validate_token():
    tokens = load_tokens()
    data = request.json
    token = data.get('token')

    if token not in tokens:
        return {'valid': False, 'message': 'Invalid token'}, 400

    token_data = tokens[token]
    expires = datetime.fromisoformat(token_data['expires'])

    if datetime.now() > expires:
        return {'valid': False, 'message': 'Token expired'}, 400

    return {
        'valid': True,
        'machine': token_data['machine'],
        'slots': token_data['slots']
    }

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('admin'))  # ✅ redirect to reload page in GET mode
        else:
            return render_template('admin.html', error="Incorrect password", show_form=False)

    show_form = session.get('authenticated', False)
    return render_template('admin.html', show_form=show_form)

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin'))


@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    name = data['name']
    email = data['email']
    layout = data['layout']
    eastern = pytz.timezone('US/Eastern')
    submitted_at = datetime.now(eastern).strftime('%B %d, %Y at %I:%M %p')

    pdf_filename = "Vending Machine Drink Selections.pdf"
    generate_pdf(name, layout, pdf_filename, submitted_at)
    send_email(name, email, pdf_filename)

    return redirect(url_for('thankyou'))



from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdf(name, layout, filename, submitted_at):
    from reportlab.platypus import SimpleDocTemplate
    from reportlab.lib.pagesizes import letter

    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title = Paragraph(f"<b>Vending Machine Drink Selections</b>", styles['Title'])
    customer_info = Paragraph(f"Customer Name: {name}", styles['Normal'])
    submission_time = Paragraph(f"<para alignment='right'><b>Submitted:</b> {submitted_at}</para>", styles['Normal'])

    elements.extend([title, customer_info, submission_time, Spacer(1, 20)])

    data = [["Slot", "Selection", "Image"]]  # Header row

    for i, item in enumerate(layout):
        slot_number = f"Slot {i + 1}"
        drink_name = item['name'] if item else "Empty"

        # Try to load image if available
        if item and item.get('img'):
            try:
                image_path = item['img'].replace("/static/", "static/")
                img = Image(image_path, width=50, height=50)
            except:
                img = Paragraph("Image Not Found", styles['Normal'])
        else:
            img = Paragraph("N/A", styles['Normal'])

        data.append([slot_number, drink_name, img])

    # Create table
    table = Table(data, colWidths=[80, 250, 80])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (2,1), (2,-1), 'CENTER'),  # Image column
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 8)
    ]))

    elements.append(table)
    doc.build(elements)




def send_email(name, customer_email, file_path):
    subject = "Drink Selections - Vending Machine(s)"
    body = f"""Hi {name},

Please find attached your drink selections. We will deliver one(1) case per selection along the vending machine/s that you have purchased.

Thank you for your business!

Sincerely,

Sales Team  
Monclus Vending Services LLC  
184-10 Jamaica Avenue, Jamaica, NY 11423  
347-757-7939
"""
    recipients = [customer_email, 'sales@monclusvs.com']
    send_message('sales@monclusvs.com', recipients, subject, body, file_path)

print("Server running. Available templates:", os.listdir("templates"))

app.run(host='0.0.0.0', port=3000, debug=True)
