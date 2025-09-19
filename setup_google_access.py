import gspread
from google.oauth2.service_account import Credentials
import os

def setup_and_get_sheet_link():
    """Set up Google Sheets and return the shareable link"""
    
    if not os.path.exists('credentials.json'):
        print("❌ Google Sheets credentials not found!")
        print("\n📋 To access Google Sheets online:")
        print("1. Follow GOOGLE_SHEETS_SETUP.md")
        print("2. Add credentials.json file")
        print("3. Run this script again")
        print("\n🔗 Once set up, you'll get a direct link like:")
        print("   https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit")
        return None
        
    try:
        # Set up credentials
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
                 'https://www.googleapis.com/auth/drive']
        
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        gc = gspread.authorize(creds)
        
        sheet_name = "Face Recognition Attendance"
        
        try:
            # Try to open existing sheet
            spreadsheet = gc.open(sheet_name)
            print(f"✅ Found existing sheet: {sheet_name}")
        except:
            # Create new sheet
            spreadsheet = gc.create(sheet_name)
            print(f"✅ Created new sheet: {sheet_name}")
            
            # Set up headers
            student_names = ['yaseen', 'naveed', 'hameed', 'vikinesh', 'sajjad', 'sammm', 'linguuu']
            headers = ['Date'] + student_names
            spreadsheet.sheet1.update('A1:H1', [headers])
            
            # Share with anyone who has the link (view access)
            spreadsheet.share('', perm_type='anyone', role='reader')
            
        # Get the shareable link
        sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}/edit"
        
        print("\n🎉 SUCCESS! Your Google Sheet is ready!")
        print("=" * 60)
        print(f"📊 Sheet Name: {sheet_name}")
        print(f"🔗 Direct Link: {sheet_url}")
        print("=" * 60)
        
        print("\n📱 How to Access:")
        print("1. 🌐 Web Browser: Copy the link above")
        print("2. 📱 Mobile: Download Google Sheets app")
        print("3. 👥 Share: Send link to others")
        
        print("\n🔧 What You Can Do:")
        print("✅ View attendance in real-time")
        print("✅ Access from any device")
        print("✅ Share with teachers/admin")
        print("✅ Export to Excel/PDF if needed")
        print("✅ Set up notifications for updates")
        
        # Copy link to clipboard (if possible)
        try:
            import pyperclip
            pyperclip.copy(sheet_url)
            print("\n📋 Link copied to clipboard!")
        except:
            print("\n💡 Tip: Copy the link above manually")
            
        return sheet_url
        
    except Exception as e:
        print(f"❌ Error setting up Google Sheets: {e}")
        return None

def migrate_local_to_google():
    """Migrate your local attendance data to Google Sheets"""
    import json
    from datetime import datetime
    
    if not os.path.exists('credentials.json'):
        print("❌ Need Google Sheets credentials first")
        return
        
    if not os.path.exists('local_attendance.json'):
        print("❌ No local attendance data found")
        return
        
    try:
        # Set up Google Sheets
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
                 'https://www.googleapis.com/auth/drive']
        
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        gc = gspread.authorize(creds)
        spreadsheet = gc.open("Face Recognition Attendance")
        sheet = spreadsheet.sheet1
        
        # Load local data
        with open('local_attendance.json', 'r') as f:
            local_data = json.load(f)
            
        print("🔄 Migrating local data to Google Sheets...")
        
        # Get current sheet data
        all_values = sheet.get_all_values()
        headers = all_values[0] if all_values else []
        
        # Migrate each day
        for date, students in local_data.items():
            print(f"📅 Migrating {date}...")
            
            # Find or create row for this date
            date_row = None
            for i, row in enumerate(all_values):
                if len(row) > 0 and row[0] == date:
                    date_row = i + 1
                    break
                    
            if date_row is None:
                # Add new row
                date_row = len(all_values) + 1
                sheet.update(f'A{date_row}', date)
                
            # Update each student's time
            for student, time in students.items():
                if student in headers:
                    col_index = headers.index(student) + 1
                    col_letter = chr(64 + col_index)
                    sheet.update(f'{col_letter}{date_row}', time)
                    
        print("✅ Migration completed!")
        print(f"🔗 View at: https://docs.google.com/spreadsheets/d/{spreadsheet.id}/edit")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")

if __name__ == "__main__":
    print("🚀 Google Sheets Access Setup")
    print("=" * 50)
    
    link = setup_and_get_sheet_link()
    
    if link:
        migrate_choice = input("\n🔄 Migrate your local attendance data to Google Sheets? (y/n): ")
        if migrate_choice.lower() == 'y':
            migrate_local_to_google()
    
    print("\n✨ Done! Your attendance system is now cloud-ready!")
