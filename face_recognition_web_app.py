"""
Face Recognition Web Application
=================================
Upload CCTV videos and identify specific people from your database.

Features:
- Upload videos via drag-and-drop
- Real-time face recognition processing
- Identify known persons (sajjad, yaseen, naveed, etc.)
- Beautiful results with person-by-person breakdown
- Download detailed reports

Author: Enhanced by AI
"""

from flask import Flask, render_template, request, jsonify, send_file, Response
import os
import json
import time
from datetime import datetime
from werkzeug.utils import secure_filename
import threading
import queue
from cctv_face_recognition_test import CCTVFaceRecognitionTest
import uuid
import config
from google_sheets_logger import FaceRecognitionSheetsLogger

app = Flask(__name__)
app.secret_key = 'face-recognition-secret-key-change-in-production'

# Configuration
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'recognition_results'
STUDENT_IMAGES_FOLDER = 'student_images'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv'}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

# Create folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Store for processing logs and results
processing_logs = {}
processing_results = {}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main upload page for face recognition"""
    return render_template('face_recognition_upload.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    """Handle video upload for face recognition"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400

        file = request.files['video']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

        # Generate unique ID
        analysis_id = str(uuid.uuid4())

        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, saved_filename)

        file.save(filepath)

        # Initialize log queue
        processing_logs[analysis_id] = queue.Queue()

        # Start processing in background
        thread = threading.Thread(
            target=process_face_recognition_background,
            args=(analysis_id, filepath, saved_filename)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'filename': saved_filename,
            'message': 'Video uploaded successfully. Starting face recognition...'
        })

    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

