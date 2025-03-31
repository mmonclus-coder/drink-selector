# gmail_auth.py

import os
import pickle
import base64
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = "token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def send_message(sender, to, subject, message_text, attachment_path=None):
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("No valid credentials available")

    service = build('gmail', 'v1', credentials=creds)

    message = EmailMessage()
    message.set_content(message_text)
    message['To'] = ", ".join(to) if isinstance(to, list) else to
    message['From'] = sender
    message['Subject'] = subject

    if attachment_path:
        with open(attachment_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(attachment_path)
        message.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    send_result = service.users().messages().send(
        userId='me',
        body={'raw': encoded_message}
    ).execute()

    print(f"✅ Email sent! Message ID: {send_result['id']}")
