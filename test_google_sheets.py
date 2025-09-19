import gspread
from google.oauth2.service_account import Credentials
import os

def test_google_sheets_connection():
    """Test if Google Sheets credentials are working"""
    
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found!")
        print("📖 Please read GOOGLE_SHEETS_SETUP.md for setup instructions")
        return False
        
    try:
        # Set up credentials
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
                 'https://www.googleapis.com/auth/drive']
        
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        gc = gspread.authorize(creds)
        
        # Test connection
        sheet_name = "Face Recognition Attendance Test"
        
        try:
            # Try to create a test sheet
            test_sheet = gc.create(sheet_name)
            test_sheet.sheet1.update('A1', 'Connection Test Successful!')
            print(f"✅ Google Sheets connection successful!")
            print(f"📊 Test sheet created: {sheet_name}")
            print(f"🔗 Access it at: https://docs.google.com/spreadsheets/d/{test_sheet.id}")
            
            # Clean up test sheet
            choice = input("Delete test sheet? (y/n): ")
            if choice.lower() == 'y':
                gc.del_spreadsheet(test_sheet.id)
                print("🗑️ Test sheet deleted")
                
        except Exception as e:
            print(f"❌ Error creating test sheet: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("📖 Please check your credentials.json file and setup")
        return False

if __name__ == "__main__":
    print("🔍 Testing Google Sheets connection...")
    print("=" * 50)
    test_google_sheets_connection()
