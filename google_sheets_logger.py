"""
Google Sheets Logger for Face Recognition System
=================================================
Automatically logs face recognition results to Google Sheets

Features:
- Service Account authentication (fully automatic, no login!)
- Automatic date row management
- Person-specific column updates
- First Arrival & Latest Visit tracking

Author: AI Enhanced System
"""

import gspread
from google.oauth2 import service_account
from datetime import datetime

class FaceRecognitionSheetsLogger:
    """Logger for sending face recognition results to Google Sheets"""

    # Google Sheets API scopes
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    # Column mapping for each person (matching Google Sheet structure)
    PERSON_COLUMNS = {
        'hameed': {'first': 'B', 'latest': 'C'},
        'linguuu': {'first': 'D', 'latest': 'E'},
        'naveed': {'first': 'F', 'latest': 'G'},
        'rizwana': {'first': 'H', 'latest': 'I'},
        'sajjad': {'first': 'J', 'latest': 'K'},
        'sammm': {'first': 'L', 'latest': 'M'},
        'vikinesh': {'first': 'N', 'latest': 'O'},
        'yaseen': {'first': 'P', 'latest': 'Q'}
    }

    def __init__(self, service_account_path, spreadsheet_id):
        """
        Initialize Google Sheets logger with Service Account

        Args:
            service_account_path: Path to service_account.json
            spreadsheet_id: Google Spreadsheet ID
        """
        self.service_account_path = service_account_path
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.sheet = None

        # Authenticate and connect
        self.authenticate()

    def authenticate(self):
        """Authenticate with Google Sheets using Service Account (automatic, no login!)"""
        try:
            # Load service account credentials
            creds = service_account.Credentials.from_service_account_file(
                self.service_account_path,
                scopes=self.SCOPES
            )

            # Connect to Google Sheets
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(self.spreadsheet_id).sheet1

            print("✅ Connected to Google Sheets successfully (Service Account)")

        except FileNotFoundError:
            print(f"❌ Service account file not found: {self.service_account_path}")
            raise
        except Exception as e:
            print(f"❌ Authentication failed: {str(e)}")
            raise

    def update_attendance(self, date_str, recognized_persons):
        """
        Update Google Sheet with face recognition results

        Args:
            date_str: Date string in "YYYY-MM-DD" format (e.g., "2025-10-05")
            recognized_persons: Dictionary of {person_name: time_detected}
                Example: {
                    "sajjad": "14:32:15",
                    "yaseen": "14:32:18",
                    "naveed": "14:32:20"
                }

        Returns:
            True if successful, False otherwise
        """
        try:
            # Find or create row for this date
            row_num = self._find_or_create_date_row(date_str)

            # Update each person's columns
            updated_count = 0
            for person_name, time_detected in recognized_persons.items():
                person_lower = person_name.lower()

                if person_lower in self.PERSON_COLUMNS:
                    cols = self.PERSON_COLUMNS[person_lower]

                    # First Arrival: Only update if cell is empty
                    first_cell = f"{cols['first']}{row_num}"
                    current_first = self.sheet.acell(first_cell).value

                    if not current_first or current_first.strip() == '':
                        self.sheet.update(first_cell, [[time_detected]])
                        print(f"✅ First Arrival - {person_name}: {time_detected}")
                    else:
                        print(f"ℹ️ First Arrival exists for {person_name}: {current_first} (keeping it)")

                    # Latest Visit: Always update with new time
                    latest_cell = f"{cols['latest']}{row_num}"
                    self.sheet.update(latest_cell, [[time_detected]])
                    print(f"✅ Latest Visit - {person_name}: {time_detected}")

                    updated_count += 1
                else:
                    print(f"⚠️ Person '{person_name}' not found in column mapping, skipping")

            print(f"📊 Updated {updated_count} person(s) in Google Sheet for date: {date_str}")
            return True

        except Exception as e:
            print(f"❌ Error updating Google Sheet: {str(e)}")
            return False

    def _find_or_create_date_row(self, date_str):
        """
        Find existing row for date or create new one

        Args:
            date_str: Date string to find/create

        Returns:
            Row number (1-indexed)
        """
        # Get all dates in column A
        dates_column = self.sheet.col_values(1)  # Column A

        # Check if date already exists
        if date_str in dates_column:
            row_num = dates_column.index(date_str) + 1  # +1 for 1-based indexing
            print(f"📅 Found existing row {row_num} for date: {date_str}")
            return row_num

        # Date doesn't exist - create new row
        # Find next empty row (skip header rows 1-2)
        next_row = len(dates_column) + 1
        if next_row < 3:  # Ensure we start from row 3
            next_row = 3

        # Write date to column A
        self.sheet.update(f'A{next_row}', [[date_str]])
        print(f"📅 Created new row {next_row} for date: {date_str}")

        return next_row

    def get_all_attendance(self):
        """
        Get all attendance data from the sheet

        Returns:
            List of all rows
        """
        try:
            all_values = self.sheet.get_all_values()
            return all_values
        except Exception as e:
            print(f"❌ Error reading from Google Sheet: {str(e)}")
            return None


# Example usage
if __name__ == "__main__":
    print("🧪 Testing Google Sheets Logger (Service Account)")

    # Configuration
    SERVICE_ACCOUNT_PATH = "credentials/facerecognition-474208-d1bfaa7ad37f.json"
    SPREADSHEET_ID = "15ZkhaDVvaaxej9a5H_PyKNuThVkMY0G7jDy5x6D4tjo"

    # Test data
    test_date = datetime.now().strftime("%Y-%m-%d")
    test_persons = {
        "sajjad": datetime.now().strftime("%H:%M:%S"),
        "yaseen": datetime.now().strftime("%H:%M:%S")
    }

    print(f"📅 Test Date: {test_date}")
    print(f"👥 Test Persons: {test_persons}")

    # Create logger and update
    logger = FaceRecognitionSheetsLogger(SERVICE_ACCOUNT_PATH, SPREADSHEET_ID)
    logger.update_attendance(test_date, test_persons)

    print("\n✅ Test complete! Check your Google Sheet.")
