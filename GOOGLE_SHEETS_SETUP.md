# Google Sheets Setup Guide for Face Recognition Attendance

## 🚀 Quick Setup (5 minutes)

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Sheets API and Google Drive API

### Step 2: Create Service Account
1. Go to "IAM & Admin" → "Service Accounts"
2. Click "Create Service Account"
3. Name it "face-recognition-attendance"
4. Create and download the JSON key file
5. **Save the JSON file as `credentials.json` in this folder**

### Step 3: Share Google Sheet
1. Create a new Google Sheet named "Face Recognition Attendance"
2. Share it with the service account email (from the JSON file)
3. Give "Editor" permissions

### Step 4: Update the Code
Once you have the credentials.json file, the system will automatically:
- Connect to Google Sheets
- Create/update attendance records
- Share data in real-time

## 🔧 Advanced Setup

If you want to set up the credentials properly, replace the `setup_google_sheets()` function with:

```python
def setup_google_sheets():
    try:
        creds = Credentials.from_service_account_file(
            'credentials.json', scopes=SCOPES)
        gc = gspread.authorize(creds)
        print("✅ Google Sheets connected successfully!")
        return gc
    except Exception as e:
        print(f"Google Sheets setup error: {e}")
        return None
```

## 📱 Benefits You Get:

✅ **Real-time sharing** - Anyone with access can see live attendance
✅ **Cloud backup** - Never lose data
✅ **Mobile access** - Check attendance from phone
✅ **No file conflicts** - Multiple users can access simultaneously
✅ **Professional reports** - Easy to format and export
✅ **Automatic timestamps** - Real-time updates when faces detected

## 🎯 For Testing Without Google API:

The current code will run and log attendance locally even without Google Sheets setup. You'll see messages like:
```
📝 Local log: sajjad detected at 15:30:45 (Google Sheets not configured)
```

When you're ready to use Google Sheets, just add the credentials.json file!
