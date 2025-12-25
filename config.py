import os
from dotenv import load_dotenv  # <-- Добавьте эту строку

# Загружаем переменные из .env файла
load_dotenv()

class Config:
    # Безопасность - берем из переменных окружения
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
    
    # Режим Flask
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
    
    # База данных
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///education_portal.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Загрузка файлов
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    
    # Почта (если нужно)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Прочее
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')