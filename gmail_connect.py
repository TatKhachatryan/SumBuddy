from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

# Define required Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    creds = None

    # Check if token.json exists (stores access tokens to avoid re-authentication)
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid credentials, authenticate the user
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)  # Opens a browser to log in

        # Save the access token for future use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def get_gmail_service():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)
    return service

if __name__ == "__main__":
    service = get_gmail_service()
    print("✅ Gmail API authentication successful!")
