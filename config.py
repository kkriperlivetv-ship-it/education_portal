import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this'
    
    # ИЗМЕНЕНИЕ: Используем SQLite вместо MySQL
    SQLALCHEMY_DATABASE_URI = 'sqlite:///education_portal.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False