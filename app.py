from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import json
import uuid

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'homework-app-secret-key-2024')
app.config['UPLOAD_FOLDER'] = 'uploads/images'
app.config['DATA_FOLDER'] = 'data'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)

# JSON File paths
QUESTIONS_FILE = os.path.join(app.config['DATA_FOLDER'], 'questions.json')
HOMEWORKS_FILE = os.path.join(app.config['DATA_FOLDER'], 'homeworks.json')
SUBJECTS_FILE = os.path.join(app.config['DATA_FOLDER'], 'subjects.json')
USERS_FILE = os.path.join(app.config['DATA_FOLDER'], 'users.json')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ==================== JSON DATA HANDLERS ====================

def load_json(filepath, default=[]):
    """Load data from JSON file"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default
    except:
        return default

def save_json(filepath, data):
    """Save data to JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_next_id(data_list):
    """Get next available ID"""
    if not data_list:
        return 1
    return max(item.get('id', 0) for item in data_list) + 1

# ==================== USER MODEL (JSON) ====================

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.password_hash = user_data['password_hash']
        self.is_admin = user_data.get('is_admin', False)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def get(user_id):
        users = load_json(USERS_FILE, [])
        for user_data in users:
            if user_data['id'] == user_id:
                return User(user_data)
        return None
    
    @staticmethod
    def get_by_username(username):
        users = load_json(USERS_FILE, [])
        for user_data in users:
            if user_data['username'] == username:
                return User(user_data)
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# ==================== HELPER FUNCTIONS ====================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_week_number():
    return datetime.utcnow().isocalendar()[1]

def get_all_subjects():
    return load_json(SUBJECTS_FILE, [])

def get_all_questions():
    return load_json(QUESTIONS_FILE, [])

def get_all_homeworks():
    return load_json(HOMEWORKS_FILE, [])

def get_question_by_id(question_id):
    questions = get_all_questions()
    for q in questions:
        if q['id'] == question_id:
            return q
    return None

def get_subject_by_id(subject_id):
    subjects = get_all_subjects()
    for s in subjects:
        if s['id'] == subject_id:
            return s
    return None

def get_homework_by_id(homework_id):
    homeworks = get_all_homeworks()
    for h in homeworks:
        if h['id'] == homework_id:
            return h
    return None

# ==================== ROUTES ====================

@app.route('/')
def index():
    return redirect(url_for('public_homework'))

# ==================== PUBLIC ROUTES (No Login Required) ====================

@app.route('/homework')
def public_homework():
    """Public homework page - no login required"""
    class_level = request.args.get('class', '')
    subject_id = request.args.get('subject', '')
    week_filter = request.args.get('week', '')
    
    homeworks = get_all_homeworks()
    subjects = get_all_subjects()
    
    # Filter homeworks
    filtered_homeworks = []
    for hw in homeworks:
        if not hw.get('is_active', True):
            continue
        
        if class_level and str(hw.get('class_level', '')) != class_level:
            continue
        
        if subject_id and str(hw.get('subject_id', '')) != subject_id:
            continue
        
        if week_filter:
            current_week = get_week_number()
            hw_week = hw.get('week_number', current_week)
            if week_filter == 'last' and hw_week != current_week - 1:
                continue
            elif week_filter == 'two_weeks' and hw_week != current_week - 2:
                continue
            elif week_filter == 'three_weeks' and hw_week != current_week - 3:
                continue
            elif week_filter == 'current' and hw_week != current_week:
                continue
        
        # Add subject name to homework
        subject = get_subject_by_id(hw.get('subject_id'))
        hw['subject_name'] = subject['name'] if subject else 'Unknown'
        
        # Add question count
        question_ids = hw.get('questions', [])
        if isinstance(question_ids, str):
            try:
                question_ids = json.loads(question_ids)
            except:
                question_ids = []
        hw['question_count'] = len(question_ids)
        
        filtered_homeworks.append(hw)
    
    # Sort by created date (newest first)
    filtered_homeworks.sort(key=lambda x: x.get('created_date', ''), reverse=True)
    
    return render_template('public_homework.html',
                         homeworks=filtered_homeworks,
                         subjects=subjects,
                         selected_class=class_level,
                         selected_subject=subject_id,
                         week_filter=week_filter)

@app.route('/homework/<int:homework_id>')
def view_homework_detail(homework_id):
    """View homework details - no login required"""
    homework = get_homework_by_id(homework_id)
    if not homework:
        flash('Homework not found!', 'error')
        return redirect(url_for('public_homework'))
    
    # Get questions
    question_ids = homework.get('questions', [])
    if isinstance(question_ids, str):
        try:
            question_ids = json.loads(question_ids)
        except:
            question_ids = []
    
    questions = []
    for qid in question_ids:
        question = get_question_by_id(int(qid))
        if question:
            # Add subject name
            subject = get_subject_by_id(question.get('subject_id'))
            question['subject_name'] = subject['name'] if subject else 'Unknown'
            questions.append(question)
    
    # Add subject name to homework
    subject = get_subject_by_id(homework.get('subject_id'))
    homework['subject_name'] = subject['name'] if subject else 'Unknown'
    
    return render_template('student/homework_detail.html',
                         homework=homework,
                         questions=questions)

