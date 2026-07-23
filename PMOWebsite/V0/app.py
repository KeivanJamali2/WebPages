"""
PMO Website - Main Application

A modular Project Management Office website with user authentication,
dynamic forms, and data analytics capabilities.
"""

from flask import Flask, render_template, redirect, url_for
import logging
from pathlib import Path

# Import configuration
from config import get_config, ensure_directories, BASE_DIR, USERS_FILE, PROJECTS_FILE

# Import database
from database import NetworkXDatabase

# Import utilities
from utils.data_loader import initialize_database

# Import blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.settings import settings_bp
from routes.language import language_bp
from routes.forms import forms_bp


def create_app(config_name='development'):
    """
    Application factory function.
    
    Args:
        config_name: Configuration environment (development, production, testing)
    
    Returns:
        Configured Flask application
    """
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Ensure required directories exist
    ensure_directories()
    
    # Setup logging
    setup_logging(app)
    
    # Initialize database
    db = initialize_app_database(app)
    app.config['db'] = db
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Add template context processors
    register_context_processors(app)
    
    # Root route
    @app.route('/')
    def index():
        """Redirect root to login page."""
        return redirect(url_for('auth.login'))
    
    app.logger.info('PMO Website initialized successfully')
    
    return app


def setup_logging(app):
    """Setup application logging."""
    log_level = getattr(logging, app.config['LOG_LEVEL'], logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_file = Path(app.config['LOG_FILE'])
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    app.logger.setLevel(log_level)
    app.logger.info('Logging configured')


def initialize_app_database(app):
    """
    Initialize and populate database.
    
    Args:
        app: Flask application
    
    Returns:
        Database instance
    """
    app.logger.info('Initializing database...')
    
    # Create database instance
    # In future, this can be switched to Neo4j by checking app.config['DATABASE_TYPE']
    db = NetworkXDatabase()
    
    # Load initial data from files
    if USERS_FILE.exists():
        app.logger.info(f'Loading users from {USERS_FILE}')
        result = initialize_database(
            db,
            str(USERS_FILE),
            str(PROJECTS_FILE) if PROJECTS_FILE.exists() else None
        )
        app.logger.info(f"Database initialized: {result}")
    else:
        app.logger.warning(f'Users file not found: {USERS_FILE}')
    
    return db


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(language_bp)
    app.register_blueprint(forms_bp)
    # Note: forms_bp and projects_bp will be added later
    
    app.logger.info('Blueprints registered')


def register_error_handlers(app):
    """Register error handlers for common HTTP errors."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 forbidden errors."""
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 internal server errors."""
        app.logger.error(f'Internal server error: {error}')
        return render_template('errors/500.html'), 500
    
    app.logger.info('Error handlers registered')


def register_context_processors(app):
    """Register template context processors."""
    
    @app.context_processor
    def utility_processor():
        """Make utility functions available in all templates."""
        from flask import session
        from utils.i18n import translate, get_locale, get_direction, format_date, format_number
        
        def is_logged_in():
            return 'user_id' in session
        
        def get_user_name():
            return session.get('user_name', 'Guest')
        
        def get_user_role():
            return session.get('user_role', '')
        
        def is_admin():
            return session.get('user_role') == 'admin'
        
        return {
            'is_logged_in': is_logged_in,
            'get_user_name': get_user_name,
            'get_user_role': get_user_role,
            'is_admin': is_admin,
            '_': translate,
            'get_locale': get_locale,
            'get_direction': get_direction,
            'format_date': format_date,
            'format_number': format_number,
        }
    
    app.logger.info('Context processors registered')


# Create application instance
app = create_app()


if __name__ == '__main__':
    print("=" * 60)
    print("PMO Website - Development Server")
    print("=" * 60)
    print("Server starting on http://127.0.0.1:5000")
    print("Press CTRL+C to quit")
    print("=" * 60)
    
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )
