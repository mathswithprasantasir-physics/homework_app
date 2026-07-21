from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
from datetime import datetime, timedelta
import hashlib
from werkzeug.utils import secure_filename

# Try to import CORS, but don't fail if it's not available
try:
    from flask_cors import CORS
    cors_available = True
except ImportError:
    cors_available = False
    print("Flask-CORS not installed. CORS features disabled.")

app = Flask(__name__)

# Enable CORS only if available
if cors_available:
    CORS(app)

app.config['UPLOAD_FOLDER'] = 'static/uploads/images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Data directory
DATA_DIR = 'data'
CLASSES_DIR = os.path.join(DATA_DIR, 'classes')
SUBJECTS_DIR = os.path.join(DATA_DIR, 'subjects')

# Create directories if they don't exist
os.makedirs(CLASSES_DIR, exist_ok=True)
os.makedirs(SUBJECTS_DIR, exist_ok=True)

def init_sample_data():
    """Initialize sample data files if they don't exist"""
    
    # Sample classes data (5-12)
    for class_num in range(5, 13):
        class_file = os.path.join(CLASSES_DIR, f'class_{class_num}.json')
        if not os.path.exists(class_file):
            sample_data = {
                "class": str(class_num),
                "subjects": ["Maths", "Physics", "Chemistry", "Biology"],
                "students": 0,
                "description": f"Class {class_num} students"
            }
            with open(class_file, 'w') as f:
                json.dump(sample_data, f, indent=2)
    
    # Sample subjects data with homework
    subjects = ["maths", "physics", "chemistry", "biology"]
    for subject in subjects:
        subject_file = os.path.join(SUBJECTS_DIR, f'{subject}.json')
        if not os.path.exists(subject_file):
            # Create sample homework with current date
            today = datetime.now()
            week_num = today.isocalendar()[1]
            
            sample_homework = {
                "subject": subject.capitalize(),
                "homework": [
                    {
                        "id": f"hw_{subject}_001",
                        "class": "8",
                        "subject": subject,
                        "type": "mcqs",
                        "question": f"Sample {subject} MCQ question for Class 8",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": "A",
                        "marks": 1,
                        "date": today.strftime("%Y-%m-%d"),
                        "week": week_num,
                        "has_image": False,
                        "image_path": None
                    },
                    {
                        "id": f"hw_{subject}_002",
                        "class": "9",
                        "subject": subject,
                        "type": "saq",
                        "question": f"Sample {subject} Short Answer Question for Class 9",
                        "hint": "Think about the basic concepts",
                        "marks": 5,
                        "date": today.strftime("%Y-%m-%d"),
                        "week": week_num,
                        "has_image": False,
                        "image_path": None
                    }
                ]
            }
            with open(subject_file, 'w') as f:
                json.dump(sample_homework, f, indent=2)

def get_week_number(date):
    """Get week number (1-52)"""
    return date.isocalendar()[1]