# ==================== AUTH ROUTES ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('public_homework'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.get_by_username(username)
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('public_homework'))
        flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('public_homework'))

# ==================== ADMIN ROUTES ====================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('public_homework'))
    
    questions = get_all_questions()
    homeworks = get_all_homeworks()
    subjects = get_all_subjects()
    
    # Get recent questions (last 10)
    questions.sort(key=lambda x: x.get('created_date', ''), reverse=True)
    recent_questions = questions[:10]
    
    # Get recent homeworks (last 10)
    homeworks.sort(key=lambda x: x.get('created_date', ''), reverse=True)
    recent_homeworks = homeworks[:10]
    
    # Add subject names to recent items
    for q in recent_questions:
        subject = get_subject_by_id(q.get('subject_id'))
        q['subject_name'] = subject['name'] if subject else 'Unknown'
        q['class_level'] = subject['class_level'] if subject else 'Unknown'
    
    for hw in recent_homeworks:
        subject = get_subject_by_id(hw.get('subject_id'))
        hw['subject_name'] = subject['name'] if subject else 'Unknown'
    
    return render_template('admin/dashboard.html',
                         total_questions=len(questions),
                         total_homeworks=len(homeworks),
                         total_subjects=len(subjects),
                         recent_questions=recent_questions,
                         recent_homeworks=recent_homeworks)

@app.route('/admin/add_question', methods=['GET', 'POST'])
@login_required
def add_question():
    if not current_user.is_admin:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            questions = get_all_questions()
            
            question = {
                'id': get_next_id(questions),
                'subject_id': int(request.form.get('subject_id')),
                'question_type': request.form.get('question_type'),
                'question_text': request.form.get('question_text'),
                'question_latex': request.form.get('question_latex', ''),
                'marks': int(request.form.get('marks', 1)),
                'difficulty': request.form.get('difficulty', 'medium'),
                'correct_answer': request.form.get('correct_answer', ''),
                'week_number': get_week_number(),
                'created_date': datetime.utcnow().isoformat(),
                'is_active': True
            }
            
            # Handle MCQ options
            if question['question_type'] == 'MCQ':
                options = {
                    'A': request.form.get('option_a', ''),
                    'B': request.form.get('option_b', ''),
                    'C': request.form.get('option_c', ''),
                    'D': request.form.get('option_d', ''),
                    'correct': request.form.get('correct_option', 'A')
                }
                question['options'] = options
            
            # Handle image upload
            if 'question_image' in request.files:
                file = request.files['question_image']
                if file and file.filename and allowed_file(file.filename):
                    filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    question['image_path'] = filename
            
            questions.append(question)
            save_json(QUESTIONS_FILE, questions)
            
            flash('✅ Question added successfully!', 'success')
            return redirect(url_for('add_question'))
            
        except Exception as e:
            flash(f'❌ Error: {str(e)}', 'error')
    
    subjects = get_all_subjects()
    subjects.sort(key=lambda x: (x['class_level'], x['name']))
    return render_template('admin/add_question.html', subjects=subjects)

