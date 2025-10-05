"""
Configuration File for Face Recognition System
===============================================
Central configuration for Google Sheets integration and system settings

Author: AI Enhanced System
"""

# ================================
# GOOGLE SHEETS CONFIGURATION
# ================================

# Enable/Disable Google Sheets logging
GOOGLE_SHEETS_ENABLED = True

# Your Google Spreadsheet ID
# Extract from URL: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
SPREADSHEET_ID = "15ZkhaDVvaaxej9a5H_PyKNuThVkMY0G7jDy5x6D4tjo"

# Service Account credentials (fully automatic, no login required!)
SERVICE_ACCOUNT_PATH = "credentials/facerecognition-474208-d1bfaa7ad37f.json"

# ================================
# FACE RECOGNITION SETTINGS
# ================================

# Confidence threshold for face recognition (distance-based)
# Lower = stricter matching, Higher = more lenient
# Good values: 0.1 (current working value)
RECOGNITION_THRESHOLD = 0.1

# Student images folder
STUDENT_IMAGES_FOLDER = "student_images"

# ================================
# WEB APP SETTINGS
# ================================

# Upload folder for videos
UPLOAD_FOLDER = "uploads"

# Results folder for JSON reports
RESULTS_FOLDER = "recognition_results"

# Maximum upload file size (in bytes)
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

# Allowed video file extensions
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv'}

# Web app host and port
WEB_APP_HOST = '0.0.0.0'  # Accessible on network
WEB_APP_PORT = 5002

# ================================
# LOGGING SETTINGS
# ================================

# Enable debug logging
DEBUG_MODE = True

# Log file path (optional)
LOG_FILE = "face_recognition.log"
