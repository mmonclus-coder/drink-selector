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

tokens = {}  # Stores token data like: {'482951': {'machine': 'DN501E', 'slots': 9, 'expires': ...}}

machine_slot_counts = {
    'DN501E': 9,
    'Summit 300': 6,
    'Royal 660': 8
}

app = Flask(__name__, template_folder='templates')



@app.route('/generate_token', methods=['POST'])
def generate_token():
    machine = request.form['machine']
    slots = machine_slot_counts.get(machine, 8)
    token = str(random.randint(100000, 999999))
    expires = datetime.now() + timedelta(hours=48)

    tokens[token] = {
        'machine': machine,
        'slots': slots,
        'expires': expires
    }

    return f"""
    <h3>✅ Token Created</h3>
    <p><strong>Token:</strong> {token}</p>
    <p><strong>Machine:</strong> {machine}</p>
    <p><strong>Slots:</strong> {slots}</p>
    <p><strong>Expires:</strong> {expires.strftime('%B %d, %Y at %I:%M %p')}</p>
    """

@app.route('/validate_token', methods=['POST'])
def validate_token():
    data = request.json
    token = data.get('token')

    if token not in tokens:
        return {'valid': False, 'message': 'Invalid token'}, 400

    token_data = tokens[token]
    if datetime.now() > token_data['expires']:
        return {'valid': False, 'message': 'Token expired'}, 400

    return {
        'valid': True,
        'machine': token_data['machine'],
        'slots': token_data['slots']
    }




@app.route('/admin')
def admin():
    print("✅ Admin route hit")
    return "<h1>Admin route is working!</h1>"




@app.route('/')
def home():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    name = data['name']
    layout = data['layout']
    submitted_at = datetime.now().strftime('%B %d, %Y at %I:%M %p')

    pdf_filename = f"{name.replace(' ', '_')}_layout.pdf"
    generate_pdf(name, layout, pdf_filename, submitted_at)

    return send_file(pdf_filename, as_attachment=True)


def generate_pdf(name, layout, filename, submitted_at):
    c = canvas.Canvas(filename, pagesize=letter)
    c.drawString(100, 750, f"Drink Layout for {name}")
    c.drawString(100, 730, f"Submitted on: {submitted_at}")
    y = 700
    for i, item in enumerate(layout):
        drink = item['name'] if item else "Empty"
        c.drawString(100, y, f"Slot {i + 1}: {drink}")
        y -= 25
    c.save()


def send_email(name, file_path):
    msg = EmailMessage()
    msg['Subject'] = f'Drink Layout - {name}'
    msg['From'] = 'mmonclus@monclusvs.com'         # Change this
    msg['To'] = 'miguelmonclus@live.com'    # Change this
    msg.set_content(f'Drink layout for {name} is attached.')

    with open(file_path, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=file_path)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('your_email@example.com', 'your_app_password')  # Replace with app password
        smtp.send_message(msg)

print("Server running. Available templates:", os.listdir("templates"))

app.run(host='0.0.0.0', port=3000, debug=True)