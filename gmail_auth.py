# gmail_auth.py
import os
import pickle
import base64

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from email.message import EmailMessage
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send']
TOKEN_FILE = 'token.json'
CREDS_FILE = 'credentials.json'

def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service

def send_message(sender, to, subject, body_text, attachment_path=None):
    service = get_gmail_service()
    message = EmailMessage()
    message.set_content(body_text)
    message['To'] = ', '.join(to) if isinstance(to, list) else to
    message['From'] = sender
    message['Subject'] = subject

    if attachment_path:
        with open(attachment_path, 'rb') as f:
            attachment_data = f.read()
        message.add_attachment(
            attachment_data,
            maintype='application',
            subtype='pdf',
            filename=os.path.basename(attachment_path)
        )

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    send_result = service.users().messages().send(userId="me", body={'raw': raw_message}).execute()
    return send_result
