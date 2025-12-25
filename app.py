from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import config

app = Flask(__name__)
app.config.from_object(config.Config)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Модели базы данных
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    avatar_url = db.Column(db.String(255), default='default_avatar.png')
    is_instructor = db.Column(db.Boolean, default=True)  # Все пользователи могут быть инструкторами
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    
    courses_created = db.relationship('Course', backref='instructor', lazy=True)
    enrollments = db.relationship('Enrollment', backref='student', lazy=True)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    
    courses = db.relationship('Course', backref='category', lazy=True)

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    price = db.Column(db.Numeric(10, 2), default=0.00)
    duration_hours = db.Column(db.Integer)
    difficulty_level = db.Column(db.Enum('beginner', 'intermediate', 'advanced'), default='beginner')
    image_url = db.Column(db.String(255))
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    lessons = db.relationship('Lesson', backref='course', lazy=True, order_by='Lesson.order_index')
    enrollments = db.relationship('Enrollment', backref='course', lazy=True)

class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    video_url = db.Column(db.String(255))
    duration_minutes = db.Column(db.Integer)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrolled_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    progress_percent = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.TIMESTAMP)
    
    lesson_progress = db.relationship('LessonProgress', backref='enrollment', lazy=True)

class LessonProgress(db.Model):
    __tablename__ = 'lesson_progress'
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollments.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.TIMESTAMP)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    categories = Category.query.all()
    featured_courses = Course.query.filter_by(is_published=True).order_by(db.func.random()).limit(6).all()
    return render_template('index.html', categories=categories, featured_courses=featured_courses)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Пользователь с таким именем или email уже существует!', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password, method='scrypt')
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            full_name=full_name,
            is_instructor=True  # Все новые пользователи могут создавать курсы
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверное имя пользователя или пароль!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    enrolled_courses = [enrollment.course for enrollment in user_enrollments]
    created_courses = Course.query.filter_by(instructor_id=current_user.id).all()
    
    return render_template('dashboard.html', 
                         enrolled_courses=enrolled_courses,
                         created_courses=created_courses,
                         user_enrollments=user_enrollments)

@app.route('/my-courses')
@login_required
def my_courses():
    created_courses = Course.query.filter_by(instructor_id=current_user.id).all()
    user_enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    enrolled_courses = [enrollment.course for enrollment in user_enrollments]
    
    return render_template('my_courses.html', 
                         created_courses=created_courses,
                         enrolled_courses=enrolled_courses)

