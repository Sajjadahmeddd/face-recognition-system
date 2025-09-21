import cv2
import numpy as np
import csv
import time
import pandas as pd
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch

# Initialize MTCNN (face detector) and Inception Resnet V1 (for face recognition)
mtcnn = MTCNN(keep_all=True)
inception = InceptionResnetV1(pretrained='vggface2').eval()

# Google Sheets configuration
GOOGLE_SHEET_NAME = "Face Recognition Attendance"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
LOCAL_ATTENDANCE_LOG = "local_attendance.json"
STUDENT_IMAGES_FOLDER = "student_images"  # Folder containing student images

# Set up time and attendance tracking
current_time = time.strftime("%Y-%m-%d %H-%M-%S")
detected_names = []
attendance_data = {}
# Set up time and attendance tracking (Modified to show time only as HH:MM:SS)
current_time1 = time.strftime("%H:%M:%S")  # Only hour, minute, and second
current_date = datetime.now().strftime("%Y-%m-%d")  # Current date for Google Sheets


# Initialize the list to store face encodings
known_face_encodings = []  # Initialize it here to avoid the NameError

# Define how much time before resetting the system
#reset_interval = 3600
#start_time = time.time()

class Face:
    def __init__(self, name, rrn, branch, image):
        self.name = name
        self.rrn = rrn
        self.image = image
        self.branch = branch

    def display_face(self):
        return f"{self.name},{self.rrn},{self.image}"

    def face_upload(self):
        try:
            # Load the image and extract face embeddings
            img = cv2.imread(self.image)
            if img is None:
                print(f"Image not found: {self.image}")
                return False
            
            # Convert BGR to RGB (OpenCV loads images in BGR format)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            faces = mtcnn(img)  # Detect faces in the image
            if faces is not None:
                for face in faces:
                    # Ensure the image is in the right format for InceptionResnetV1
                    face_embedding = inception(face.unsqueeze(0))  # Add batch dimension
                    # Return face encoding and the person's details (name, rrn, branch)
                    return face_embedding.detach().numpy(), self.name, self.rrn, self.branch
            return None
        except Exception as e:
            print(f"Error loading image: {e}")
            return None

def save_local_attendance_with_tracking(student_name, time_detected):
    """Save attendance locally with First Arrival and Latest Visit tracking"""
    try:
        # Load existing data
        if os.path.exists(LOCAL_ATTENDANCE_LOG):
            with open(LOCAL_ATTENDANCE_LOG, 'r') as f:
                data = json.load(f)
        else:
            data = {}
        
        # Initialize today's data if not exists
        if current_date not in data:
            data[current_date] = {}
        
        # Initialize student data if not exists
        if student_name not in data[current_date]:
            data[current_date][student_name] = {
                "first_arrival": time_detected,
                "latest_visit": time_detected
            }
        else:
            # Only update latest visit (keep first arrival unchanged)
            data[current_date][student_name]["latest_visit"] = time_detected
        
        # Save back
        with open(LOCAL_ATTENDANCE_LOG, 'w') as f:
            json.dump(data, f, indent=2)
            
    except Exception as e:
        print(f"Error saving local attendance: {e}")

def save_local_attendance(student_name, time_detected):
    """Legacy function - now calls the tracking version"""
    save_local_attendance_with_tracking(student_name, time_detected)

def setup_google_sheets():
    """Set up Google Sheets connection and create/initialize the attendance sheet"""
    try:
        if not os.path.exists('credentials.json'):
            print("📝 Google Sheets credentials not found. Using local storage.")
            print("💡 To enable Google Sheets: Follow GOOGLE_SHEETS_SETUP.md")
            return None
            
        # Load credentials and connect
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        gc = gspread.authorize(creds)
        print("✅ Google Sheets connected successfully!")
        return gc
        
    except Exception as e:
        print(f"⚠️ Google Sheets setup error: {e}")
        print("📝 Falling back to local storage")
        return None

