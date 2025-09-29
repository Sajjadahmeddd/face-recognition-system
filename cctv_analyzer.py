"""
CCTV Video Analyzer for Face Recognition Compatibility
=====================================================

This module analyzes CCTV footage to determine if the camera quality 
is sufficient for reliable face recognition in institutional settings.

Features:
- Video quality assessment
- Face detection confidence analysis
- Lighting and clarity evaluation
- Professional compatibility report generation

Author: Sajjad Ahmed
Version: 1.0
For: Institutional CCTV Integration Assessment
"""

import cv2
import numpy as np
import json
import os
from datetime import datetime
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
from collections import defaultdict

class CCTVAnalyzer:
    def __init__(self):
        # Initialize face detection models
        self.mtcnn = MTCNN(keep_all=True, device='cpu')
        self.inception = InceptionResnetV1(pretrained='vggface2').eval()
        
        # Analysis results storage
        self.analysis_results = {
            'video_info': {},
            'quality_metrics': {},
            'face_detection_stats': {},
            'compatibility_score': 0,
            'recommendations': []
        }
    
    def analyze_video_quality(self, video_path):
        """Comprehensive video quality analysis for CCTV footage"""
        print(f"🎥 Analyzing CCTV footage: {video_path}")
        
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
        
        self.analysis_results['video_info'] = {
            'filename': os.path.basename(video_path),
            'resolution': f"{width}x{height}",
            'fps': fps,
            'duration_seconds': round(duration, 2),
            'total_frames': frame_count
        }
        
        print(f"📊 Video Info: {width}x{height}, {fps} FPS, {duration:.1f}s")
        
        # Analysis variables
        frame_analyses = []
        face_detection_results = []
        brightness_levels = []
        sharpness_scores = []
        
        # Sample frames for analysis (every 30 frames to avoid overprocessing)
        sample_interval = max(1, frame_count // 50)  # Analyze up to 50 frames
        frame_number = 0
        
        print("🔍 Processing frames for quality analysis...")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every nth frame
            if frame_number % sample_interval == 0:
                analysis = self.analyze_frame(frame, frame_number)
                frame_analyses.append(analysis)
                
                # Collect metrics
                brightness_levels.append(analysis['brightness'])
                sharpness_scores.append(analysis['sharpness'])
                face_detection_results.append(analysis['faces_detected'])
                
                # Progress indicator
                progress = (frame_number / frame_count) * 100
                if frame_number % (sample_interval * 10) == 0:
                    print(f"   Progress: {progress:.1f}% - Frame {frame_number}")
            
            frame_number += 1
        
        cap.release()
        
        # Calculate overall metrics
        self.calculate_quality_metrics(brightness_levels, sharpness_scores, face_detection_results, frame_analyses)
        
        # Generate compatibility score and recommendations
        self.generate_compatibility_assessment()
        
        print("✅ Video analysis completed!")
        return self.analysis_results
    
    def analyze_frame(self, frame, frame_number):
        """Analyze individual frame for quality metrics"""
        
        # Convert to RGB for face detection
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Face detection
        boxes, probs, landmarks = self.mtcnn.detect(rgb_frame, landmarks=True)
        faces_detected = 0 if boxes is None else len(boxes)
        
        # Quality metrics
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Brightness (average pixel intensity)
        brightness = np.mean(gray)
        
        # Sharpness (Laplacian variance)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Contrast (standard deviation of pixel intensities)
        contrast = np.std(gray)
        
        # Face detection confidence
        avg_confidence = 0
        if probs is not None and len(probs) > 0:
            # Filter out None values and convert to numpy array
            valid_probs = [p for p in probs if p is not None]
            if valid_probs:
                avg_confidence = np.mean(valid_probs)
        
        return {
            'frame_number': frame_number,
            'faces_detected': faces_detected,
            'brightness': brightness,
            'sharpness': sharpness,
            'contrast': contrast,
            'face_confidence': avg_confidence,
            'boxes': boxes.tolist() if boxes is not None else [],
            'landmarks': landmarks.tolist() if landmarks is not None else []
        }
    
    def calculate_quality_metrics(self, brightness_levels, sharpness_scores, face_detections, frame_analyses):
        """Calculate overall quality metrics from frame analyses"""
        
        total_frames = len(frame_analyses)
        frames_with_faces = sum(1 for f in face_detections if f > 0)
        
        self.analysis_results['quality_metrics'] = {
            'average_brightness': round(np.mean(brightness_levels), 2),
            'brightness_consistency': round(np.std(brightness_levels), 2),
            'average_sharpness': round(np.mean(sharpness_scores), 2),
            'sharpness_consistency': round(np.std(sharpness_scores), 2),
            'total_faces_detected': sum(face_detections),
            'frames_with_faces': frames_with_faces,
            'face_detection_rate': round((frames_with_faces / total_frames) * 100, 1) if total_frames > 0 else 0,
            'frames_analyzed': total_frames
        }
        
        # Face detection statistics
        confidences = [f['face_confidence'] for f in frame_analyses if f['face_confidence'] > 0]
        
        self.analysis_results['face_detection_stats'] = {
            'frames_analyzed': total_frames,
            'frames_with_faces': frames_with_faces,
            'detection_success_rate': round((frames_with_faces / total_frames) * 100, 1),
            'average_confidence': round(np.mean(confidences), 3) if confidences else 0,
            'min_confidence': round(np.min(confidences), 3) if confidences else 0,
            'max_confidence': round(np.max(confidences), 3) if confidences else 0
        }
    
    def generate_compatibility_assessment(self):
        """Generate compatibility score and recommendations"""
        
        metrics = self.analysis_results['quality_metrics']
        face_stats = self.analysis_results['face_detection_stats']
        
        # Scoring criteria (0-100 scale)
        scores = {
            'resolution': self.score_resolution(),
            'brightness': self.score_brightness(metrics['average_brightness']),
            'sharpness': self.score_sharpness(metrics['average_sharpness']),
            'face_detection': self.score_face_detection(face_stats['detection_success_rate']),
            'consistency': self.score_consistency(metrics['brightness_consistency'], metrics['sharpness_consistency'])
        }
        
        # Overall compatibility score (weighted average)
        weights = {
            'resolution': 0.2,
            'brightness': 0.2,
            'sharpness': 0.25,
            'face_detection': 0.25,
            'consistency': 0.1
        }
        
        compatibility_score = sum(scores[key] * weights[key] for key in scores)
        
        self.analysis_results['compatibility_score'] = round(compatibility_score, 1)
        self.analysis_results['detailed_scores'] = scores
        
        # Generate recommendations
        self.generate_recommendations(scores, metrics, face_stats)
    
    def score_resolution(self):
        """Score based on video resolution"""
        width, height = map(int, self.analysis_results['video_info']['resolution'].split('x'))
        total_pixels = width * height
        
        if total_pixels >= 1920 * 1080:  # Full HD or higher
            return 100
        elif total_pixels >= 1280 * 720:  # HD
            return 85
        elif total_pixels >= 854 * 480:   # 480p
            return 70
        elif total_pixels >= 640 * 480:   # VGA
            return 55
        else:
            return 30
    
    def score_brightness(self, brightness):
        """Score based on brightness levels (0-255 scale)"""
        if 80 <= brightness <= 180:  # Optimal range
            return 100
        elif 60 <= brightness <= 200:  # Good range
            return 80
        elif 40 <= brightness <= 220:  # Acceptable range
            return 60
        else:
            return 30
    
    def score_sharpness(self, sharpness):
        """Score based on sharpness (higher is better)"""
        if sharpness >= 500:
            return 100
        elif sharpness >= 200:
            return 80
        elif sharpness >= 100:
            return 60
        elif sharpness >= 50:
            return 40
        else:
            return 20
    
    def score_face_detection(self, detection_rate):
        """Score based on face detection success rate"""
        if detection_rate >= 80:
            return 100
        elif detection_rate >= 60:
            return 75
        elif detection_rate >= 40:
            return 50
        elif detection_rate >= 20:
            return 25
        else:
            return 0
    
    def score_consistency(self, brightness_std, sharpness_std):
        """Score based on consistency of quality metrics"""
        brightness_score = 100 if brightness_std <= 10 else max(0, 100 - brightness_std * 2)
        sharpness_score = 100 if sharpness_std <= 50 else max(0, 100 - sharpness_std * 0.5)
        return (brightness_score + sharpness_score) / 2
    
    def generate_recommendations(self, scores, metrics, face_stats):
        """Generate actionable recommendations for CCTV system"""
        
        recommendations = []
        
        # Resolution recommendations
        if scores['resolution'] < 70:
            recommendations.append({
                'category': 'Hardware',
                'priority': 'High',
                'issue': 'Low Resolution',
                'recommendation': 'Upgrade to HD (1280x720) or Full HD (1920x1080) cameras for better face recognition accuracy.',
                'impact': 'Improved face detection and recognition reliability'
            })
        
        # Brightness recommendations
        if scores['brightness'] < 60:
            if metrics['average_brightness'] < 60:
                recommendations.append({
                    'category': 'Environment',
                    'priority': 'Medium',
                    'issue': 'Poor Lighting',
                    'recommendation': 'Install additional lighting or use cameras with better low-light performance.',
                    'impact': 'Better face visibility and detection accuracy'
                })
            elif metrics['average_brightness'] > 200:
                recommendations.append({
                    'category': 'Environment',
                    'priority': 'Medium',
                    'issue': 'Overexposure',
                    'recommendation': 'Adjust camera exposure settings or reduce ambient lighting.',
                    'impact': 'Prevent face features from being washed out'
                })
        
        # Sharpness recommendations
        if scores['sharpness'] < 60:
            recommendations.append({
                'category': 'Hardware',
                'priority': 'High',
                'issue': 'Poor Image Sharpness',
                'recommendation': 'Clean camera lens, adjust focus, or upgrade to higher quality cameras.',
                'impact': 'Clearer face features for better recognition accuracy'
            })
        
        # Face detection recommendations
        if scores['face_detection'] < 50:
            recommendations.append({
                'category': 'Positioning',
                'priority': 'High',
                'issue': 'Low Face Detection Rate',
                'recommendation': 'Reposition cameras to face-level height and ensure clear view of entry points.',
                'impact': 'Higher face detection success rate'
            })
        
        # Consistency recommendations
        if scores['consistency'] < 60:
            recommendations.append({
                'category': 'Technical',
                'priority': 'Medium',
                'issue': 'Inconsistent Video Quality',
                'recommendation': 'Check camera mounting stability and ensure consistent lighting conditions.',
                'impact': 'More reliable face recognition performance'
            })
        
        self.analysis_results['recommendations'] = recommendations
    
    def generate_report(self, output_path="cctv_compatibility_report.json"):
        """Generate comprehensive compatibility report"""
        
        # Add timestamp and analysis metadata
        self.analysis_results['analysis_metadata'] = {
            'analyzed_at': datetime.now().isoformat(),
            'analyzer_version': '1.0',
            'analysis_type': 'CCTV Compatibility Assessment'
        }
        
        # Save detailed JSON report
        with open(output_path, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)
        
        # Generate human-readable summary
        self.print_summary_report()
        
        return output_path
    
    def print_summary_report(self):
        """Print a human-readable summary report"""
        
        print("\n" + "="*60)
        print("🏢 CCTV COMPATIBILITY ASSESSMENT REPORT")
        print("="*60)
        
        # Video Information
        video_info = self.analysis_results['video_info']
        print(f"\n📹 Video Information:")
        print(f"   File: {video_info['filename']}")
        print(f"   Resolution: {video_info['resolution']}")
        print(f"   Duration: {video_info['duration_seconds']}s")
        print(f"   FPS: {video_info['fps']}")
        
        # Overall Compatibility Score
        score = self.analysis_results['compatibility_score']
        print(f"\n🎯 Overall Compatibility Score: {score}/100")
        
        if score >= 80:
            status = "✅ EXCELLENT - Ready for deployment"
            color = "GREEN"
        elif score >= 65:
            status = "✅ GOOD - Suitable with minor adjustments"
            color = "YELLOW"
        elif score >= 45:
            status = "⚠️ FAIR - Requires improvements"
            color = "ORANGE"
        else:
            status = "❌ POOR - Major upgrades needed"
            color = "RED"
        
        print(f"   Status: {status}")
        
        # Detailed Scores
        scores = self.analysis_results['detailed_scores']
        print(f"\n📊 Detailed Analysis:")
        print(f"   Resolution Quality: {scores['resolution']}/100")
        print(f"   Lighting Quality: {scores['brightness']}/100")
        print(f"   Image Sharpness: {scores['sharpness']}/100")
        print(f"   Face Detection: {scores['face_detection']}/100")
        print(f"   Consistency: {scores['consistency']}/100")
        
        # Face Detection Stats
        face_stats = self.analysis_results['face_detection_stats']
        print(f"\n👤 Face Detection Performance:")
        print(f"   Frames Analyzed: {face_stats['frames_analyzed']}")
        print(f"   Frames with Faces: {face_stats['frames_with_faces']}")
        print(f"   Detection Rate: {face_stats['detection_success_rate']}%")
        print(f"   Average Confidence: {face_stats['average_confidence']}")
        
        # Recommendations
        recommendations = self.analysis_results['recommendations']
        if recommendations:
            print(f"\n💡 Recommendations for Improvement:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. [{rec['priority']}] {rec['issue']}")
                print(f"      → {rec['recommendation']}")
        else:
            print(f"\n🎉 No major improvements needed - System is ready!")
        
        print("\n" + "="*60)
        print("Report saved as 'cctv_compatibility_report.json'")
        print("="*60 + "\n")

# Example usage function
def analyze_cctv_footage(video_path):
    """Main function to analyze CCTV footage"""
    
    analyzer = CCTVAnalyzer()
    results = analyzer.analyze_video_quality(video_path)
    
    if results:
        # Generate comprehensive report
        report_path = analyzer.generate_report()
        
        # Return analysis results
        return results, report_path
    else:
        print("❌ Failed to analyze video footage")
        return None, None

if __name__ == "__main__":
    # Test with sample video
    print("🎥 CCTV Video Analyzer - Ready for Testing")
    print("Place your CCTV footage in the project folder and update the path below:")
    
    # Replace with your actual video path
    video_path = "cctv_test_footage.mp4"  # Update this with your video filename
    
    if os.path.exists(video_path):
        results, report_path = analyze_cctv_footage(video_path)
        print(f"\n✅ Analysis complete! Check {report_path} for detailed results.")
    else:
        print(f"⚠️ Video file not found: {video_path}")
        print("Please place your CCTV footage in the project folder and update the filename.")