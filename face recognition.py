import cv2
import numpy as np
import csv
import time
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch

# Initialize MTCNN (face detector) and Inception Resnet V1 (for face recognition)
mtcnn = MTCNN(keep_all=True)
inception = InceptionResnetV1(pretrained='vggface2').eval()

# Set up time and attendance tracking
current_time = time.strftime("%Y-%m-%d %H-%M-%S")
detected_names = []
attendance_data = {}
# Set up time and attendance tracking (Modified to show time only as HH:MM:SS)
current_time1 = time.strftime("%H-%M-%S")  # Only hour, minute, and second


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

def add_face(name, rrn, branch, image_path):
    face = Face(name, rrn, branch, image_path)
    face_data = face.face_upload()
    if face_data:
        encoding, name, rrn, branch = face_data
        # Append the face encoding and details to the global list
        known_face_encodings.append((encoding, name, rrn, branch))
        print(f"Uploaded face for {name}")
    else:
        print(f"Failed to upload face for {name}")

add_face('yaseen', 1170, 'AI&DS', 'yaseen.jpg')
add_face('naveed', 1152, 'AI&DS', 'naveed.jpg')
add_face('hameed', 1145, 'AI&DS', 'hameed.jpg')
add_face('vikinesh',1146, 'AI&DS', 'viki.jpg')

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

                # Add name to detected names list if not already added
                if name != "unknown" and name not in detected_names:
                    detected_names.append(name)
                    if name not in attendance_data:
                        # Log first-time face detection (RRN and time)
                        person_data = [entry for entry in known_face_encodings if entry[1] == name][0]
                        rrn = person_data[2]
                        branch = person_data[3]
                        attendance_data[name] = {"rrn": rrn, "branch": branch, "time": current_time1}

    # Display the resulting frame
    cv2.imshow("Video", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    # Check if the system needs to reset after the set time interval
    #if time.time() - start_time > reset_interval:
        #print("Resetting the system...")
        # Define the file name here to avoid the NameError
file_name = f"attendance_{current_time}.csv"
        
        # Save attendance data to CSV
with open(file_name, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Name", "RRN", "Branch", "Time entered","Status"])
    for name, details in attendance_data.items():
        writer.writerow([name, details["rrn"], details["branch"], details["time"],"present"])

print(f"Attendance saved to {file_name}")
        # Reset the system
        #detected_names.clear()
        #attendance_data.clear()
        #start_time = time.time()  # Reset the timer

# Release the webcam and close OpenCV windows
video_capture.release()
cv2.destroyAllWindows()