def process_face_recognition_background(analysis_id, video_path, filename):
    """Process video for face recognition in background"""
    log_queue = processing_logs[analysis_id]

    try:
        # Log start
        log_queue.put({
            'type': 'info',
            'message': f'🎥 Starting face recognition on: {filename}',
            'timestamp': datetime.now().isoformat()
        })

        log_queue.put({
            'type': 'info',
            'message': f'📂 Loading face database from: {STUDENT_IMAGES_FOLDER}',
            'timestamp': datetime.now().isoformat()
        })

        # Create face recognition tester with logging
        tester = LoggingCCTVFaceRecognitionTest(log_queue, STUDENT_IMAGES_FOLDER)

        log_queue.put({
            'type': 'info',
            'message': '🔍 Starting video processing...',
            'timestamp': datetime.now().isoformat()
        })

        # Test video recognition
        # Using same threshold as working Python script (0.1)
        results = tester.test_video_recognition(video_path, confidence_threshold=0.1)

        if results:
            log_queue.put({
                'type': 'success',
                'message': '✅ Face recognition completed successfully!',
                'timestamp': datetime.now().isoformat()
            })

            # Save results
            results_filename = f"recognition_{analysis_id}.json"
            results_path = os.path.join(RESULTS_FOLDER, results_filename)

            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)

            processing_results[analysis_id] = {
                'status': 'completed',
                'results': results,
                'results_file': results_filename,
                'video_file': filename
            }

            # Summary log
            stats = results['recognition_stats']
            log_queue.put({
                'type': 'success',
                'message': f"📊 Results: {stats['total_faces_recognized']} faces recognized from {stats['total_faces_detected']} detected",
                'timestamp': datetime.now().isoformat()
            })

            # ===== UPDATE GOOGLE SHEETS =====
            if config.GOOGLE_SHEETS_ENABLED:
                try:
                    log_queue.put({
                        'type': 'info',
                        'message': '📤 Updating Google Sheets...',
                        'timestamp': datetime.now().isoformat()
                    })

                    # Get recognized persons from breakdown
                    breakdown = stats.get('recognition_breakdown', {})

                    if breakdown:
                        # Prepare data: {person_name: detection_time}
                        current_time = datetime.now().strftime("%H:%M:%S")
                        recognized_persons = {}

                        for person_name in breakdown.keys():
                            recognized_persons[person_name] = current_time

                        # Initialize Google Sheets logger (Service Account - no login!)
                        logger = FaceRecognitionSheetsLogger(
                            config.SERVICE_ACCOUNT_PATH,
                            config.SPREADSHEET_ID
                        )

                        # Update sheet with today's date
                        current_date = datetime.now().strftime("%Y-%m-%d")
                        success = logger.update_attendance(current_date, recognized_persons)

                        if success:
                            log_queue.put({
                                'type': 'success',
                                'message': f'✅ Google Sheets updated for {len(recognized_persons)} person(s)',
                                'timestamp': datetime.now().isoformat()
                            })
                        else:
                            log_queue.put({
                                'type': 'warning',
                                'message': '⚠️ Google Sheets update completed with warnings',
                                'timestamp': datetime.now().isoformat()
                            })
                    else:
                        log_queue.put({
                            'type': 'info',
                            'message': 'ℹ️ No persons recognized, skipping Google Sheets update',
                            'timestamp': datetime.now().isoformat()
                        })

                except Exception as e:
                    log_queue.put({
                        'type': 'warning',
                        'message': f'⚠️ Google Sheets update failed: {str(e)}',
                        'timestamp': datetime.now().isoformat()
                    })
            # ===== END GOOGLE SHEETS UPDATE =====

            log_queue.put({
                'type': 'done',
                'message': 'Face recognition complete!',
                'timestamp': datetime.now().isoformat()
            })
        else:
            log_queue.put({
                'type': 'error',
                'message': 'Analysis failed. Please check video file.',
                'timestamp': datetime.now().isoformat()
            })

            processing_results[analysis_id] = {
                'status': 'failed',
                'error': 'Face recognition failed'
            }

    except Exception as e:
        log_queue.put({
            'type': 'error',
            'message': f'❌ Error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })

        processing_results[analysis_id] = {
            'status': 'failed',
            'error': str(e)
        }

@app.route('/logs/<analysis_id>')
def stream_logs(analysis_id):
    """Stream processing logs using Server-Sent Events"""
    def generate():
        if analysis_id not in processing_logs:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Invalid analysis ID'})}\n\n"
            return

        log_queue = processing_logs[analysis_id]

        while True:
            try:
                log_entry = log_queue.get(timeout=1)
                yield f"data: {json.dumps(log_entry)}\n\n"

                if log_entry.get('type') == 'done':
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/results/<analysis_id>')
def get_results(analysis_id):
    """Get face recognition results"""
    if analysis_id not in processing_results:
        return jsonify({'error': 'Analysis not found'}), 404

    result_data = processing_results[analysis_id]

    if result_data['status'] == 'failed':
        return jsonify({'error': result_data.get('error', 'Analysis failed')}), 500

    return jsonify(result_data)

@app.route('/view/<analysis_id>')
def view_results(analysis_id):
    """View results page"""
    return render_template('face_recognition_results.html', analysis_id=analysis_id)

@app.route('/processing/<analysis_id>')
def processing_page(analysis_id):
    """Processing logs page"""
    return render_template('processing.html', analysis_id=analysis_id)

@app.route('/download/<analysis_id>')
def download_report(analysis_id):
    """Download JSON report"""
    if analysis_id not in processing_results:
        return jsonify({'error': 'Analysis not found'}), 404

    result_data = processing_results[analysis_id]

    if result_data['status'] != 'completed':
        return jsonify({'error': 'Analysis not completed'}), 400

    results_file = result_data['results_file']
    results_path = os.path.join(RESULTS_FOLDER, results_file)

    return send_file(
        results_path,
        as_attachment=True,
        download_name=f"face_recognition_{analysis_id}.json"
    )

class LoggingCCTVFaceRecognitionTest(CCTVFaceRecognitionTest):
    """Extended Face Recognition Test with logging support"""

    def __init__(self, log_queue, student_images_folder="student_images"):
        self.log_queue = log_queue
        super().__init__(student_images_folder)

    def log(self, message, log_type='info'):
        """Send log message to queue"""
        self.log_queue.put({
            'type': log_type,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })

    def load_face_database(self):
        """Override to add logging"""
        self.log(f"📂 Loading face database from: {self.student_images_folder}")

        result = super().load_face_database()

        if result:
            db_info = self.recognition_results['database_info']
            self.log(f"✅ Loaded {db_info['faces_successfully_loaded']} known faces", 'success')
            self.log(f"👥 Known persons: {', '.join(db_info['known_persons'])}")
        else:
            self.log("❌ Failed to load face database", 'error')

        return result

    def test_video_recognition(self, video_path, confidence_threshold=0.1):
        """Override to add logging"""
        import cv2
        import numpy as np
        from collections import defaultdict

        self.log(f"🎥 Opening video: {os.path.basename(video_path)}")

        if len(self.known_names) == 0:
            self.log("❌ No faces in database. Cannot perform recognition.", 'error')
            return None

        if not os.path.exists(video_path):
            self.log(f"❌ Video file not found", 'error')
            return None

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            self.log("❌ Could not open video file", 'error')
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

        self.log(f"📊 Video: {width}x{height}, {fps:.1f} FPS, {duration:.1f}s ({frame_count} frames)")

        # Recognition tracking
        recognition_count = defaultdict(int)
        total_faces_detected = 0
        total_faces_recognized = 0
        frame_results = []

        # Sample frames
        sample_interval = max(1, frame_count // 100)
        frame_number = 0

        self.log(f"🔍 Processing frames (sampling every {sample_interval} frames)...")

        last_progress = -1
        last_recognition_log = {}

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_number % sample_interval == 0:
                result = self.recognize_faces_in_frame(frame, frame_number, confidence_threshold)

                if result:
                    frame_results.append(result)
                    total_faces_detected += result['faces_detected']

                    # Log recognitions
                    for recognition in result['recognitions']:
                        if recognition['recognized']:
                            total_faces_recognized += 1
                            name = recognition['name']
                            recognition_count[name] += 1

                            # Log new recognitions (not too frequently)
                            if name not in last_recognition_log or \
                               (frame_number - last_recognition_log[name]) > sample_interval * 10:
                                confidence_pct = recognition['confidence'] * 100
                                distance = recognition['distance']
                                self.log(f"👤 Detected: {name} (confidence: {confidence_pct:.1f}%, distance: {distance:.3f})", 'success')
                                last_recognition_log[name] = frame_number

                # Progress updates
                progress = int((frame_number / frame_count) * 100)
                if progress // 20 > last_progress // 20:  # Every 20%
                    self.log(f"⏳ Progress: {progress}% - Frame {frame_number}/{frame_count}")
                    if recognition_count:
                        summary = ", ".join([f"{name}: {count}" for name, count in recognition_count.items()])
                        self.log(f"📊 Current counts: {summary}")
                    last_progress = progress

            frame_number += 1

        cap.release()

        self.log("📊 Calculating statistics...")
        self.calculate_recognition_statistics(
            frame_results, recognition_count,
            total_faces_detected, total_faces_recognized
        )

        self.log("✅ Face recognition test completed!", 'success')

        # Final summary
        stats = self.recognition_results['recognition_stats']
        self.log(f"📈 Final Results:")
        self.log(f"   Total faces detected: {stats['total_faces_detected']}")
        self.log(f"   Faces recognized: {stats['total_faces_recognized']}")
        self.log(f"   Recognition rate: {stats['recognition_rate_percent']}%")

        if stats['recognition_breakdown']:
            self.log(f"👥 Person breakdown:")
            for name, count in stats['recognition_breakdown'].items():
                self.log(f"   - {name}: {count} times")

        return self.recognition_results

if __name__ == '__main__':
    print("🎯 Starting Face Recognition Web Application")
    print("=" * 60)
    print("📊 Access the application at:")
    print("   🖥️  Local: http://localhost:5002")
    print("   📱 Network: http://[YOUR-IP]:5002")
    print("=" * 60)
    print("👤 Upload CCTV videos to identify known persons!")
    print(f"📂 Using database from: {STUDENT_IMAGES_FOLDER}/")

    app.run(host='0.0.0.0', port=5002, debug=True, threaded=True)
