from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import base64
import json
import os
import time
from datetime import datetime
from insightface.app import FaceAnalysis
from PIL import Image
import io

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize models (SCRFD + ArcFace)
print("🔄 Loading face recognition models...")
face_app = FaceAnalysis(providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0, det_size=(320, 320), det_thresh=0.3)  # Smaller det_size and lower threshold for better detection
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
                return None
            
            # InsightFace works with BGR images directly
            faces = face_app.get(img)
            if faces and len(faces) > 0:
                face_embedding = faces[0].embedding
                return face_embedding, self.name, self.rrn, self.branch
            print(f"No face detected in: {self.image}")
            return None
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"Error loading image {self.image}: {e}")
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
        'yaseen.jpg': ('yaseen', 104, 'INTERN'),
        'sajjad.jpg': ('sajjad', 105, 'INTERN'),
        'darun.jpg': ('darun', 106, 'INTERN'),
        'iyaad.jpg': ('iyaad', 103, 'INTERN'),
        'aravind.jpg': ('aravind', 102, 'DEVELOPER')
    }
    
    loaded_count = 0
    for filename in image_files:
        if filename in student_data:
            name, rrn, branch = student_data[filename]
            try:
                if add_face(name, rrn, branch, filename):
                    loaded_count += 1
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"⚠️ Failed to load {filename}: {e}")
                continue
    
    print(f"📊 Successfully loaded {loaded_count} faces out of {len(image_files)} images")