@app.route('/courses')
def courses():
    category_id = request.args.get('category_id', type=int)
    search_query = request.args.get('search', '')
    
    query = Course.query.filter_by(is_published=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search_query:
        query = query.filter(Course.title.contains(search_query) | Course.description.contains(search_query))
    
    all_courses = query.order_by(Course.created_at.desc()).all()
    categories = Category.query.all()
    
    return render_template('courses.html', 
                         courses=all_courses, 
                         categories=categories,
                         selected_category=category_id,
                         search_query=search_query)

@app.route('/course/<int:course_id>')
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    is_enrolled = False
    
    if current_user.is_authenticated:
        enrollment = Enrollment.query.filter_by(
            user_id=current_user.id, 
            course_id=course_id
        ).first()
        is_enrolled = enrollment is not None
    
    return render_template('course_detail.html', 
                         course=course, 
                         is_enrolled=is_enrolled)

@app.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    existing_enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if existing_enrollment:
        flash('Вы уже записаны на этот курс!', 'info')
        return redirect(url_for('course_detail', course_id=course_id))
    
    new_enrollment = Enrollment(
        user_id=current_user.id,
        course_id=course_id,
        progress_percent=0
    )
    
    db.session.add(new_enrollment)
    db.session.commit()
    
    flash(f'Вы успешно записались на курс "{course.title}"!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/create-course', methods=['GET', 'POST'])
@login_required
def create_course():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category_id = request.form.get('category_id')
        price = request.form.get('price', 0)
        duration_hours = request.form.get('duration_hours')
        difficulty_level = request.form.get('difficulty_level', 'beginner')
        
        new_course = Course(
            title=title,
            description=description,
            category_id=int(category_id) if category_id else None,
            instructor_id=current_user.id,
            price=float(price) if price else 0.00,
            duration_hours=int(duration_hours) if duration_hours else None,
            difficulty_level=difficulty_level,
            image_url=request.form.get('image_url', ''),
            is_published=True
        )
        
        db.session.add(new_course)
        db.session.commit()
        
        # Создаем уроки, если они есть
        lesson_titles = request.form.getlist('lesson_title[]')
        lesson_contents = request.form.getlist('lesson_content[]')
        
        for i, title in enumerate(lesson_titles):
            if title.strip():
                lesson = Lesson(
                    course_id=new_course.id,
                    title=title,
                    content=lesson_contents[i] if i < len(lesson_contents) else '',
                    order_index=i
                )
                db.session.add(lesson)
        
        db.session.commit()
        flash('Курс успешно создан и опубликован!', 'success')
        return redirect(url_for('my_courses'))
    
    categories = Category.query.all()
    return render_template('create_course.html', categories=categories)

@app.route('/edit-course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    if course.instructor_id != current_user.id:
        flash('Вы не можете редактировать этот курс!', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        course.title = request.form['title']
        course.description = request.form['description']
        course.category_id = request.form.get('category_id')
        course.price = request.form.get('price', 0)
        course.duration_hours = request.form.get('duration_hours')
        course.difficulty_level = request.form.get('difficulty_level', 'beginner')
        course.image_url = request.form.get('image_url', '')
        
        # Обновляем существующие уроки
        lesson_ids = request.form.getlist('lesson_id[]')
        lesson_titles = request.form.getlist('lesson_title[]')
        lesson_contents = request.form.getlist('lesson_content[]')
        lesson_durations = request.form.getlist('lesson_duration[]')
        lesson_videos = request.form.getlist('lesson_video[]')
        
        for i, lesson_id in enumerate(lesson_ids):
            if lesson_id:
                lesson = Lesson.query.get(lesson_id)
                if lesson and lesson.course_id == course.id:
                    lesson.title = lesson_titles[i]
                    lesson.content = lesson_contents[i]
                    lesson.duration_minutes = int(lesson_durations[i]) if lesson_durations[i] and lesson_durations[i].strip() else None
                    lesson.video_url = lesson_videos[i] if lesson_videos[i] and lesson_videos[i].strip() else None
        
        db.session.commit()
        flash('Курс успешно обновлен!', 'success')
        return redirect(url_for('course_detail', course_id=course.id))
    
    categories = Category.query.all()
    return render_template('edit_course.html', course=course, categories=categories)

@app.route('/delete-course/<int:course_id>', methods=['POST'])
@login_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    if course.instructor_id != current_user.id:
        flash('Вы не можете удалить этот курс!', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        db.session.delete(course)
        db.session.commit()
        flash('Курс успешно удален!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при удалении курса!', 'danger')
    
    return redirect(url_for('my_courses'))

@app.route('/delete-lesson/<int:lesson_id>', methods=['POST'])
@login_required
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = Course.query.get(lesson.course_id)
    
    if course.instructor_id != current_user.id:
        return jsonify({'success': False, 'error': 'Доступ запрещен'})
    
    try:
        db.session.delete(lesson)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form['full_name']
        current_user.email = request.form['email']
        
        if request.form['password']:
            current_user.password = generate_password_hash(request.form['password'], method='scrypt')
        
        db.session.commit()
        flash('Профиль обновлен!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Доступ запрещен!', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    courses = Course.query.all()
    enrollments = Enrollment.query.all()
    
    return render_template('admin.html', 
                         users=users, 
                         courses=courses, 
                         enrollments=enrollments)

@app.route('/api/course-progress/<int:course_id>')
@login_required
def get_course_progress(course_id):
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if not enrollment:
        return jsonify({'error': 'Not enrolled'}), 404
    
    return jsonify({
        'progress_percent': enrollment.progress_percent,
        'enrolled_at': enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
        'completed_at': enrollment.completed_at.isoformat() if enrollment.completed_at else None
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)