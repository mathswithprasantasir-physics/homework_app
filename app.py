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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'homework-app-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///homework.db'
app.config['UPLOAD_FOLDER'] = 'uploads/images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ==================== MODELS ====================

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
    question_type = db.Column(db.String(20), nullable=False)  # MCQ, SAQ, VSAQ, LAQ
    question_text = db.Column(db.Text, nullable=False)
    question_latex = db.Column(db.Text)
    options = db.Column(db.Text)  # JSON for MCQ
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
    questions = db.Column(db.Text)  # JSON array of question IDs
    total_marks = db.Column(db.Integer)
    due_date = db.Column(db.DateTime)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    week_number = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    subject = db.relationship('Subject', backref='assignments')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ==================== HELPER FUNCTIONS ====================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_week_number():
    return datetime.utcnow().isocalendar()[1]

def get_week_label(week_offset=0):
    labels = {0: "This Week", 1: "Last Week", 2: "2 Weeks Ago", 3: "3 Weeks Ago"}
    return labels.get(week_offset, f"{week_offset} Weeks Ago")

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
    
    query = HomeworkAssignment.query.filter_by(is_active=True)
    
    if class_level:
        query = query.filter_by(class_level=class_level)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if week_filter:
        current_week = get_week_number()
        if week_filter == 'last':
            query = query.filter_by(week_number=current_week - 1)
        elif week_filter == 'two_weeks':
            query = query.filter_by(week_number=current_week - 2)
        elif week_filter == 'three_weeks':
            query = query.filter_by(week_number=current_week - 3)
        else:
            query = query.filter_by(week_number=current_week)
    
    homeworks = query.order_by(HomeworkAssignment.created_date.desc()).all()
    subjects = Subject.query.all()
    
    # Get unique class levels
    class_levels = sorted(list(set([str(i) for i in range(5, 13)])))
    
    return render_template('public_homework.html',
                         homeworks=homeworks,
                         subjects=subjects,
                         class_levels=class_levels,
                         selected_class=class_level,
                         selected_subject=subject_id,
                         week_filter=week_filter)

@app.route('/homework/<int:homework_id>')
def view_homework_detail(homework_id):
    """View homework details - no login required"""
    homework = HomeworkAssignment.query.get_or_404(homework_id)
    question_ids = json.loads(homework.questions) if homework.questions else []
    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    
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
        user = User.query.filter_by(username=username).first()
        
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
    
    total_questions = Question.query.count()
    total_homeworks = HomeworkAssignment.query.count()
    total_subjects = Subject.query.count()
    recent_questions = Question.query.order_by(Question.created_date.desc()).limit(10).all()
    recent_homeworks = HomeworkAssignment.query.order_by(HomeworkAssignment.created_date.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_questions=total_questions,
                         total_homeworks=total_homeworks,
                         total_subjects=total_subjects,
                         recent_questions=recent_questions,
                         recent_homeworks=recent_homeworks)

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
                    'A': request.form.get('option_a', ''),
                    'B': request.form.get('option_b', ''),
                    'C': request.form.get('option_c', ''),
                    'D': request.form.get('option_d', ''),
                    'correct': request.form.get('correct_option', 'A')
                }
                question.options = json.dumps(options)
            
            # Handle image upload
            if 'question_image' in request.files:
                file = request.files['question_image']
                if file and file.filename and allowed_file(file.filename):
                    filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    question.image_path = filename
            
            db.session.add(question)
            db.session.commit()
            flash('✅ Question added successfully!', 'success')
            return redirect(url_for('add_question'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error: {str(e)}', 'error')
    
    subjects = Subject.query.order_by(Subject.class_level, Subject.name).all()
    return render_template('admin/add_question.html', subjects=subjects)

@app.route('/admin/create_homework', methods=['GET', 'POST'])
@login_required
def create_homework():
    if not current_user.is_admin:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
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
            flash('✅ Homework created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error: {str(e)}', 'error')
    
    subjects = Subject.query.all()
    return render_template('admin/create_homework.html', subjects=subjects)

@app.route('/admin/get_questions')
@login_required
def get_questions_api():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    subject_id = request.args.get('subject_id', '')
    class_level = request.args.get('class_level', '')
    question_type = request.args.get('question_type', '')
    
    # Get subject's class level
    if subject_id:
        subject = db.session.get(Subject, int(subject_id))
        if subject:
            class_level = subject.class_level
    
    query = Question.query.filter_by(is_active=True)
    
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if question_type:
        query = query.filter_by(question_type=question_type)
    
    questions = query.order_by(Question.created_date.desc()).limit(50).all()
    
    return jsonify([{
        'id': q.id,
        'text': q.question_text[:100] + ('...' if len(q.question_text) > 100 else ''),
        'type': q.question_type,
        'marks': q.marks,
        'difficulty': q.difficulty,
        'subject': q.subject.name,
        'class': q.subject.class_level
    } for q in questions])

@app.route('/admin/manage_questions')
@login_required
def manage_questions():
    if not current_user.is_admin:
        return redirect(url_for('login'))
    
    questions = Question.query.order_by(Question.created_date.desc()).all()
    return render_template('admin/manage_questions.html', questions=questions)

@app.route('/admin/delete_question/<int:question_id>')
@login_required
def delete_question(question_id):
    if not current_user.is_admin:
        return redirect(url_for('login'))
    
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted!', 'success')
    return redirect(url_for('manage_questions'))

# ==================== FILE SERVING ====================

@app.route('/uploads/images/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==================== HEALTH CHECK ====================

@app.route('/health')
def health_check():
    return jsonify({'status': 'ok', 'message': 'Homework App is running!'})

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# ==================== INITIALIZE DATABASE ====================

with app.app_context():
    db.create_all()
    
    # Create admin user
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created!")
    
    # Create subjects if not exists
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
            db.session.add(Subject(name=name, class_level=level))
        db.session.commit()
        print("✅ Subjects created!")

# ==================== RUN APP ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)