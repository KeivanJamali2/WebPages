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
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
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


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
