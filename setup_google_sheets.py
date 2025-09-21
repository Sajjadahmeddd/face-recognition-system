"""
Google Sheets Quick Setup for Face Recognition Attendance
This script helps you set up Google Sheets integration step by step
"""
import os
import json
import gspread
from google.oauth2.service_account import Credentials

def check_credentials():
    """Check if credentials.json exists and is valid"""
    if not os.path.exists('credentials.json'):
        return False, "credentials.json file not found"
    
    try:
        with open('credentials.json', 'r') as f:
            creds_data = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds_data]nah 
        
        if missing_fields:
            return False, f"Missing fields in credentials.json: {missing_fields}"
            
        return True, "Credentials file looks valid"
        
    except Exception as e:
        return False, f"Error reading credentials.json: {e}"

def test_google_sheets_connection():
    """Test connection to Google Sheets"""
    try:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
                 'https://www.googleapis.com/auth/drive']
        
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        gc = gspread.authorize(creds)
        
        # Test by trying to create a temporary sheet
        test_sheet = gc.create("Face Recognition Test")
        sheet_url = f"https://docs.google.com/spreadsheets/d/{test_sheet.id}/edit"
        
        # Clean up test sheet
        gc.del_spreadsheet(test_sheet.id)
        
        return True, f"✅ Connection successful! Test sheet created and deleted."
        
    except Exception as e:
        return False, f"❌ Connection failed: {e}"

def create_attendance_sheet():
    """Create the actual attendance Google Sheet"""
    try:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
                 'https://www.googleapis.com/auth/drive']
        
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        gc = gspread.authorize(creds)
        
        # Create the attendance sheet
        sheet_name = "Face Recognition Attendance"
        spreadsheet = gc.create(sheet_name)
        sheet = spreadsheet.sheet1
        
        # Set up headers with First Arrival and Latest Visit
        student_names = ['yaseen', 'naveed', 'hameed', 'vikinesh', 'sajjad', 'sammm', 'linguuu']
        headers = ['Date']
        
        for student in student_names:
            headers.extend([f"{student}_first", f"{student}_latest"])
        
        # Update headers
        sheet.update('A1', [headers])
        
        # Format headers
        sheet.format('A1:' + chr(64 + len(headers)) + '1', {
            "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })
        
        sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}/edit"
        
        return True, f"✅ Attendance sheet created successfully!\n🔗 URL: {sheet_url}"
        
    except Exception as e:
        return False, f"❌ Failed to create attendance sheet: {e}"

def main():
    print("🚀 Google Sheets Setup for Face Recognition Attendance")
    print("=" * 60)
    
    # Step 1: Check credentials
    print("📋 Step 1: Checking credentials...")
    creds_valid, creds_msg = check_credentials()
    print(f"   {creds_msg}")
    
    if not creds_valid:
        print("\n❌ Setup cannot continue without valid credentials.json")
        print("📖 Please follow these steps:")
        print("   1. Go to: https://console.cloud.google.com/")
        print("   2. Create a new project or select existing")
        print("   3. Enable Google Sheets API and Google Drive API")
        print("   4. Create a Service Account")
        print("   5. Download the JSON key file")
        print("   6. Rename it to 'credentials.json' and place in this folder")
        print("   7. Run this script again")
        return
    
    # Step 2: Test connection
    print("\n📡 Step 2: Testing Google Sheets connection...")
    conn_success, conn_msg = test_google_sheets_connection()
    print(f"   {conn_msg}")
    
    if not conn_success:
        print("\n❌ Connection test failed. Please check your credentials.")
        return
    
    # Step 3: Create attendance sheet
    print("\n📊 Step 3: Creating attendance Google Sheet...")
    sheet_success, sheet_msg = create_attendance_sheet()
    print(f"   {sheet_msg}")
    
    if sheet_success:
        print("\n🎉 Setup Complete!")
        print("=" * 40)
        print("✅ Google Sheets is now configured")
        print("✅ Attendance sheet created with First Arrival and Latest Visit tracking")
        print("✅ Your face recognition system will now save to Google Sheets")
        print("\n🎯 Next Steps:")
        print("   1. Run your face recognition system: python 'face recognition.py'")
        print("   2. When faces are detected, they'll be saved to Google Sheets")
        print("   3. Share the Google Sheet link with teachers/administrators")
        print("\n📱 Features you now have:")
        print("   🎯 First Arrival: Records when student first enters each day")
        print("   🔄 Latest Visit: Updates every time student is detected")
        print("   ☁️  Cloud Storage: Accessible from anywhere")
        print("   👥 Real-time Sharing: Multiple people can view simultaneously")
    else:
        print(f"\n❌ Setup failed: {sheet_msg}")

if __name__ == "__main__":
    main()