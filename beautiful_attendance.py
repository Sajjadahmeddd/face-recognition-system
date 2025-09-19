import json
import os
from datetime import datetime
from tabulate import tabulate
import pandas as pd

LOCAL_ATTENDANCE_LOG = "local_attendance.json"

def create_beautiful_attendance_table():
    """Create a beautiful table view of attendance data"""
    
    if not os.path.exists(LOCAL_ATTENDANCE_LOG):
        print("❌ No attendance records found yet.")
        print("🎯 Run the face recognition system first!")
        return
    
    with open(LOCAL_ATTENDANCE_LOG, 'r') as f:
        data = json.load(f)
    
    if not data:
        print("📊 No attendance data available.")
        return
    
    # Get all students
    all_students = set()
    for date_data in data.values():
        all_students.update(date_data.keys())
    
    all_students = sorted(list(all_students))
    
    # Create table data
    table_data = []
    headers = ["Date"] + all_students
    
    for date in sorted(data.keys(), reverse=True):
        row = [date]
        for student in all_students:
            time_val = data[date].get(student, "")
            row.append(time_val)
        table_data.append(row)
    
    # Display beautiful table
    print("\n" + "="*80)
    print("📊 FACE RECOGNITION ATTENDANCE RECORDS")
    print("="*80)
    
    # Use tabulate for beautiful formatting
    try:
        print(tabulate(table_data, headers=headers, tablefmt="grid", stralign="center"))
    except:
        # Fallback if tabulate not available
        print(tabulate(table_data, headers=headers, tablefmt="simple"))
    
    print("="*80)
    
    # Summary statistics
    total_days = len(data)
    today = datetime.now().strftime("%Y-%m-%d")
    today_count = len(data.get(today, {}))
    
    print(f"📈 Summary:")
    print(f"   📅 Total days recorded: {total_days}")
    print(f"   👥 Students registered: {len(all_students)}")
    print(f"   🎯 Today's attendance: {today_count} students")
    
    # Most active students
    student_counts = {}
    for date_data in data.values():
        for student in date_data:
            student_counts[student] = student_counts.get(student, 0) + 1
    
    if student_counts:
        most_active = max(student_counts, key=student_counts.get)
        print(f"   🏆 Most active student: {most_active} ({student_counts[most_active]} days)")
    
    print("="*80)

def export_to_excel():
    """Export attendance data to Excel for better viewing"""
    if not os.path.exists(LOCAL_ATTENDANCE_LOG):
        print("❌ No attendance data to export.")
        return
    
    with open(LOCAL_ATTENDANCE_LOG, 'r') as f:
        data = json.load(f)
    
    # Convert to pandas DataFrame
    all_students = set()
    for date_data in data.values():
        all_students.update(date_data.keys())
    
    all_students = sorted(list(all_students))
    
    # Create DataFrame
    df_data = []
    for date in sorted(data.keys()):
        row = {"Date": date}
        for student in all_students:
            row[student] = data[date].get(student, "")
        df_data.append(row)
    
    df = pd.DataFrame(df_data)
    
    # Save to Excel
    excel_file = "attendance_backup.xlsx"
    df.to_excel(excel_file, index=False)
    print(f"✅ Attendance exported to: {excel_file}")
    print(f"📊 You can now open {excel_file} in Excel for beautiful viewing!")

def main():
    print("🎯 Beautiful Attendance Viewer")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. 📊 View beautiful table")
        print("2. 📁 Export to Excel")
        print("3. 🚪 Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            create_beautiful_attendance_table()
        elif choice == "2":
            export_to_excel()
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
