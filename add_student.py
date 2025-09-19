"""
Student Image Manager
Add new students to the face recognition system easily
"""
import os
import shutil

STUDENT_IMAGES_FOLDER = "student_images"

def add_new_student():
    """Add a new student to the system"""
    print("👥 Add New Student to Face Recognition System")
    print("=" * 50)
    
    # Get student details
    name = input("Enter student name: ").strip().lower()
    rrn = input("Enter RRN number: ").strip()
    branch = input("Enter branch (e.g., AI&DS, IT, CSE): ").strip()
    
    # Get image file
    image_path = input("Enter path to student's image file: ").strip().strip('"')
    
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return
    
    # Create filename
    _, ext = os.path.splitext(image_path)
    new_filename = f"{name}{ext}"
    destination = os.path.join(STUDENT_IMAGES_FOLDER, new_filename)
    
    # Copy image to student_images folder
    try:
        shutil.copy2(image_path, destination)
        print(f"✅ Image copied to: {destination}")
    except Exception as e:
        print(f"❌ Error copying image: {e}")
        return
    
    # Show code to add to face recognition.py
    print("\n📝 Add this line to your student_data dict in face recognition.py:")
    print(f"    '{new_filename}': ('{name}', {rrn}, '{branch}'),")
    
    print(f"\n🎯 Student '{name}' added successfully!")
    print(f"📁 Image location: student_images/{new_filename}")

def list_students():
    """List all students in the system"""
    print("👥 Current Students in System")
    print("=" * 40)
    
    if not os.path.exists(STUDENT_IMAGES_FOLDER):
        print(f"❌ Student images folder not found!")
        return
    
    image_files = [f for f in os.listdir(STUDENT_IMAGES_FOLDER) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print("❌ No student images found!")
        return
    
    print(f"📷 Found {len(image_files)} student images:")
    for i, filename in enumerate(sorted(image_files), 1):
        name = os.path.splitext(filename)[0]
        print(f"  {i}. {name.title()} ({filename})")

def main():
    print("🎯 Student Image Manager")
    print("=" * 30)
    
    while True:
        print("\nOptions:")
        print("1. 👥 Add new student")
        print("2. 📋 List current students")
        print("3. 🚪 Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            add_new_student()
        elif choice == "2":
            list_students()
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