def initialize_google_sheet(gc):
    """Initialize the Google Sheet with student names and First Arrival/Latest Visit columns"""
    try:
        if gc is None:
            return None
            
        # Try to open existing sheet
        try:
            sheet = gc.open(GOOGLE_SHEET_NAME).sheet1
            print(f"✅ Opened existing Google Sheet: {GOOGLE_SHEET_NAME}")
        except:
            # Create new sheet if it doesn't exist
            spreadsheet = gc.create(GOOGLE_SHEET_NAME)
            sheet = spreadsheet.sheet1
            print(f"🆕 Created new Google Sheet: {GOOGLE_SHEET_NAME}")
            
            # Set up headers with First Arrival and Latest Visit for each student
            student_names = ['yaseen', 'naveed', 'hameed', 'vikinesh', 'sajjad', 'sammm', 'linguuu']
            headers = ['Date']
            
            # Add columns for each student: First Arrival and Latest Visit
            for student in student_names:
                headers.extend([f"{student}_first", f"{student}_latest"])
            
            # Update the first row with headers
            sheet.update('A1', [headers])
            
            # Format headers for better readability
            sheet.format('A1:' + chr(64 + len(headers)) + '1', {
                "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
                "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
            })
            
            print(f"📊 Sheet structure: Date + {len(student_names)} students × 2 columns (First/Latest)")
            
        return sheet
    except Exception as e:
        print(f"❌ Error initializing Google Sheet: {e}")
        return None

def update_google_sheet_attendance(sheet, student_name, time_detected):
    """Update attendance for a student with First Arrival and Latest Visit tracking"""
    # Always save locally first
    save_local_attendance_with_tracking(student_name, time_detected)
    
    try:
        if sheet is None:
            print(f"📝 Local log: {student_name} detected at {time_detected} (Google Sheets not configured)")
            print(f"💾 Saved to local file: {LOCAL_ATTENDANCE_LOG}")
            return
            
        # Get all values to find today's row
        all_values = sheet.get_all_values()
        headers = all_values[0] if all_values else []
        
        # Find student columns (first arrival and latest visit)
        first_col_name = f"{student_name}_first"
        latest_col_name = f"{student_name}_latest"
        
        if first_col_name not in headers or latest_col_name not in headers:
            print(f"❌ Student columns not found for {student_name}")
            return
            
        first_col = headers.index(first_col_name) + 1  # +1 for 1-based indexing
        latest_col = headers.index(latest_col_name) + 1
        
        # Find today's row or create it
        today_row = None
        existing_first_arrival = None
        
        for i, row in enumerate(all_values):
            if len(row) > 0 and row[0] == current_date:
                today_row = i + 1  # +1 for 1-based indexing
                # Check if this student already has a first arrival time
                if len(row) >= first_col:
                    existing_first_arrival = row[first_col - 1]  # -1 for 0-based indexing
                break
                
        if today_row is None:
            # Add new row for today
            today_row = len(all_values) + 1
            sheet.update(f'A{today_row}', current_date)
            
        # Update First Arrival (only if empty)
        first_col_letter = chr(64 + first_col)
        if not existing_first_arrival or existing_first_arrival.strip() == "":
            sheet.update(f'{first_col_letter}{today_row}', time_detected)
            print(f"🎯 First Arrival: {student_name} at {time_detected}")
        else:
            print(f"⏰ First Arrival already recorded: {student_name} at {existing_first_arrival}")
            
        # Always update Latest Visit
        latest_col_letter = chr(64 + latest_col)
        sheet.update(f'{latest_col_letter}{today_row}', time_detected)
        print(f"🔄 Latest Visit: {student_name} at {time_detected}")
        
        print(f"✅ Google Sheets updated successfully!")
        
    except Exception as e:
        print(f"Error updating Google Sheets: {e}")
        print(f"📝 Local log: {student_name} detected at {time_detected}")

def get_today_google_attendance(sheet, student_name):
    """Check if student has already been marked present today in Google Sheets"""
    try:
        if sheet is None:
            return None
            
        all_values = sheet.get_all_values()
        headers = all_values[0] if all_values else []
        
        if student_name not in headers:
            return None
            
        student_col = headers.index(student_name)
        
        for row in all_values:
            if len(row) > 0 and row[0] == current_date:
                return row[student_col] if student_col < len(row) else None
                
        return None
    except:
        return None

def add_face(name, rrn, branch, image_filename):
    """Add a face to the recognition system - now uses student_images folder"""
    image_path = os.path.join(STUDENT_IMAGES_FOLDER, image_filename)
    face = Face(name, rrn, branch, image_path)
    face_data = face.face_upload()
    if face_data:
        encoding, name, rrn, branch = face_data
        # Append the face encoding and details to the global list
        known_face_encodings.append((encoding, name, rrn, branch))
        print(f"✅ Uploaded face for {name} from {image_path}")
    else:
        print(f"❌ Failed to upload face for {name} from {image_path}")