@app.route('/admin/create_homework', methods=['GET', 'POST'])
@login_required
def create_homework():
    if not current_user.is_admin:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            homeworks = get_all_homeworks()
            question_ids = request.form.getlist('question_ids')
            
            # Calculate total marks
            total_marks = 0
            for qid in question_ids:
                question = get_question_by_id(int(qid))
                if question:
                    total_marks += question.get('marks', 0)
            
            due_date_str = request.form.get('due_date')
            due_date = due_date_str if due_date_str else None
            
            homework = {
                'id': get_next_id(homeworks),
                'title': request.form.get('title'),
                'class_level': request.form.get('class_level'),
                'subject_id': int(request.form.get('subject_id')),
                'questions': question_ids,  # List of question IDs
                'total_marks': total_marks,
                'due_date': due_date,
                'created_date': datetime.utcnow().isoformat(),
                'week_number': get_week_number(),
                'is_active': True
            }
            
            homeworks.append(homework)
            save_json(HOMEWORKS_FILE, homeworks)
            
            flash(f'✅ Homework created with {len(question_ids)} questions! Total: {total_marks} marks', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            flash(f'❌ Error: {str(e)}', 'error')
    
    subjects = get_all_subjects()
    return render_template('admin/create_homework.html', subjects=subjects)

@app.route('/admin/get_questions')
@login_required
def get_questions_api():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    subject_id = request.args.get('subject_id', '')
    question_type = request.args.get('question_type', '')
    
    questions = get_all_questions()
    filtered_questions = []
    
    for q in questions:
        if not q.get('is_active', True):
            continue
        
        if subject_id and str(q.get('subject_id', '')) != subject_id:
            continue
        
        if question_type and q.get('question_type', '') != question_type:
            continue
        
        # Add subject info
        subject = get_subject_by_id(q.get('subject_id'))
        filtered_questions.append({
            'id': q['id'],
            'text': q['question_text'][:100] + ('...' if len(q['question_text']) > 100 else ''),
            'type': q['question_type'],
            'marks': q['marks'],
            'difficulty': q.get('difficulty', 'medium'),
            'subject': subject['name'] if subject else 'Unknown',
            'class': subject['class_level'] if subject else 'Unknown'
        })
    
    # Sort by newest first
    filtered_questions.reverse()
    
    return jsonify(filtered_questions)

@app.route('/admin/manage_questions')
@login_required
def manage_questions():
    if not current_user.is_admin:
        return redirect(url_for('login'))
    
    questions = get_all_questions()
    
    # Add subject names
    for q in questions:
        subject = get_subject_by_id(q.get('subject_id'))
        q['subject_name'] = subject['name'] if subject else 'Unknown'
        q['class_level'] = subject['class_level'] if subject else 'Unknown'
    
    questions.sort(key=lambda x: x.get('created_date', ''), reverse=True)
    
    return render_template('admin/manage_questions.html', questions=questions)

@app.route('/admin/delete_question/<int:question_id>')
@login_required
def delete_question(question_id):
    if not current_user.is_admin:
        return redirect(url_for('login'))
    
    questions = get_all_questions()
    questions = [q for q in questions if q['id'] != question_id]
    save_json(QUESTIONS_FILE, questions)
    
    flash('Question deleted!', 'success')
    return redirect(url_for('manage_questions'))

@app.route('/admin/delete_homework/<int:homework_id>')
@login_required
def delete_homework(homework_id):
    if not current_user.is_admin:
        return redirect(url_for('login'))
    
    homeworks = get_all_homeworks()
    homeworks = [h for h in homeworks if h['id'] != homework_id]
    save_json(HOMEWORKS_FILE, homeworks)
    
    flash('Homework deleted!', 'success')
    return redirect(url_for('admin_dashboard'))

# ==================== FILE SERVING ====================

@app.route('/uploads/images/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==================== HEALTH CHECK ====================

@app.route('/health')
def health_check():
    questions = get_all_questions()
    homeworks = get_all_homeworks()
    return jsonify({
        'status': 'ok',
        'message': 'Homework App is running!',
        'total_questions': len(questions),
        'total_homeworks': len(homeworks)
    })

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# ==================== INITIALIZE DATA ====================

def init_data():
    """Initialize JSON data files with default data"""
    
    # Initialize subjects
    subjects = get_all_subjects()
    if not subjects:
        subjects_data = [
            ('Mathematics', '5'), ('Mathematics', '6'), ('Mathematics', '7'),
            ('Mathematics', '8'), ('Mathematics', '9'), ('Mathematics', '10'),
            ('Mathematics', '11'), ('Mathematics', '12'),
            ('Physics', '9'), ('Physics', '10'), ('Physics', '11'), ('Physics', '12'),
            ('Chemistry', '9'), ('Chemistry', '10'), ('Chemistry', '11'), ('Chemistry', '12'),
            ('Biology', '9'), ('Biology', '10'), ('Biology', '11'), ('Biology', '12'),
        ]
        for i, (name, level) in enumerate(subjects_data, 1):
            subjects.append({
                'id': i,
                'name': name,
                'class_level': level
            })
        save_json(SUBJECTS_FILE, subjects)
        print("✅ Subjects initialized!")
    
    # Initialize admin user
    users = load_json(USERS_FILE, [])
    if not users:
        admin_user = {
            'id': 1,
            'username': 'admin',
            'password_hash': generate_password_hash('admin123'),
            'is_admin': True
        }
        users.append(admin_user)
        save_json(USERS_FILE, users)
        print("✅ Admin user created!")
    
    # Initialize empty questions if file doesn't exist
    if not os.path.exists(QUESTIONS_FILE):
        save_json(QUESTIONS_FILE, [])
        print("✅ Questions file created!")
    
    # Initialize empty homeworks if file doesn't exist
    if not os.path.exists(HOMEWORKS_FILE):
        save_json(HOMEWORKS_FILE, [])
        print("✅ Homeworks file created!")

# Initialize data on startup
init_data()

# ==================== RUN APP ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
