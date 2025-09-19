import json
import os
from datetime import datetime

# Local attendance storage
ATTENDANCE_LOG = "local_attendance.json"

def save_local_attendance(student_name, time_detected):
    """Save attendance locally when Google Sheets is not available"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Load existing data
    if os.path.exists(ATTENDANCE_LOG):
        with open(ATTENDANCE_LOG, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    
    # Update today's attendance
    if today not in data:
        data[today] = {}
    
    data[today][student_name] = time_detected
    
    # Save back
    with open(ATTENDANCE_LOG, 'w') as f:
        json.dump(data, f, indent=2)

def view_attendance():
    """View all attendance records"""
    if not os.path.exists(ATTENDANCE_LOG):
        print("❌ No attendance records found yet.")
        print("🎯 Run the face recognition system first to generate attendance data.")
        return
    
    with open(ATTENDANCE_LOG, 'r') as f:
        data = json.load(f)
    
    print("=" * 60)
    print("📊 FACE RECOGNITION ATTENDANCE RECORDS")
    print("=" * 60)
    
    if not data:
        print("No attendance recorded yet.")
        return
    
    # Display attendance by date
    for date in sorted(data.keys(), reverse=True):
        print(f"\n📅 Date: {date}")
        print("-" * 40)
        
        day_data = data[date]
        if day_data:
            for student, time in day_data.items():
                print(f"  ✅ {student.ljust(15)} - {time}")
        else:
            print("  No attendance for this day")
    
    print("\n" + "=" * 60)
    print(f"📈 Total attendance sessions: {len(data)} days")
    
    # Show today's summary
    today = datetime.now().strftime("%Y-%m-%d")
    if today in data:
        print(f"👥 Today's attendance: {len(data[today])} students present")
    else:
        print("👥 Today's attendance: No students detected yet")

def show_student_history(student_name):
    """Show attendance history for a specific student"""
    if not os.path.exists(ATTENDANCE_LOG):
        print("❌ No attendance records found.")
        return
    
    with open(ATTENDANCE_LOG, 'r') as f:
        data = json.load(f)
    
    print(f"📊 Attendance History for: {student_name.upper()}")
    print("=" * 50)
    
    found = False
    for date in sorted(data.keys(), reverse=True):
        if student_name in data[date]:
            print(f"📅 {date} - ⏰ {data[date][student_name]}")
            found = True
    
    if not found:
        print(f"❌ No attendance records found for {student_name}")

if __name__ == "__main__":
    print("🎯 Face Recognition Attendance Viewer")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. View all attendance")
        print("2. View student history")
        print("3. Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            view_attendance()
        elif choice == "2":
            student = input("Enter student name: ").strip().lower()
            show_student_history(student)
        elif choice == "3":
            break
        else:
            print("❌ Invalid choice. Please try again.")