def load_all_student_faces():
    """Automatically load all student faces from the student_images folder"""
    if not os.path.exists(STUDENT_IMAGES_FOLDER):
        print(f"❌ Student images folder '{STUDENT_IMAGES_FOLDER}' not found!")
        return
    
    print(f"📁 Loading student images from '{STUDENT_IMAGES_FOLDER}' folder...")
    
    # Get all image files in the folder
    image_files = [f for f in os.listdir(STUDENT_IMAGES_FOLDER) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print(f"❌ No image files found in '{STUDENT_IMAGES_FOLDER}' folder!")
        return
    
    print(f"📷 Found {len(image_files)} image files: {image_files}")
    
    # For now, load the known students manually (you can modify this)
    student_data = {
        'yaseen.jpg': ('yaseen', 1170, 'AI&DS'),
        'naveed.jpg': ('naveed', 1152, 'AI&DS'),
        'hameed.jpg': ('hameed', 1145, 'AI&DS'),
        'viki.jpg': ('vikinesh', 1146, 'AI&DS'),
        'sajjad.jpg': ('sajjad', 1134, 'IT'),
        'samgr.jpg': ('sammm', 1136, 'IT'),
        'lingesh.jpg': ('linguuu', 1136, 'IT'),
        'rizwana.jpg': ('rizwana', 1137, 'IT'),
        'sam_white.jpg': ('sammm', 1138, 'IT')
    }
    
    # Load each student's face
    loaded_count = 0
    for filename in image_files:
        if filename in student_data:
            name, rrn, branch = student_data[filename]
            add_face(name, rrn, branch, filename)
            loaded_count += 1
        else:
            print(f"⚠️  Unknown student image: {filename} (add to student_data dict)")
    
    print(f"📊 Successfully loaded {loaded_count} faces out of {len(image_files)} images")

# Initialize Google Sheets connection
gc = setup_google_sheets()
sheet = initialize_google_sheet(gc)

# Load all student faces automatically
load_all_student_faces()
# Initialize webcam
video_capture = cv2.VideoCapture(0)

while True:
    ret, frame = video_capture.read()
    if not ret:
        break

    # Convert BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect faces in the frame
    boxes, probs = mtcnn.detect(rgb_frame)  # Get bounding boxes and probabilities
    faces = mtcnn(rgb_frame)  # Get the actual face images

    if boxes is not None:
        # Process each detected face
        for i, face in enumerate(faces):
            if face is not None:
                # Ensure the image is in the right format for InceptionResnetV1
                face_embedding = inception(face.unsqueeze(0))  # Add batch dimension

                # Calculate the distances between the detected face and known faces
                distances = [np.linalg.norm(face_embedding.detach().numpy() - encoding) for encoding, _, _, _ in known_face_encodings]
                min_distance_index = np.argmin(distances)
                name = "unknown"

                # If the distance is small enough, it's a match
                if distances[min_distance_index] < 0.9:
                    name = known_face_encodings[min_distance_index][1]

                # Get the bounding box coordinates
                x_min, y_min, x_max, y_max = boxes[i].tolist()

                # Draw bounding box and label
                cv2.rectangle(frame, (int(x_min), int(y_min)), (int(x_max), int(y_max)), (0, 0, 255), 2)
                cv2.putText(frame, name, (int(x_min), int(y_min) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

                # Update Excel attendance if face is recognized
                if name != "unknown":
                    # Get current time for this detection
                    current_detection_time = datetime.now().strftime("%H:%M:%S")
                    
                    # Update Google Sheets attendance (this will overwrite previous time for same day)
                    update_google_sheet_attendance(sheet, name, current_detection_time)
                    
                    # Add to detected names list if not already added for console display
                    if name not in detected_names:
                        detected_names.append(name)
                        person_data = [entry for entry in known_face_encodings if entry[1] == name][0]
                        rrn = person_data[2]
                        branch = person_data[3]
                        attendance_data[name] = {"rrn": rrn, "branch": branch, "time": current_detection_time}
                        print(f"{name} detected and attendance updated at {current_detection_time}")

    # Display the resulting frame
    cv2.imshow("Video", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close OpenCV windows
video_capture.release()
cv2.destroyAllWindows()

print("Face recognition stopped. Attendance has been saved to Google Sheets.")
print(f"Check '{GOOGLE_SHEET_NAME}' Google Sheet for attendance records.")

