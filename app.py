from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import json
import uuid

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///homework.db'
app.config['UPLOAD_FOLDER'] = 'uploads/images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    class_level = db.Column(db.String(10), nullable=False)
    questions = db.relationship('Question', backref='subject', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    question_type = db.Column(db.String(20), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_latex = db.Column(db.Text)
    options = db.Column(db.Text)
    correct_answer = db.Column(db.Text)
    marks = db.Column(db.Integer, default=1)
    difficulty = db.Column(db.String(20), default='medium')
    image_path = db.Column(db.String(200))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    week_number = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)

class HomeworkAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    class_level = db.Column(db.String(10), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    questions = db.Column(db.Text)
    total_marks = db.Column(db.Integer)
    due_date = db.Column(db.DateTime)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    week_number = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_week_number():
    return datetime.utcnow().isocalendar()[1]

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('student_dashboard'))
        flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('student_dashboard'))
    
    questions = Question.query.order_by(Question.created_date.desc()).limit(10).all()
    subjects = Subject.query.all()
    
    return render_template('admin/dashboard.html', 
                         questions=questions,
                         subjects=subjects)

@app.route('/admin/add_question', methods=['GET', 'POST'])
@login_required
def add_question():
    if not current_user.is_admin:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            question = Question(
                subject_id=request.form.get('subject_id'),
                question_type=request.form.get('question_type'),
                question_text=request.form.get('question_text'),
                question_latex=request.form.get('question_latex', ''),
                marks=int(request.form.get('marks', 1)),
                difficulty=request.form.get('difficulty', 'medium'),
                correct_answer=request.form.get('correct_answer', ''),
                week_number=get_week_number()
            )
            
            # Handle MCQ options
            if question.question_type == 'MCQ':
                options = {
                    'choices': request.form.getlist('options[]'),
                    'correct': request.form.get('correct_option', '0')
                }
                question.options = json.dumps(options)
            
            # Handle image upload
            if 'question_image' in request.files:
                file = request.files['question_image']
                if file and allowed_file(file.filename):
                    filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    question.image_path = filename
            
            db.session.add(question)
            db.session.commit()
            flash('Question added successfully!', 'success')
            return redirect(url_for('add_question'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    
    subjects = Subject.query.all()
    return render_template('admin/add_question.html', subjects=subjects)

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    class_level = request.args.get('class', '')
    subject_id = request.args.get('subject', '')
    week = request.args.get('week', '')
    
    query = HomeworkAssignment.query.filter_by(is_active=True)
    
    if class_level:
        query = query.filter_by(class_level=class_level)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if week:
        week_num = get_week_number()
        if week == 'last':
            query = query.filter_by(week_number=week_num-1)
        elif week == 'two_weeks':
            query = query.filter_by(week_number=week_num-2)
        else:
            query = query.filter_by(week_number=week_num)
    
    homeworks = query.order_by(HomeworkAssignment.created_date.desc()).all()
    subjects = Subject.query.all()
    
    return render_template('student/view_homework.html', 
                         homeworks=homeworks,
                         subjects=subjects)

@app.route('/uploads/images/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({'status': 'ok', 'message': 'App is running!'}), 200

# Create database and default data
with app.app_context():
    db.create_all()
    
    # Create admin user
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
    
    # Create subjects
    if not Subject.query.first():
        subjects = [
            ('Mathematics', '5'), ('Mathematics', '6'), ('Mathematics', '7'),
            ('Mathematics', '8'), ('Mathematics', '9'), ('Mathematics', '10'),
            ('Mathematics', '11'), ('Mathematics', '12'),
            ('Physics', '9'), ('Physics', '10'), ('Physics', '11'), ('Physics', '12'),
            ('Chemistry', '9'), ('Chemistry', '10'), ('Chemistry', '11'), ('Chemistry', '12'),
            ('Biology', '9'), ('Biology', '10'), ('Biology', '11'), ('Biology', '12'),
        ]
        for name, level in subjects:
            db.session.add(Subject(name=name, class_level=level))
        db.session.commit()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
