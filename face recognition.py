import cv2
import numpy as np
import csv
import time
import pandas as pd
import os
import json
from datetime import datetime
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch

# Initialize MTCNN (face detector) and Inception Resnet V1 (for face recognition)
mtcnn = MTCNN(keep_all=True)
inception = InceptionResnetV1(pretrained='vggface2').eval()

# Configuration - Use absolute paths relative to script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_ATTENDANCE_LOG = os.path.join(SCRIPT_DIR, "local_attendance.json")
STUDENT_IMAGES_FOLDER = os.path.join(SCRIPT_DIR, "student_images")  # Folder containing student images

# Set up time and attendance tracking
current_time = time.strftime("%Y-%m-%d %H-%M-%S")
detected_names = []
attendance_data = {}
# Set up time and attendance tracking (Modified to show time only as HH:MM:SS)
current_time1 = time.strftime("%H:%M:%S")  # Only hour, minute, and second
current_date = datetime.now().strftime("%Y-%m-%d")  # Current date

# Frame statistics tracking
frame_stats = {
    "people_detected": 0,
    "attendance_marked": 0,
    "unknown_people": 0
}


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

# Google Sheets functions removed - using local JSON storage only
    """Update attendance for a student with First Arrival and Latest Visit tracking"""
    # Always save locally first
    save_local_attendance_with_tracking(student_name, time_detected)
    print(f"✅ Local attendance saved successfully!")

# Google Sheets functions removed - using local JSON storage only

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
    print(f"🔍 Looking for student images at: {STUDENT_IMAGES_FOLDER}")
    print(f"🔍 Script directory: {SCRIPT_DIR}")
    print(f"🔍 Does folder exist? {os.path.exists(STUDENT_IMAGES_FOLDER)}")
    
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
        'sajjad.jpg': ('sajjad', 1134, 'IT'),
        'darun.jpg': ('darun', 1137, 'IT'),
        'iyaad.jpg': ('iyaad', 1138, 'IT'),
        'aravind.jpg': ('aravind', 1139, 'IT')
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

# Load all student faces automatically
load_all_student_faces()
# Initialize webcam
video_capture = cv2.VideoCapture(0)

# Set camera resolution to maximum (1920x1080 or whatever your camera supports)
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

# Create a normal window (will start at default size, user can maximize)
cv2.namedWindow("Video", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Video", 640, 480)  # Start with a smaller default size

while True:
    frame_start_time = time.time()  # For FPS calculation
    ret, frame = video_capture.read()
    if not ret:
        break

    # Convert BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect faces in the frame
    boxes, probs = mtcnn.detect(rgb_frame)  # Get bounding boxes and probabilities
    faces = mtcnn(rgb_frame)  # Get the actual face images

    # Reset frame statistics
    frame_stats["people_detected"] = 0
    frame_stats["attendance_marked"] = 0
    frame_stats["unknown_people"] = 0

    if boxes is not None:
        frame_stats["people_detected"] = len(boxes)
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
                if distances[min_distance_index] < 0.75:
                    name = known_face_encodings[min_distance_index][1]
                    frame_stats["attendance_marked"] += 1
                else:
                    frame_stats["unknown_people"] += 1

                # Get the bounding box coordinates
                x_min, y_min, x_max, y_max = boxes[i].tolist()

                # Draw bounding box and label
                cv2.rectangle(frame, (int(x_min), int(y_min)), (int(x_max), int(y_max)), (0, 0, 255), 2)
                cv2.putText(frame, name, (int(x_min), int(y_min) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

                # Update attendance if face is recognized
                if name != "unknown":
                    # Get current time for this detection
                    current_detection_time = datetime.now().strftime("%H:%M:%S")
                    
                    # Save attendance locally with dual tracking (First Arrival & Latest Visit)
                    save_local_attendance(name, current_detection_time)
                    
                    # Console output for every detection
                    print(f"{name} detected at {current_detection_time}")
                    
                    # Add to detected names list for session tracking
                    if name not in detected_names:
                        detected_names.append(name)
                        person_data = [entry for entry in known_face_encodings if entry[1] == name][0]
                        rrn = person_data[2]
                        branch = person_data[3]
                        attendance_data[name] = {"rrn": rrn, "branch": branch, "time": current_detection_time}

    # Add semi-transparent overlay for header
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame.shape[1], 100), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
    
    # Display header information (top left)
    cv2.putText(frame, "REAL-TIME OFFICE ATTENDANCE SYSTEM", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Time: {datetime.now().strftime('%H:%M:%S')}", 
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"Today's Attendance: {len(detected_names)}", 
                (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, f"Enrolled Employees: {len(known_face_encodings)}", 
                (450, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Display FPS in top right corner
    cv2.putText(frame, f"FPS: {int(1/(time.time() - frame_start_time + 0.0001))}", 
                (frame.shape[1] - 120, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    # Display statistics on the frame (bottom left)
    y_offset = frame.shape[0] - 100  # Start from bottom
    cv2.putText(frame, f"People Detected: {frame_stats['people_detected']}", 
                (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"Attendance Marked: {frame_stats['attendance_marked']}", 
                (10, y_offset + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, f"Unknown People: {frame_stats['unknown_people']}", 
                (10, y_offset + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # Display the resulting frame
    cv2.imshow("Video", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close OpenCV windows
video_capture.release()
cv2.destroyAllWindows()

print("Face recognition stopped. Attendance has been saved locally.")
print(f"Check '{LOCAL_ATTENDANCE_LOG}' for attendance records.")
print("Run 'python beautiful_attendance.py' to view attendance or export to Excel.")

