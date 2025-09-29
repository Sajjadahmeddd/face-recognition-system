"""
Quick CCTV Test Runner
=====================

Simple script to test HR's CCTV footage for face recognition compatibility.
Just place the video file in the project folder and run this script.

Author: Sajjad Ahmed
"""

import os
from cctv_analyzer import analyze_cctv_footage

def main():
    print("🏢 CCTV Footage Analysis for Institutional Deployment")
    print("="*55)
    
    # List video files in current directory
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
    video_files = []
    
    for file in os.listdir('.'):
        if any(file.lower().endswith(ext) for ext in video_extensions):
            video_files.append(file)
    
    if not video_files:
        print("❌ No video files found in current directory")
        print("   Please place your CCTV footage file here and try again.")
        print("   Supported formats: MP4, AVI, MOV, MKV, WMV, FLV")
        return
    
    print("📹 Found video files:")
    for i, video in enumerate(video_files, 1):
        print(f"   {i}. {video}")
    
    # Select video file
    if len(video_files) == 1:
        selected_video = video_files[0]
        print(f"\n🎯 Analyzing: {selected_video}")
    else:
        try:
            choice = int(input(f"\nSelect video file (1-{len(video_files)}): ")) - 1
            selected_video = video_files[choice]
        except (ValueError, IndexError):
            print("❌ Invalid selection")
            return
    
    # Analyze the video
    print(f"\n🔍 Starting compatibility analysis...")
    results, report_path = analyze_cctv_footage(selected_video)
    
    if results:
        print("\n✅ Analysis completed successfully!")
        print(f"📋 Detailed report saved as: {report_path}")
        
        # Quick summary for HR
        score = results['compatibility_score']
        print(f"\n📊 QUICK SUMMARY FOR HR:")
        print(f"   Compatibility Score: {score}/100")
        
        if score >= 75:
            recommendation = "✅ RECOMMENDED: Your CCTV system is suitable for face recognition attendance!"
        elif score >= 50:
            recommendation = "⚠️ CONDITIONAL: System can work with some improvements (see recommendations)"
        else:
            recommendation = "❌ NOT RECOMMENDED: Significant upgrades needed for reliable operation"
        
        print(f"   Status: {recommendation}")
        
        # Show key metrics
        face_stats = results['face_detection_stats']
        print(f"\n🎯 Key Performance Metrics:")
        print(f"   Face Detection Rate: {face_stats['detection_success_rate']}%")
        print(f"   Video Resolution: {results['video_info']['resolution']}")
        print(f"   Frames Analyzed: {face_stats['frames_analyzed']}")
        
        # Show top recommendations
        if results['recommendations']:
            print(f"\n💡 Top Priority Improvements:")
            high_priority = [r for r in results['recommendations'] if r['priority'] == 'High']
            for rec in high_priority[:3]:  # Show top 3
                print(f"   • {rec['issue']}: {rec['recommendation']}")
    
    else:
        print("❌ Analysis failed. Please check the video file and try again.")

if __name__ == "__main__":
    main()
    input("\nPress Enter to close...")