# test_drive.py
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

print("🔍 Testing Google Drive Connection...")
print("=" * 50)

try:
    # Find credentials file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    creds_path = os.path.join(current_dir, 'credentials.json')
    
    print(f"1. Looking for credentials at: {creds_path}")
    
    if not os.path.exists(creds_path):
        print("❌ ERROR: credentials.json not found!")
        print(f"   Make sure file dey for: {current_dir}")
        exit()
    
    print("✅ credentials.json found!")
    
    # Setup authentication
    print("2. Setting up authentication...")
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    credentials = service_account.Credentials.from_service_account_file(
        creds_path, scopes=SCOPES
    )
    
    print("✅ Authentication successful!")
    
    # Create Drive service
    print("3. Creating Drive service...")
    service = build('drive', 'v3', credentials=credentials)
    
    print("✅ Drive service created!")
    
    # Test connection
    print("4. Testing connection to Google Drive...")
    results = service.files().list(pageSize=5).execute()
    files = results.get('files', [])
    
    if not files:
        print("⚠️  WARNING: No files found!")
        print("   Make sure you share folder with service account")
        print(f"   Service account email: {credentials.service_account_email}")
    else:
        print(f"✅ SUCCESS! Found {len(files)} files")
        print("\nFirst 5 files:")
        for i, file in enumerate(files[:5], 1):
            print(f"   {i}. {file.get('name', 'No name')} ({file.get('id', 'No ID')})")
    
    print("\n" + "=" * 50)
    print("🎉 Google Drive API is WORKING!")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Check say credentials.json correct")
    print("2. Check say you share Drive folder with service account")
    print("3. Check internet connection")