def get_week_range(date):
    """Get start and end date of a week"""
    start = date - timedelta(days=date.weekday())
    end = start + timedelta(days=6)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page with filters"""
    return render_template('index.html')

@app.route('/api/classes')
def get_classes():
    """Get all classes"""
    classes = []
    for class_num in range(5, 13):
        class_file = os.path.join(CLASSES_DIR, f'class_{class_num}.json')
        if os.path.exists(class_file):
            try:
                with open(class_file, 'r') as f:
                    class_data = json.load(f)
                    classes.append(class_data)
            except:
                # If file is corrupted, skip it
                pass
    return jsonify(classes)

@app.route('/api/subjects')
def get_subjects():
    """Get all subjects"""
    subjects = []
    for subject_file in os.listdir(SUBJECTS_DIR):
        if subject_file.endswith('.json'):
            try:
                with open(os.path.join(SUBJECTS_DIR, subject_file), 'r') as f:
                    subject_data = json.load(f)
                    subjects.append(subject_data['subject'])
            except:
                pass
    return jsonify(subjects)

@app.route('/api/homework')
def get_homework():
    """Get homework with filters"""
    class_filter = request.args.get('class')
    subject_filter = request.args.get('subject')
    week_filter = request.args.get('week')
    type_filter = request.args.get('type')
    
    all_homework = []
    
    # Load all homework from subject files
    for subject_file in os.listdir(SUBJECTS_DIR):
        if subject_file.endswith('.json'):
            try:
                with open(os.path.join(SUBJECTS_DIR, subject_file), 'r') as f:
                    data = json.load(f)
                    for homework in data.get('homework', []):
                        # Apply filters
                        if class_filter and homework.get('class') != class_filter:
                            continue
                        if subject_filter and homework.get('subject').lower() != subject_filter.lower():
                            continue
                        if type_filter and homework.get('type') != type_filter:
                            continue
                        if week_filter:
                            hw_date = datetime.strptime(homework.get('date', datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
                            hw_week = get_week_number(hw_date)
                            if str(hw_week) != week_filter:
                                continue
                        all_homework.append(homework)
            except:
                pass
    
    return jsonify(all_homework)

@app.route('/api/weeks')
def get_weeks():
    """Get available weeks with date ranges"""
    weeks = []
    current_date = datetime.now()
    
    # Get last 4 weeks
    for i in range(4):
        week_date = current_date - timedelta(weeks=i)
        week_num = get_week_number(week_date)
        start, end = get_week_range(week_date)
        weeks.append({
            'week_number': week_num,
            'start_date': start,
            'end_date': end,
            'label': f'Week {week_num} ({start} to {end})'
        })
    
    return jsonify(weeks)

@app.route('/api/question_types')
def get_question_types():
    """Get available question types"""
    types = ['mcqs', 'saq', 'vsaq', 'laq']
    return jsonify(types)

@app.route('/admin')
def admin():
    """Admin panel"""
    return render_template('admin.html')

@app.route('/api/upload_image', methods=['POST'])
def upload_image():
    """Upload image for question"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        image_path = f"/static/uploads/images/{filename}"
        return jsonify({
            'success': True,
            'image_path': image_path,
            'filename': filename
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/add_homework', methods=['POST'])
def add_homework():
    """Add new homework (admin only)"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['class', 'subject', 'type', 'question']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Load subject file
        subject_file = os.path.join(SUBJECTS_DIR, f"{data['subject'].lower()}.json")
        if not os.path.exists(subject_file):
            return jsonify({'error': 'Subject not found'}), 404
        
        with open(subject_file, 'r') as f:
            subject_data = json.load(f)
        
        # Generate homework ID
        hw_id = f"hw_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create homework entry
        homework = {
            'id': hw_id,
            'class': data['class'],
            'subject': data['subject'].lower(),
            'type': data['type'],
            'question': data['question'],
            'marks': int(data.get('marks', 1)),
            'date': data.get('date', datetime.now().strftime("%Y-%m-%d")),
            'week': get_week_number(datetime.now()),
            'has_image': bool(data.get('image_path')),
            'image_path': data.get('image_path'),
            'options': data.get('options', []),
            'correct_answer': data.get('correct_answer'),
            'hint': data.get('hint')
        }
        
        # Add to subject data
        subject_data['homework'].append(homework)
        
        # Save back to file
        with open(subject_file, 'w') as f:
            json.dump(subject_data, f, indent=2)
        
        return jsonify({'success': True, 'homework': homework})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_homework/<hw_id>', methods=['PUT'])
def update_homework(hw_id):
    """Update existing homework (admin only)"""
    try:
        data = request.json
        
        # Find and update homework in subject files
        found = False
        for subject_file in os.listdir(SUBJECTS_DIR):
            if subject_file.endswith('.json'):
                filepath = os.path.join(SUBJECTS_DIR, subject_file)
                try:
                    with open(filepath, 'r') as f:
                        subject_data = json.load(f)
                    
                    for i, hw in enumerate(subject_data.get('homework', [])):
                        if hw['id'] == hw_id:
                            # Update fields
                            for key, value in data.items():
                                if key in hw:
                                    hw[key] = value
                            subject_data['homework'][i] = hw
                            found = True
                            break
                    
                    if found:
                        with open(filepath, 'w') as f:
                            json.dump(subject_data, f, indent=2)
                        break
                except:
                    pass
        
        if not found:
            return jsonify({'error': 'Homework not found'}), 404
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_homework/<hw_id>', methods=['DELETE'])
def delete_homework(hw_id):
    """Delete homework (admin only)"""
    try:
        found = False
        for subject_file in os.listdir(SUBJECTS_DIR):
            if subject_file.endswith('.json'):
                filepath = os.path.join(SUBJECTS_DIR, subject_file)
                try:
                    with open(filepath, 'r') as f:
                        subject_data = json.load(f)
                    
                    original_length = len(subject_data.get('homework', []))
                    subject_data['homework'] = [hw for hw in subject_data.get('homework', []) if hw['id'] != hw_id]
                    
                    if len(subject_data['homework']) < original_length:
                        found = True
                        with open(filepath, 'w') as f:
                            json.dump(subject_data, f, indent=2)
                        break
                except:
                    pass
        
        if not found:
            return jsonify({'error': 'Homework not found'}), 404
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialize sample data
try:
    init_sample_data()
except:
    print("Warning: Could not initialize sample data")

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
