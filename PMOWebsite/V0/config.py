"""
Configuration Management

Centralized configuration for the PMO Website application.
"""

import os
from pathlib import Path


# Base directory (project root)
BASE_DIR = Path(__file__).parent.absolute()

# Data directories
DATA_DIR = BASE_DIR / 'data'
SUBMISSIONS_DIR = DATA_DIR / 'submissions'
BACKUPS_DIR = DATA_DIR / 'backups'
LOGS_DIR = BASE_DIR / 'logs'

# Data files
USERS_FILE = DATA_DIR / 'users.txt'
PROJECTS_FILE = DATA_DIR / 'projects.txt'

# Static and template directories
STATIC_DIR = BASE_DIR / 'static'
TEMPLATES_DIR = BASE_DIR / 'templates'

# Flask Configuration
class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Session settings
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour in seconds
    
    # Database settings
    DATABASE_TYPE = 'networkx'  # Change to 'neo4j' for production
    
    # Neo4j settings (for future use)
    NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'password')
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}
    
    # Logging settings
    LOG_FILE = LOGS_DIR / 'app.log'
    LOG_LEVEL = 'INFO'
    
    # Pagination settings
    ITEMS_PER_PAGE = 20
    
    # Date format
    DATE_FORMAT = '%Y-%m-%d'
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env: str = None) -> Config:
    """
    Get configuration based on environment.
    
    Args:
        env: Environment name (development, production, testing)
             If None, uses FLASK_ENV environment variable or 'default'
    
    Returns:
        Configuration class
    """
    if env is None:
        env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])


def ensure_directories():
    """
    Ensure all required directories exist.
    Creates directories if they don't exist.
    """
    directories = [
        DATA_DIR,
        SUBMISSIONS_DIR,
        BACKUPS_DIR,
        LOGS_DIR,
        STATIC_DIR / 'css',
        STATIC_DIR / 'js',
        STATIC_DIR / 'img',
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"[Config] Ensured directory: {directory}")


def get_submission_path(project_id: str, form_type: str, filename: str) -> Path:
    """
    Get the full path for a form submission file.
    
    Args:
        project_id: Project identifier
        form_type: Type of form
        filename: Name of the file
    
    Returns:
        Path object for the submission file
    """
    project_dir = SUBMISSIONS_DIR / project_id / form_type
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir / filename


if __name__ == '__main__':
    # Test configuration
    print("PMO Website Configuration")
    print("=" * 50)
    print(f"Base Directory: {BASE_DIR}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Users File: {USERS_FILE}")
    print(f"Projects File: {PROJECTS_FILE}")
    print(f"Submissions Directory: {SUBMISSIONS_DIR}")
    print(f"Backups Directory: {BACKUPS_DIR}")
    print(f"Logs Directory: {LOGS_DIR}")
    print("=" * 50)
    
    # Ensure directories exist
    ensure_directories()
    print("\nAll directories created successfully!")
