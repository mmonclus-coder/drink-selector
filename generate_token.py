import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scope to send emails with Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def main():
    creds = None
    if os.path.exists('token.json'):
        print("Token already exists.")
        return

    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    # Save the token
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

    print("✅ token.json generated successfully!")

if __name__ == '__main__':
    main()
