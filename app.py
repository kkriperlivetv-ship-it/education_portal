from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///education_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Модели БД
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    is_instructor = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    courses_created = db.relationship('Course', backref='instructor', lazy=True)
    enrollments = db.relationship('Enrollment', backref='student', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    
    courses = db.relationship('Course', backref='category_ref', lazy=True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    price = db.Column(db.Float, default=0.00)
    duration_hours = db.Column(db.Integer)
    difficulty_level = db.Column(db.String(20), default='beginner')
    image_url = db.Column(db.String(255))
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    lessons = db.relationship('Lesson', backref='course', lazy=True)
    enrollments = db.relationship('Enrollment', backref='course', lazy=True)

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    video_url = db.Column(db.String(255))
    duration_minutes = db.Column(db.Integer)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    progress_percent = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Создаем тестовые данные при первом запуске
def create_sample_data():
    # Проверяем, есть ли уже категории
    if Category.query.count() == 0:
        categories = [
            Category(name='Дизайн', description='Курсы по веб-дизайну, UI/UX', icon='palette'),
            Category(name='Игры', description='Создание игр, геймдизайн', icon='gamepad'),
            Category(name='Программирование', description='Веб и мобильная разработка', icon='code'),
        ]
        for cat in categories:
            db.session.add(cat)
        
        # Создаем тестового пользователя если нет
        if User.query.filter_by(username='admin').first() is None:
            admin = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin123'),
                full_name='Администратор',
                is_admin=True
            )
            db.session.add(admin)
        
        db.session.commit()

# Профиль пользователя
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', '')
        current_user.email = request.form.get('email', '')
        
        new_password = request.form.get('password', '')
        if new_password:
            current_user.password = generate_password_hash(new_password)
        
        db.session.commit()
        flash('Профиль обновлен!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

# Админ-панель
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

# Маршруты (упрощенные версии)
@app.route('/')
def index():
    courses = Course.query.filter_by(is_published=True).limit(6).all()
    categories = Category.query.all()
    return render_template('index.html', courses=courses, categories=categories)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form.get('full_name', '')
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Пользователь уже существует!', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            full_name=full_name,
            is_instructor=True
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        flash('Регистрация успешна!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Вход выполнен!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверные данные!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_courses = Course.query.filter_by(instructor_id=current_user.id).all()
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', 
                         created_courses=user_courses,
                         enrollments=enrollments)

@app.route('/courses')
def courses():
    all_courses = Course.query.filter_by(is_published=True).all()
    categories = Category.query.all()
    return render_template('courses.html', courses=all_courses, categories=categories)

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
    
    return render_template('course_detail.html', course=course, is_enrolled=is_enrolled)

@app.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if not enrollment:
        new_enrollment = Enrollment(
            user_id=current_user.id,
            course_id=course_id
        )
        db.session.add(new_enrollment)
        db.session.commit()
        flash('Вы записались на курс!', 'success')
    
    return redirect(url_for('dashboard'))

@app.route('/create-course', methods=['GET', 'POST'])
@login_required
def create_course():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category_id = request.form.get('category_id')
        price = request.form.get('price', 0)
        
        course = Course(
            title=title,
            description=description,
            category_id=category_id if category_id else None,
            instructor_id=current_user.id,
            price=float(price) if price else 0.00
        )
        
        db.session.add(course)
        db.session.commit()
        
        flash('Курс создан!', 'success')
        return redirect(url_for('dashboard'))
    
    categories = Category.query.all()
    return render_template('create_course.html', categories=categories)

@app.route('/edit-course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    if course.instructor_id != current_user.id:
        flash('Нельзя редактировать чужой курс!', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        course.title = request.form['title']
        course.description = request.form['description']
        course.category_id = request.form.get('category_id')
        course.price = request.form.get('price', 0)
        course.difficulty_level = request.form.get('difficulty_level', 'beginner')
        
        db.session.commit()
        flash('Курс обновлен!', 'success')
        return redirect(url_for('dashboard'))
    
    categories = Category.query.all()
    return render_template('edit_course.html', course=course, categories=categories)

@app.route('/delete-course/<int:course_id>', methods=['POST'])
@login_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    if course.instructor_id != current_user.id:
        flash('Нельзя удалить чужой курс!', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(course)
    db.session.commit()
    flash('Курс удален!', 'info')
    return redirect(url_for('dashboard'))

@app.route('/my-courses')
@login_required
def my_courses():
    created_courses = Course.query.filter_by(instructor_id=current_user.id).all()
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    enrolled_courses = [e.course for e in enrollments]
    
    return render_template('my_courses.html', 
                         created_courses=created_courses,
                         enrolled_courses=enrolled_courses)

# Создаем БД и тестовые данные при запуске
with app.app_context():
    db.create_all()
    create_sample_data()

if __name__ == '__main__':
    app.run()