def recognize_face(face_image_data, face_id=None):
    """
    Recognize a face from base64 image data
    Returns the name of the recognized person or "Unknown"
    Uses face tracking to maintain consistency across frames
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
            img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
        elif img_array.shape[2] == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
        elif img_array.shape[2] == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Extract ALL faces from the frame using InsightFace
        faces = face_app.get(img_array)
        if not faces or len(faces) == 0:
            # Clean up cache for this face_id since no face detected
            if face_id is not None and face_id in face_tracking_cache:
                del face_tracking_cache[face_id]
            print("⚠️  No face detected in frame")
            return "Unknown"
        
        threshold = 0.55  # ArcFace threshold (stricter to prevent false positives)
        
        # Recognize ALL detected faces first to build a complete picture
        detected_faces = []
        for idx, face in enumerate(faces):
            face_encoding = face.embedding
            bbox = face.bbox
            
            # Validate embedding
            if face_encoding is None or len(face_encoding) == 0 or np.linalg.norm(face_encoding) == 0:
                print(f"⚠️  Face {idx}: Invalid embedding (skipping)")
                continue
            
            best_name = "Unknown"
            best_distance = float('inf')
            best_rrn = None
            best_branch = None
            
            # Store all distances for debugging
            all_distances = []
            
            # Compare with known faces
            for known_encoding, name, rrn, branch in known_face_encodings:
                similarity = np.dot(face_encoding, known_encoding) / (
                    np.linalg.norm(face_encoding) * np.linalg.norm(known_encoding)
                )
                distance = 1 - similarity
                all_distances.append((name, distance))
                
                if distance < best_distance and distance < threshold:
                    best_distance = distance
                    best_name = name
                    best_rrn = rrn
                    best_branch = branch
            
            # Debug: Log the best match for this face
            if best_name != "Unknown":
                print(f"✓ Face {idx}: {best_name} (distance: {best_distance:.3f})")
            else:
                # Show top 3 closest matches to help diagnose
                all_distances.sort(key=lambda x: x[1])
                top_3 = all_distances[:3]
                top_3_str = ", ".join([f"{name}: {dist:.3f}" for name, dist in top_3])
                print(f"✗ Face {idx}: Unknown (closest: {top_3_str}, threshold: {threshold})")
            
            detected_faces.append({
                "index": idx,
                "name": best_name,
                "distance": best_distance,
                "rrn": best_rrn,
                "branch": best_branch,
                "bbox": bbox,
                "center_x": (bbox[0] + bbox[2]) / 2
            })
        
        # Sort by horizontal position (left to right)
        detected_faces.sort(key=lambda x: x["center_x"])
        
        # Match face_id to the correct detected face
        if face_id is not None and isinstance(face_id, int):
            # Use spatial ordering: face_id 0 = leftmost, 1 = second from left, etc.
            if face_id < len(detected_faces):
                matched_face = detected_faces[face_id]
                recognized_name = matched_face["name"]
                recognized_rrn = matched_face["rrn"]
                recognized_branch = matched_face["branch"]
                min_distance = matched_face["distance"]
                
                # Update cache
                face_tracking_cache[face_id] = {
                    "name": recognized_name,
                    "last_seen": datetime.now(),
                    "bbox": matched_face["bbox"]
                }
            else:
                # face_id out of range - use first detected face
                matched_face = detected_faces[0]
                recognized_name = matched_face["name"]
                recognized_rrn = matched_face["rrn"]
                recognized_branch = matched_face["branch"]
                min_distance = matched_face["distance"]
        else:
            # No face_id provided, use first detected face
            matched_face = detected_faces[0]
            recognized_name = matched_face["name"]
            recognized_rrn = matched_face["rrn"]
            recognized_branch = matched_face["branch"]
            min_distance = matched_face["distance"]
        
        # Save attendance if recognized
        if recognized_name != "Unknown":
            current_time = datetime.now().strftime("%H:%M:%S")
            attendance_key = f"{recognized_name}_{datetime.now().strftime('%Y-%m-%d')}"
            
            if attendance_key not in attendance_marked_today:
                save_local_attendance_with_tracking(recognized_name, current_time)
                attendance_marked_today.add(attendance_key)
                print(f"✅ {recognized_name} recognized (distance: {min_distance:.3f})")
        
        return recognized_name
        
    except Exception as e:
        print(f"Error in face recognition: {e}")
        return "Unknown"

# Cache for face tracking across frames (helps with consistency)
face_tracking_cache = {}  # {face_id: {"name": str, "last_seen": timestamp, "bbox": [x,y,w,h]}}
from datetime import datetime, timedelta

# Load all student faces on startup
load_all_student_faces()

@app.get("/")
async def get():
    """Serve the main HTML page with no-cache headers"""
    from fastapi.responses import Response
    content = open("web_interface.html", encoding="utf-8").read()
    return Response(
        content=content,
        media_type="text/html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.post("/recognize")
async def recognize_endpoint(request: Request):
    """HTTP endpoint for face recognition (single face crop)"""
    try:
        data = await request.json()
        face_image = data.get("image")
        face_id = data.get("id")
        
        if not face_image:
            return JSONResponse(
                status_code=400,
                content={"error": "No image provided"}
            )
        
        # Recognize the face with face_id for multi-face scenarios
        recognized_name = recognize_face(face_image, face_id)
        
        # Return result
        return JSONResponse(content={
            "id": face_id,
            "name": recognized_name,
            "success": True
        })
    
    except Exception as e:
        print(f"Error in recognize endpoint: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/recognize_frame")
async def recognize_frame_endpoint(request: Request):
    """HTTP endpoint for recognizing all faces in a full frame"""
    try:
        data = await request.json()
        frame_image = data.get("image")
        num_faces = data.get("num_faces", 0)
        
        if not frame_image:
            return JSONResponse(
                status_code=400,
                content={"error": "No image provided"}
            )
        
        # Decode base64 image (optimized)
        if ',' in frame_image:
            frame_image = frame_image.split(',')[1]
        
        img_bytes = base64.b64decode(frame_image)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img_array = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # Direct BGR decode
        
        if img_array is None:
            # Fallback to PIL if cv2 decode fails
            img = Image.open(io.BytesIO(img_bytes))
            img_array = np.array(img)
            if len(img_array.shape) == 2:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
            elif img_array.shape[2] == 4:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
            elif img_array.shape[2] == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Detect all faces
        faces = face_app.get(img_array)
        
        if not faces or len(faces) == 0:
            return JSONResponse(content={
                "success": True,
                "faces": []
            })
        
        threshold = 0.55
        detected_faces = []
        
        # Process each face
        for idx, face in enumerate(faces):
            face_encoding = face.embedding
            bbox = face.bbox
            
            # Validate embedding
            if face_encoding is None or len(face_encoding) == 0 or np.linalg.norm(face_encoding) == 0:
                continue
            
            best_name = "Unknown"
            best_distance = float('inf')
            best_rrn = None
            best_branch = None
            all_distances = []
            
            # Compare with known faces
            for known_encoding, name, rrn, branch in known_face_encodings:
                similarity = np.dot(face_encoding, known_encoding) / (
                    np.linalg.norm(face_encoding) * np.linalg.norm(known_encoding)
                )
                distance = 1 - similarity
                all_distances.append((name, distance))
                
                if distance < best_distance and distance < threshold:
                    best_distance = distance
                    best_name = name
                    best_rrn = rrn
                    best_branch = branch
            
            # Log recognition
            if best_name != "Unknown":
                print(f"✓ Face {idx}: {best_name} (distance: {best_distance:.3f})")
            else:
                all_distances.sort(key=lambda x: x[1])
                top_3 = all_distances[:3]
                top_3_str = ", ".join([f"{name}: {dist:.3f}" for name, dist in top_3])
                print(f"✗ Face {idx}: Unknown (closest: {top_3_str}, threshold: {threshold})")
            
            detected_faces.append({
                "index": idx,
                "name": best_name,
                "distance": best_distance,
                "rrn": best_rrn,
                "branch": best_branch,
                "bbox": bbox.tolist(),
                "center_x": (bbox[0] + bbox[2]) / 2
            })
        
        # Sort faces left to right
        detected_faces.sort(key=lambda x: x["center_x"])
        
        # Save attendance for recognized faces
        current_time = datetime.now().strftime("%H:%M:%S")
        for face in detected_faces:
            if face["name"] != "Unknown":
                attendance_key = f"{face['name']}_{datetime.now().strftime('%Y-%m-%d')}"
                if attendance_key not in attendance_marked_today:
                    save_local_attendance_with_tracking(face["name"], current_time)
                    attendance_marked_today.add(attendance_key)
                    print(f"✅ Attendance saved for {face['name']} at {current_time}")
        
        # Return all faces with their indices and bounding boxes
        # Convert numpy/inf/nan values to JSON-safe values
        import math
        return JSONResponse(content={
            "success": True,
            "faces": [{"index": i, 
                      "name": face["name"], 
                      "id": face["rrn"],
                      "branch": face["branch"],
                      "distance": face["distance"] if not (math.isnan(face["distance"]) or math.isinf(face["distance"])) else 999.0,
                      "bbox": face["bbox"]} 
                     for i, face in enumerate(detected_faces)]
        })
    
    except Exception as e:
        print(f"Recognition error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "success": False}
        )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting web face recognition server...")
    print("📡 Open http://localhost:9991 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=9991)
