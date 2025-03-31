import base64
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def send_message(sender, to, subject, body, attachment_path):
    creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/gmail.send"])
    service = build('gmail', 'v1', credentials=creds)

    message = EmailMessage()
    message.set_content(body)
    message['To'] = ', '.join(to) if isinstance(to, list) else to
    message['From'] = sender
    message['Subject'] = subject

    if attachment_path:
        with open(attachment_path, 'rb') as f:
            file_data = f.read()
            file_name = attachment_path
        message.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    send_request = {
        'raw': encoded_message
    }

    try:
        send_response = service.users().messages().send(userId="me", body=send_request).execute()
        print(f"✅ Email sent. Message ID: {send_response['id']}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")

