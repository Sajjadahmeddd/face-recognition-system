from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import cv2
import numpy as np
import base64
import json
import os
import time
from datetime import datetime
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
from PIL import Image
import io

app = FastAPI()

# Initialize models (same as face recognition.py)
print("🔄 Loading face recognition models...")
mtcnn = MTCNN(keep_all=True)
inception = InceptionResnetV1(pretrained='vggface2').eval()
print("✅ Models loaded successfully!")

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_ATTENDANCE_LOG = os.path.join(SCRIPT_DIR, "local_attendance.json")
STUDENT_IMAGES_FOLDER = os.path.join(SCRIPT_DIR, "student_images")

# Global storage for known faces
known_face_encodings = []
attendance_marked_today = set()

class Face:
    def __init__(self, name, rrn, branch, image):
        self.name = name
        self.rrn = rrn
        self.image = image
        self.branch = branch

    def face_upload(self):
        try:
            img = cv2.imread(self.image)
            if img is None:
                print(f"Image not found: {self.image}")
                return False
            
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            faces = mtcnn(img)
            if faces is not None:
                for face in faces:
                    face_embedding = inception(face.unsqueeze(0))
                    return face_embedding.detach().numpy(), self.name, self.rrn, self.branch
            return None
        except Exception as e:
            print(f"Error loading image: {e}")
            return None

def save_local_attendance_with_tracking(student_name, time_detected):
    """Save attendance locally with First Arrival and Latest Visit tracking"""
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        if os.path.exists(LOCAL_ATTENDANCE_LOG):
            with open(LOCAL_ATTENDANCE_LOG, 'r') as f:
                data = json.load(f)
        else:
            data = {}
        
        if current_date not in data:
            data[current_date] = {}
        
        if student_name not in data[current_date]:
            data[current_date][student_name] = {
                "first_arrival": time_detected,
                "latest_visit": time_detected
            }
        else:
            data[current_date][student_name]["latest_visit"] = time_detected
        
        with open(LOCAL_ATTENDANCE_LOG, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"✅ Attendance saved for {student_name} at {time_detected}")
            
    except Exception as e:
        print(f"Error saving local attendance: {e}")

def add_face(name, rrn, branch, image_filename):
    """Add a face to the recognition system"""
    image_path = os.path.join(STUDENT_IMAGES_FOLDER, image_filename)
    face = Face(name, rrn, branch, image_path)
    face_data = face.face_upload()
    if face_data:
        encoding, name, rrn, branch = face_data
        known_face_encodings.append((encoding, name, rrn, branch))
        print(f"✅ Uploaded face for {name} from {image_path}")
        return True
    else:
        print(f"❌ Failed to upload face for {name} from {image_path}")
        return False

def load_all_student_faces():
    """Load all student faces from the student_images folder"""
    print(f"📁 Loading student images from '{STUDENT_IMAGES_FOLDER}' folder...")
    
    if not os.path.exists(STUDENT_IMAGES_FOLDER):
        print(f"❌ Student images folder '{STUDENT_IMAGES_FOLDER}' not found!")
        return
    
    image_files = [f for f in os.listdir(STUDENT_IMAGES_FOLDER) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print(f"❌ No image files found in '{STUDENT_IMAGES_FOLDER}' folder!")
        return
    
    print(f"📷 Found {len(image_files)} image files")
    
    student_data = {
        'yaseen.jpg': ('yaseen', 1170, 'AI&DS'),
        'naveed.jpg': ('naveed', 1152, 'AI&DS'),
        'hameed.jpg': ('hameed', 1145, 'AI&DS'),
        'viki.jpg': ('vikinesh', 1146, 'AI&DS'),
        'sajjad.jpg': ('sajjad', 1134, 'IT'),
        'lingesh.jpg': ('linguuu', 1136, 'IT'),
        'darun.jpg': ('darun', 1137, 'IT')
    }
    
    loaded_count = 0
    for filename in image_files:
        if filename in student_data:
            name, rrn, branch = student_data[filename]
            if add_face(name, rrn, branch, filename):
                loaded_count += 1
    
    print(f"📊 Successfully loaded {loaded_count} faces out of {len(image_files)} images")

def recognize_face(face_image_data):
    """
    Recognize a face from base64 image data
    Returns the name of the recognized person or "Unknown"
    """
    try:
        # Decode base64 image
        if ',' in face_image_data:
            face_image_data = face_image_data.split(',')[1]
        
        img_bytes = base64.b64decode(face_image_data)
        img = Image.open(io.BytesIO(img_bytes))
        img_array = np.array(img)
        
        # Convert to RGB if needed
        if len(img_array.shape) == 2:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
        elif img_array.shape[2] == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        
        # Extract face embedding using MTCNN
        face_tensor = mtcnn(img_array)
        if face_tensor is None:
            return "Unknown"
        
        # Handle single face detection - mtcnn returns a tensor, get first face
        if len(face_tensor.shape) == 4 and face_tensor.shape[0] > 0:
            face_tensor = face_tensor[0]  # Get first detected face
        
        # Get embedding - add batch dimension if needed
        if len(face_tensor.shape) == 3:
            face_tensor = face_tensor.unsqueeze(0)
        
        face_embedding = inception(face_tensor)
        face_encoding = face_embedding.detach().numpy()
        
        # Compare with known faces
        min_distance = float('inf')
        recognized_name = "Unknown"
        recognized_rrn = None
        recognized_branch = None
        
        threshold = 0.8  # Similarity threshold (increased for better matching)
        
        for known_encoding, name, rrn, branch in known_face_encodings:
            # Calculate Euclidean distance
            distance = np.linalg.norm(face_encoding - known_encoding)
            
            if distance < min_distance and distance < threshold:
                min_distance = distance
                recognized_name = name
                recognized_rrn = rrn
                recognized_branch = branch
        
        # Save attendance if recognized
        if recognized_name != "Unknown":
            current_time = datetime.now().strftime("%H:%M:%S")
            attendance_key = f"{recognized_name}_{datetime.now().strftime('%Y-%m-%d')}"
            
            if attendance_key not in attendance_marked_today:
                save_local_attendance_with_tracking(recognized_name, current_time)
                attendance_marked_today.add(attendance_key)
                print(f"🎯 Recognized: {recognized_name} (RRN: {recognized_rrn}, Branch: {recognized_branch})")
        
        return recognized_name
        
    except Exception as e:
        print(f"Error in face recognition: {e}")
        return "Unknown"

# Load all student faces on startup
load_all_student_faces()

@app.get("/")
async def get():
    """Serve the main HTML page"""
    return HTMLResponse(content=open("web_interface.html", encoding="utf-8").read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🔌 WebSocket connection established")
    
    try:
        while True:
            # Receive face crop from client
            data = await websocket.receive_json()
            
            if data.get("type") == "face_crop":
                face_image = data.get("image")
                face_id = data.get("id")
                
                # Recognize the face
                recognized_name = recognize_face(face_image)
                
                # Send result back to client
                await websocket.send_json({
                    "type": "recognition_result",
                    "id": face_id,
                    "name": recognized_name
                })
    
    except WebSocketDisconnect:
        print("🔌 WebSocket connection closed")
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting web face recognition server...")
    print("📡 Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000)
