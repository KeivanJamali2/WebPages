"""
Configuration settings for the PMO Website application.
"""
import os

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'pmo-website-secret-key-change-in-production'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'data', 'pmo.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # User file path
    USER_FILE = os.path.join(BASE_DIR, 'user.txt')
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'uploads')
    FORM_DOCUMENTS_FOLDER = os.path.join(BASE_DIR, 'data', 'form_documents')
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200MB max total upload size
    MAX_DOCUMENT_SIZE = 200 * 1024 * 1024  # 200MB max for form documents
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'doc', 'docx', 'zip', 'rar'}
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds
    
    # Default language
    DEFAULT_LANGUAGE = 'en'
    SUPPORTED_LANGUAGES = ['en', 'fa']


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
    # Security settings for HTTPS
    SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to cookies
    SESSION_COOKIE_SAMESITE = 'Lax'  # Protect against CSRF
    
    # Ensure you set a strong SECRET_KEY in environment variables
    # export SECRET_KEY='your-very-long-random-secret-key'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
