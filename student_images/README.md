# Student Images Folder

This folder contains all student photos used for face recognition.

## 📁 Current Students:
- yaseen.jpg - Yaseen (RRN: 1170, Branch: AI&DS)
- naveed.jpg - Naveed (RRN: 1152, Branch: AI&DS)  
- hameed.jpg - Hameed (RRN: 1145, Branch: AI&DS)
- viki.jpg - Vikinesh (RRN: 1146, Branch: AI&DS)
- sajjad.jpg - Sajjad (RRN: 1134, Branch: IT)
- samgr.jpg - Sammm (RRN: 1136, Branch: IT)
- lingesh.jpg - Linguuu (RRN: 1136, Branch: IT)

## 📷 Adding New Students:

### Method 1: Using the Helper Script
```bash
python add_student.py
```

### Method 2: Manual Addition
1. **Add image**: Copy student's photo to this folder
2. **Naming**: Use format `firstname.jpg` (lowercase)
3. **Update code**: Add entry to `student_data` dict in `face recognition.py`

### Example:
```python
# In face recognition.py, add to student_data dict:
'john.jpg': ('john', 1234, 'CSE'),
```

## 📋 Image Requirements:
- **Format**: JPG, JPEG, or PNG
- **Quality**: Clear face, good lighting
- **Size**: Any reasonable size (will be processed automatically)
- **Face**: One person per image, facing camera

## 🎯 Benefits of This Structure:
- ✅ **Organized**: All images in one place
- ✅ **Scalable**: Easy to add many students
- ✅ **Clean**: Main folder not cluttered
- ✅ **Professional**: Better project structure
