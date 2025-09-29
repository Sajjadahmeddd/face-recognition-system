"""
CCTV Face Recognition Database Test
==================================

This module tests whether faces in CCTV footage can be accurately recognized
against the existing student/employee database. It processes the HR's video
and attempts to identify known persons walking in the footage.

Features:
- Load existing face database from student_images folder
- Process CCTV video frame by frame
- Attempt face recognition on detected faces
- Generate recognition accuracy report
- Show confidence scores and matches

Author: Sajjad Ahmed
Version: 1.0
For: Real-world CCTV deployment validation
"""

import cv2
import numpy as np
import json
import os
from datetime import datetime
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
from PIL import Image
from collections import defaultdict

class CCTVFaceRecognitionTest:
    def __init__(self, student_images_folder="student_images"):
        """Initialize face recognition system with existing database"""
        
        self.student_images_folder = student_images_folder
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Initialize models
        self.mtcnn = MTCNN(keep_all=True, device=self.device)
        self.inception = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
        
        # Storage for known faces and results
        self.known_faces = {}
        self.known_names = []
        self.recognition_results = {
            'video_info': {},
            'database_info': {},
            'recognition_stats': {},
            'frame_results': [],
            'summary': {}
        }
        
        # Load known faces from database
        self.load_face_database()
    
    def load_face_database(self):
        """Load all known faces from student_images folder"""
        
        print(f"📂 Loading face database from: {self.student_images_folder}")
        
        if not os.path.exists(self.student_images_folder):
            print(f"❌ Student images folder not found: {self.student_images_folder}")
            return False
        
        known_encodings = []
        known_names = []
        
        # Supported image formats
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        
        image_files = []
        for file in os.listdir(self.student_images_folder):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_files.append(file)
        
        if not image_files:
            print(f"❌ No image files found in {self.student_images_folder}")
            return False
        
        print(f"📷 Found {len(image_files)} face images to process...")
        
        for image_file in image_files:
            # Extract name from filename (remove extension)
            name = os.path.splitext(image_file)[0].lower()
            image_path = os.path.join(self.student_images_folder, image_file)
            
            # Load and process image
            try:
                img = cv2.imread(image_path)
                if img is None:
                    print(f"⚠️ Could not load image: {image_file}")
                    continue
                
                # Convert BGR to RGB
                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Detect face in the image
                boxes, probs, landmarks = self.mtcnn.detect(rgb_img, landmarks=True)
                
                if boxes is not None and len(boxes) > 0:
                    # Use the first detected face
                    box = boxes[0]
                    
                    # Extract face region
                    x1, y1, x2, y2 = [int(coord) for coord in box]
                    face_region = rgb_img[y1:y2, x1:x2]
                    
                    if face_region.size > 0:
                        # Convert to PIL Image and resize
                        pil_image = Image.fromarray(face_region)
                        pil_image = pil_image.resize((160, 160))
                        
                        # Convert to tensor and get embedding
                        face_tensor = torch.tensor(np.array(pil_image)).permute(2, 0, 1).float()
                        face_tensor = face_tensor.unsqueeze(0).to(self.device)
                        face_tensor = (face_tensor - 127.5) / 128.0  # Normalize to [-1, 1]
                        
                        # Get face embedding
                        with torch.no_grad():
                            embedding = self.inception(face_tensor)
                            embedding = embedding.cpu().numpy().flatten()
                        
                        known_encodings.append(embedding)
                        known_names.append(name)
                        
                        print(f"   ✅ Loaded: {name} ({image_file})")
                    else:
                        print(f"   ⚠️ Invalid face region in: {image_file}")
                else:
                    print(f"   ❌ No face detected in: {image_file}")
            
            except Exception as e:
                print(f"   ❌ Error processing {image_file}: {str(e)}")
        
        # Store in class variables
        self.known_face_encodings = np.array(known_encodings) if known_encodings else np.array([])
        self.known_names = known_names
        
        # Update results
        self.recognition_results['database_info'] = {
            'total_images_found': len(image_files),
            'faces_successfully_loaded': len(known_names),
            'known_persons': known_names,
            'database_folder': self.student_images_folder
        }
        
        print(f"✅ Database loaded: {len(known_names)} known faces ready for recognition")
        return len(known_names) > 0
    
    def test_video_recognition(self, video_path, confidence_threshold=0.1):
        """Test face recognition on CCTV video footage"""
        
        print(f"\n🎥 Testing face recognition on: {video_path}")
        
        if len(self.known_names) == 0:
            print("❌ No faces loaded in database. Cannot perform recognition test.")
            return None
        
        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            return None
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print("❌ Error: Could not open video file")
            return None
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        self.recognition_results['video_info'] = {
            'filename': os.path.basename(video_path),
            'resolution': f"{width}x{height}",
            'fps': fps,
            'duration_seconds': round(duration, 2),
            'total_frames': frame_count
        }
        
        print(f"📊 Video: {width}x{height}, {fps} FPS, {duration:.1f}s, {frame_count} frames")
        
        # Recognition tracking
        recognition_count = defaultdict(int)
        total_faces_detected = 0
        total_faces_recognized = 0
        frame_results = []
        
        # Process every nth frame to avoid overprocessing
        sample_interval = max(1, frame_count // 100)  # Sample up to 100 frames
        frame_number = 0
        
        print(f"🔍 Processing frames for face recognition (sampling every {sample_interval} frames)...")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process sampled frames
            if frame_number % sample_interval == 0:
                result = self.recognize_faces_in_frame(frame, frame_number, confidence_threshold)
                
                if result:
                    frame_results.append(result)
                    total_faces_detected += result['faces_detected']
                    
                    # Count recognitions
                    for recognition in result['recognitions']:
                        if recognition['recognized']:
                            total_faces_recognized += 1
                            recognition_count[recognition['name']] += 1
                
                # Progress indicator
                progress = (frame_number / frame_count) * 100
                if frame_number % (sample_interval * 20) == 0:
                    print(f"   Progress: {progress:.1f}% - Frame {frame_number}")
            
            frame_number += 1
        
        cap.release()
        
        # Calculate statistics
        self.calculate_recognition_statistics(
            frame_results, recognition_count, 
            total_faces_detected, total_faces_recognized
        )
        
        print("✅ Face recognition test completed!")
        return self.recognition_results
    
    def recognize_faces_in_frame(self, frame, frame_number, confidence_threshold):
        """Recognize faces in a single frame"""
        
        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        boxes, probs, landmarks = self.mtcnn.detect(rgb_frame, landmarks=True)
        
        if boxes is None or len(boxes) == 0:
            return {
                'frame_number': frame_number,
                'faces_detected': 0,
                'recognitions': []
            }
        
        recognitions = []
        
        for i, box in enumerate(boxes):
            # Extract face region
            x1, y1, x2, y2 = [int(coord) for coord in box]
            
            # Ensure coordinates are within frame bounds
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(rgb_frame.shape[1], x2)
            y2 = min(rgb_frame.shape[0], y2)
            
            if x2 > x1 and y2 > y1:
                face_region = rgb_frame[y1:y2, x1:x2]
                
                try:
                    # Convert to PIL and resize
                    pil_image = Image.fromarray(face_region)
                    pil_image = pil_image.resize((160, 160))
                    
                    # Get embedding
                    face_tensor = torch.tensor(np.array(pil_image)).permute(2, 0, 1).float()
                    face_tensor = face_tensor.unsqueeze(0).to(self.device)
                    face_tensor = (face_tensor - 127.5) / 128.0
                    
                    with torch.no_grad():
                        embedding = self.inception(face_tensor)
                        embedding = embedding.cpu().numpy().flatten()
                    
                    # Compare with known faces
                    if len(self.known_face_encodings) > 0:
                        # Calculate distances to all known faces
                        distances = np.linalg.norm(self.known_face_encodings - embedding, axis=1)
                        min_distance_idx = np.argmin(distances)
                        min_distance = distances[min_distance_idx]
                        
                        # Convert distance to similarity score
                        similarity = max(0, 1 - min_distance)
                        
                        # Check if recognition meets confidence threshold
                        if similarity >= confidence_threshold:
                            recognized_name = self.known_names[min_distance_idx]
                            recognized = True
                        else:
                            recognized_name = "Unknown"
                            recognized = False
                        
                        recognitions.append({
                            'box': [x1, y1, x2, y2],
                            'confidence': float(similarity),
                            'distance': float(min_distance),
                            'name': recognized_name,
                            'recognized': recognized,
                            'detection_confidence': float(probs[i]) if probs is not None else 0.0
                        })
                    
                except Exception as e:
                    print(f"   ⚠️ Error processing face in frame {frame_number}: {str(e)}")
        
        return {
            'frame_number': frame_number,
            'faces_detected': len(boxes),
            'recognitions': recognitions
        }
    
    def calculate_recognition_statistics(self, frame_results, recognition_count, 
                                       total_faces_detected, total_faces_recognized):
        """Calculate comprehensive recognition statistics"""
        
        frames_processed = len(frame_results)
        frames_with_faces = sum(1 for result in frame_results if result['faces_detected'] > 0)
        frames_with_recognition = sum(1 for result in frame_results 
                                    if any(r['recognized'] for r in result['recognitions']))
        
        # Calculate recognition accuracy
        recognition_rate = (total_faces_recognized / max(total_faces_detected, 1)) * 100
        
        # Get confidence scores
        all_confidences = []
        recognized_confidences = []
        
        for result in frame_results:
            for recognition in result['recognitions']:
                all_confidences.append(recognition['confidence'])
                if recognition['recognized']:
                    recognized_confidences.append(recognition['confidence'])
        
        self.recognition_results['recognition_stats'] = {
            'frames_processed': frames_processed,
            'frames_with_faces': frames_with_faces,
            'frames_with_recognition': frames_with_recognition,
            'total_faces_detected': total_faces_detected,
            'total_faces_recognized': total_faces_recognized,
            'recognition_rate_percent': round(recognition_rate, 1),
            'unique_persons_recognized': len(recognition_count),
            'recognition_breakdown': dict(recognition_count),
            'average_confidence_all': round(np.mean(all_confidences), 3) if all_confidences else 0,
            'average_confidence_recognized': round(np.mean(recognized_confidences), 3) if recognized_confidences else 0,
            'min_confidence': round(np.min(all_confidences), 3) if all_confidences else 0,
            'max_confidence': round(np.max(all_confidences), 3) if all_confidences else 0
        }
        
        self.recognition_results['frame_results'] = frame_results
        
        # Generate summary
        self.generate_recognition_summary()
    
    def generate_recognition_summary(self):
        """Generate summary and recommendations"""
        
        stats = self.recognition_results['recognition_stats']
        
        # Overall assessment
        recognition_rate = stats['recognition_rate_percent']
        
        if recognition_rate >= 80:
            overall_status = "EXCELLENT - Ready for deployment"
            recommendation = "✅ DEPLOY: CCTV system performs excellently for face recognition attendance"
        elif recognition_rate >= 60:
            overall_status = "GOOD - Suitable for deployment"
            recommendation = "✅ DEPLOY: System performs well, minor optimizations may improve accuracy"
        elif recognition_rate >= 40:
            overall_status = "FAIR - Conditional deployment"
            recommendation = "⚠️ CONDITIONAL: System works but needs camera positioning improvements"
        else:
            overall_status = "POOR - Not recommended"
            recommendation = "❌ NOT RECOMMENDED: Significant improvements needed before deployment"
        
        self.recognition_results['summary'] = {
            'overall_status': overall_status,
            'recommendation': recommendation,
            'recognition_rate': recognition_rate,
            'database_size': len(self.known_names),
            'test_completed_at': datetime.now().isoformat()
        }
    
    def generate_report(self, output_path="cctv_recognition_test_report.json"):
        """Generate comprehensive recognition test report"""
        
        # Add metadata
        self.recognition_results['test_metadata'] = {
            'test_type': 'CCTV Face Recognition Database Test',
            'version': '1.0',
            'tested_at': datetime.now().isoformat()
        }
        
        # Save detailed JSON report
        with open(output_path, 'w') as f:
            json.dump(self.recognition_results, f, indent=2)
        
        # Print summary
        self.print_recognition_report()
        
        return output_path
    
    def print_recognition_report(self):
        """Print human-readable recognition test report"""
        
        print("\n" + "="*70)
        print("🎯 CCTV FACE RECOGNITION DATABASE TEST REPORT")
        print("="*70)
        
        # Database info
        db_info = self.recognition_results['database_info']
        print(f"\n📂 Face Database Information:")
        print(f"   Known Persons: {db_info['faces_successfully_loaded']}")
        print(f"   Names: {', '.join(db_info['known_persons'])}")
        
        # Video info
        video_info = self.recognition_results['video_info']
        print(f"\n📹 Test Video Information:")
        print(f"   File: {video_info['filename']}")
        print(f"   Resolution: {video_info['resolution']}")
        print(f"   Duration: {video_info['duration_seconds']}s")
        
        # Recognition results
        stats = self.recognition_results['recognition_stats']
        print(f"\n🎯 Recognition Test Results:")
        print(f"   Frames Processed: {stats['frames_processed']}")
        print(f"   Total Faces Detected: {stats['total_faces_detected']}")
        print(f"   Faces Successfully Recognized: {stats['total_faces_recognized']}")
        print(f"   Recognition Success Rate: {stats['recognition_rate_percent']}%")
        
        # Per-person breakdown
        if stats['recognition_breakdown']:
            print(f"\n👤 Person Recognition Breakdown:")
            for name, count in stats['recognition_breakdown'].items():
                print(f"   {name}: recognized {count} times")
        
        # Confidence scores
        print(f"\n📊 Confidence Analysis:")
        print(f"   Average Confidence (All): {stats['average_confidence_all']}")
        print(f"   Average Confidence (Recognized): {stats['average_confidence_recognized']}")
        print(f"   Confidence Range: {stats['min_confidence']} - {stats['max_confidence']}")
        
        # Summary
        summary = self.recognition_results['summary']
        print(f"\n🏆 Final Assessment:")
        print(f"   Status: {summary['overall_status']}")
        print(f"   Recommendation: {summary['recommendation']}")
        
        print("\n" + "="*70)
        print("Detailed report saved as 'cctv_recognition_test_report.json'")
        print("="*70 + "\n")

def test_cctv_face_recognition(video_path, student_images_folder="student_images"):
    """Main function to test CCTV face recognition"""
    
    tester = CCTVFaceRecognitionTest(student_images_folder)
    results = tester.test_video_recognition(video_path)
    
    if results:
        report_path = tester.generate_report()
        return results, report_path
    else:
        print("❌ Face recognition test failed")
        return None, None

if __name__ == "__main__":
    print("🎯 CCTV Face Recognition Database Test")
    print("Testing if CCTV footage can recognize known persons from database")
    
    video_path = "test_video.mp4"  # Your CCTV footage
    
    if os.path.exists(video_path):
        results, report_path = test_cctv_face_recognition(video_path)
        if results:
            print(f"\n✅ Test complete! Check {report_path} for detailed results.")
        else:
            print("❌ Test failed")
    else:
        print(f"⚠️ Video file not found: {video_path}")
        print("Please ensure your CCTV footage is in the project folder.")