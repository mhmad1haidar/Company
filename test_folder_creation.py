"""
Test script to create a folder in Google Drive shared drive
"""
import os
import sys
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Configuration
CREDENTIALS_PATH = "company/google_drive_credentials.json"
SHARED_DRIVE_ID = "0AEhS2Z1pFEMVUk9PVA"

def test_folder_creation():
    """Test creating a folder in the shared drive"""
    print("Loading credentials...")
    credentials = Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    
    print("Building Drive service...")
    service = build('drive', 'v3', credentials=credentials)
    
    print(f"Creating folder in shared drive: {SHARED_DRIVE_ID}")
    
    # Create folder metadata
    folder_metadata = {
        'name': 'test_folder_creation',
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [SHARED_DRIVE_ID]
    }
    
    try:
        folder = service.files().create(
            body=folder_metadata,
            fields='id',
            supportsAllDrives=True
        ).execute()
        
        print(f"SUCCESS! Folder created with ID: {folder.get('id')}")
        return True
    except Exception as e:
        print(f"FAILED! Error: {e}")
        return False

if __name__ == '__main__':
    success = test_folder_creation()
    sys.exit(0 if success else 1)
