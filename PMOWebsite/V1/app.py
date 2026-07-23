"""
PMO Website - Main Application
Employee Performance Tracking System
"""
import os
import json
from flask import Flask, session, g
from config import config
from models import db
from translations import Translator, get_all_translations
from utils.jalali import register_jalali_filters


def create_app(config_name='default'):
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Register Jalali date filters
    register_jalali_filters(app)
    
    # Ensure data directory exists
    os.makedirs(os.path.join(app.config['BASE_DIR'], 'data'), exist_ok=True)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.forms import forms_bp
    from routes.projects import projects_bp
    from routes.analytics import analytics_bp
    from routes.notifications import notifications_bp
    from routes.export import export_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(forms_bp, url_prefix='/forms')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(export_bp, url_prefix='/export')
    
    # Context processor for templates
    @app.context_processor
    def inject_globals():
        lang = session.get('lang', 'en')
        translator = Translator(lang)
        user = session.get('user', None)
        
        # Get unread notifications count
        unread_count = 0
        if user:
            from models import User, Notification
            db_user = User.query.filter_by(username=user['username']).first()
            if db_user:
                unread_count = Notification.query.filter_by(
                    user_id=db_user.id,
                    is_read=False
                ).count()
        
        return {
            't': translator,
            'lang': lang,
            'user': user,
            'unread_count': unread_count,
            'translations_json': json.dumps(get_all_translations(lang))
        }
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Sync users from user.txt
        from routes.auth import sync_all_users
        sync_all_users()
        
        # Sync projects from configuration
        sync_projects()
    
    return app


def sync_projects():
    """Sync projects from project_configuration.py to database."""
    from models import Project
    from Projects.project_configuration import projects
    
    for code, data in projects.items():
        project = Project.query.filter_by(project_code=code).first()
        
        if not project:
            # Parse dates
            from datetime import datetime
            start_date = None
            end_date = None
            is_ongoing = False
            
            if data.get('start_date'):
                try:
                    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                except:
                    pass
            
            if data.get('end_date'):
                if data['end_date'] == 'On-Going':
                    is_ongoing = True
                else:
                    try:
                        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
                    except:
                        pass
            
            project = Project(
                project_code=code,
                name=data.get('name', ''),
                location=data.get('location', ''),
                contract_number=data.get('contract_number', ''),
                start_date=start_date,
                end_date=end_date,
                is_ongoing=is_ongoing,
                budget=data.get('budget'),
                owner=data.get('Owner', ''),
                manager=data.get('manager', '')
            )
            db.session.add(project)
    
    db.session.commit()


# Run the application
if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5000)
