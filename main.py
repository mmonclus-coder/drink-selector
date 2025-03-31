from flask import Flask, render_template, request
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import smtplib
from email.message import EmailMessage
from datetime import datetime
from flask import send_file
import random
from datetime import datetime, timedelta
import json
import pytz
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

def generate_pdf(name, layout, filename, submitted_at):
    c = canvas.Canvas(filename, pagesize=letter)

    # Title line
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 750, f"Vending Machine Drink Selections: {name}")

    # Submission time (right-aligned)
    c.setFont("Helvetica", 10)
    c.drawRightString(550, 735, f"Submitted: {submitted_at}")

    # Drink slots
    y = 700
    c.setFont("Helvetica-Bold", 12)
    for i, item in enumerate(layout):
        drink = item['name'] if item else "Empty"
        c.drawString(100, y, f"Slot {i + 1}: {drink}")
        y -= 25

    c.save()


 # Stores token data like: {'482951': {'machine': 'DN501E', 'slots': 9, 'expires': ...}}

machine_slot_counts = {
    'DN501E': 9,
    'Summit 300': 6,
    'Royal 660': 8
}

app = Flask(__name__, template_folder='templates')


TOKEN_FILE = "tokens.json"

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
        'expires': expires.isoformat()  # convert datetime to string
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
    tokens = load_tokens()  # Load latest on every request
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

from flask import Response

ADMIN_PASSWORD = "0429"  # 🔐 Set your desired password

@app.route('/admin')
def admin():
    auth = request.authorization
    if not auth or auth.password != ADMIN_PASSWORD:
        return Response(
            'Unauthorized', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'}
        )
    return render_template('admin.html')


@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')


@app.route('/')
def home():
    return render_template('index.html')


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

    return send_file(pdf_filename, as_attachment=True)



def generate_pdf(name, layout, filename, submitted_at):
    c = canvas.Canvas(filename, pagesize=letter)

    # Title line
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 750, f"Vending Machine Drink Selections: {name}")

    # Submission time (right-aligned)
    c.setFont("Helvetica", 10)
    c.drawRightString(550, 735, f"Submitted: {submitted_at}")

    # Drink slots
    y = 700
    c.setFont("Helvetica-Bold", 12)
    for i, item in enumerate(layout):
        drink = item['name'] if item else "Empty"
        c.drawString(100, y, f"Slot {i + 1}: {drink}")
        y -= 25

    c.save()


from gmail_auth import send_message  # Make sure you create this module as explained earlier

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
