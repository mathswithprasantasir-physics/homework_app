from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import uuid
from PIL import Image
import base64
from io import BytesIO

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///homework.db'
app.config['UPLOAD_FOLDER'] = 'uploads/images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    class_level = db.Column(db.String(10), nullable=False)  # Class 5 to 12
    questions = db.relationship('Question', backref='subject', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # MCQ, SAQ, VSAQ, LAQ
    question_text = db.Column(db.Text, nullable=False)
    question_latex = db.Column(db.Text)  # For LaTeX content
    options = db.Column(db.Text)  # JSON string for MCQ options
    correct_answer = db.Column(db.Text)
    marks = db.Column(db.Integer, default=1)
    difficulty = db.Column(db.String(20), default='medium')  # easy, medium, hard
    image_path = db.Column(db.String(200))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    week_number = db.Column(db.Integer)  # Week number in year
    is_active = db.Column(db.Boolean, default=True)

class HomeworkAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    class_level = db.Column(db.String(10), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    questions = db.Column(db.Text)  # JSON array of question IDs
    total_marks = db.Column(db.Integer)
    due_date = db.Column(db.DateTime)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    week_number = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Optimize image
        img = Image.open(file)
        img.thumbnail((800, 800))  # Resize if too large
        img.save(filepath, optimize=True, quality=85)
        
        return filename
    return None

def get_week_number(date=None):
    if date is None:
        date = datetime.utcnow()
    return date.isocalendar()[1]

def get_week_label(week_offset=0):
    """Get week label like 'Current Week', 'Last Week', etc."""
    current_week = get_week_number()
    target_week = current_week - week_offset
    
    if week_offset == 0:
        return "Current Week"
    elif week_offset == 1:
        return "Last Week"
    elif week_offset == 2:
        return "Two Weeks Ago"
    elif week_offset == 3:
        return "Three Weeks Ago"
    else:
        return f"Week {target_week}"

# Routes
@app.route('/')
def index():
    return render_template('base.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Admin Routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    subjects = Subject.query.all()
    recent_homeworks = HomeworkAssignment.query.order_by(
        HomeworkAssignment.created_date.desc()
    ).limit(10).all()
    
    return render_template('admin/dashboard.html', 
                         subjects=subjects, 
                         recent_homeworks=recent_homeworks)

@app.route('/admin/add_question', methods=['GET', 'POST'])
@login_required
def add_question():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            subject_id = request.form.get('subject_id')
            question_type = request.form.get('question_type')
            question_text = request.form.get('question_text')
            question_latex = request.form.get('question_latex', '')
            marks = int(request.form.get('marks', 1))
            difficulty = request.form.get('difficulty', 'medium')
            
            # Handle MCQ options
            options = None
            if question_type == 'MCQ':
                options_list = request.form.getlist('options[]')
                correct_option = request.form.get('correct_option')
                options = {
                    'choices': options_list,
                    'correct': correct_option
                }
            
            # Handle image upload
            image_path = None
            if 'question_image' in request.files:
                file = request.files['question_image']
                if file.filename:
                    image_path = save_image(file)
            
            # Create new question
            question = Question(
                subject_id=subject_id,
                question_type=question_type,
                question_text=question_text,
                question_latex=question_latex,
                options=json.dumps(options) if options else None,
                correct_answer=request.form.get('correct_answer'),
                marks=marks,
                difficulty=difficulty,
                image_path=image_path,
                week_number=get_week_number()
            )
            
            db.session.add(question)
            db.session.commit()
            flash('Question added successfully!', 'success')
            
        except Exception as e:
            flash(f'Error adding question: {str(e)}', 'error')
        
        return redirect(url_for('add_question'))
    
    subjects = Subject.query.all()
    return render_template('admin/add_question.html', subjects=subjects)

@app.route('/admin/create_homework', methods=['GET', 'POST'])
@login_required
def create_homework():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        class_level = request.form.get('class_level')
        subject_id = request.form.get('subject_id')
        question_ids = request.form.getlist('question_ids')
        due_date_str = request.form.get('due_date')
        
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        
        # Calculate total marks
        questions = Question.query.filter(Question.id.in_(question_ids)).all()
        total_marks = sum(q.marks for q in questions)
        
        homework = HomeworkAssignment(
            title=title,
            class_level=class_level,
            subject_id=subject_id,
            questions=json.dumps(question_ids),
            total_marks=total_marks,
            due_date=due_date,
            week_number=get_week_number()
        )
        
        db.session.add(homework)
        db.session.commit()
        flash('Homework assignment created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    subjects = Subject.query.all()
    return render_template('admin/create_homework.html', subjects=subjects)

@app.route('/admin/get_questions')
@login_required
def get_questions():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    subject_id = request.args.get('subject_id')
    class_level = request.args.get('class_level')
    question_type = request.args.get('question_type')
    week_offset = request.args.get('week', 0, type=int)
    
    query = Question.query.filter_by(is_active=True)
    
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if question_type:
        query = query.filter_by(question_type=question_type)
    if week_offset >= 0:
        target_week = get_week_number() - week_offset
        query = query.filter_by(week_number=target_week)
    
    questions = query.all()
    
    return jsonify([{
        'id': q.id,
        'text': q.question_text[:100] + '...',
        'type': q.question_type,
        'marks': q.marks,
        'difficulty': q.difficulty,
        'subject': q.subject.name
    } for q in questions])

# Student Routes
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Get filter parameters
    class_level = request.args.get('class', '')
    subject_id = request.args.get('subject', '')
    week_filter = request.args.get('week', 'current')
    
    query = HomeworkAssignment.query.filter_by(is_active=True)
    
    if class_level:
        query = query.filter_by(class_level=class_level)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    
    # Week filtering
    current_week = get_week_number()
    if week_filter == 'current':
        query = query.filter_by(week_number=current_week)
    elif week_filter == 'last':
        query = query.filter_by(week_number=current_week - 1)
    elif week_filter == 'two_weeks':
        query = query.filter_by(week_number=current_week - 2)
    elif week_filter == 'three_weeks':
        query = query.filter_by(week_number=current_week - 3)
    
    homeworks = query.order_by(HomeworkAssignment.created_date.desc()).all()
    subjects = Subject.query.all()
    
    return render_template('student/view_homework.html', 
                         homeworks=homeworks, 
                         subjects=subjects,
                         week_filter=week_filter)

@app.route('/student/homework/<int:homework_id>')
@login_required
def view_homework_detail(homework_id):
    homework = HomeworkAssignment.query.get_or_404(homework_id)
    question_ids = json.loads(homework.questions)
    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    
    return render_template('student/homework_detail.html', 
                         homework=homework, 
                         questions=questions)

@app.route('/uploads/images/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# API Routes for dynamic filtering
@app.route('/api/subjects')
def get_subjects():
    class_level = request.args.get('class')
    query = Subject.query
    if class_level:
        query = query.filter_by(class_level=class_level)
    subjects = query.all()
    return jsonify([{'id': s.id, 'name': s.name, 'class': s.class_level} for s in subjects])

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Initialize database and create admin user
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                is_admin=True
            )
            admin.set_password('admin123')  # Change this password!
            db.session.add(admin)
        
        # Create sample subjects if not exists
        if not Subject.query.first():
            subjects_data = [
                ('Mathematics', '5'), ('Mathematics', '6'), ('Mathematics', '7'),
                ('Mathematics', '8'), ('Mathematics', '9'), ('Mathematics', '10'),
                ('Mathematics', '11'), ('Mathematics', '12'),
                ('Physics', '9'), ('Physics', '10'), ('Physics', '11'), ('Physics', '12'),
                ('Chemistry', '9'), ('Chemistry', '10'), ('Chemistry', '11'), ('Chemistry', '12'),
                ('Biology', '9'), ('Biology', '10'), ('Biology', '11'), ('Biology', '12'),
            ]
            
            for name, level in subjects_data:
                subject = Subject(name=name, class_level=level)
                db.session.add(subject)
        
        db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)

# Initialize database before first request
@app.before_request
def before_first_request():
    db.create_all()
    
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            is_admin=True
        )
        admin.set_password('admin123')  # CHANGE THIS PASSWORD!
        db.session.add(admin)
    
    # Create sample subjects if not exists
    if not Subject.query.first():
        subjects_data = [
            ('Mathematics', '5'), ('Mathematics', '6'), ('Mathematics', '7'),
            ('Mathematics', '8'), ('Mathematics', '9'), ('Mathematics', '10'),
            ('Mathematics', '11'), ('Mathematics', '12'),
            ('Physics', '9'), ('Physics', '10'), ('Physics', '11'), ('Physics', '12'),
            ('Chemistry', '9'), ('Chemistry', '10'), ('Chemistry', '11'), ('Chemistry', '12'),
            ('Biology', '9'), ('Biology', '10'), ('Biology', '11'), ('Biology', '12'),
        ]
        
        for name, level in subjects_data:
            subject = Subject(name=name, class_level=level)
            db.session.add(subject)
    
    db.session.commit()
