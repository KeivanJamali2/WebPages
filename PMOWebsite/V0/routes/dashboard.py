"""
Dashboard Routes

Main dashboard views for users and admins.
"""

from flask import Blueprint, render_template, request, session, current_app
from utils.decorators import require_login, require_role
from models.form_submission import get_user_submissions, get_all_submissions
from models.project import get_all_projects

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/')
@dashboard_bp.route('/home')
@require_login
def home():
    """
    User dashboard - shows personalized information.
    """
    db = current_app.config['db']
    
    user_id = session.get('user_id')
    user_name = session.get('user_name')
    user_role = session.get('user_role')
    
    # Get user's submissions
    user_submissions = get_user_submissions(db, user_id)
    
    # Get all projects
    projects = get_all_projects(db)
    
    # Calculate stats
    stats = {
        'total_submissions': len(user_submissions),
        'total_projects': len(projects),
        'recent_submissions': user_submissions[-5:] if user_submissions else []
    }
    
    return render_template(
        'dashboard/home.html',
        user_name=user_name,
        user_role=user_role,
        stats=stats,
        projects=projects
    )


@dashboard_bp.route('/admin')
@require_login
@require_role('admin')
def admin():
    """
    Admin dashboard - shows system-wide statistics and analytics.
    """
    db = current_app.config['db']
    
    # Get all data for admin
    all_submissions = get_all_submissions(db)
    all_projects = get_all_projects(db)
    all_users = db.get_all_users()
    
    # Calculate statistics
    stats = {
        'total_users': len(all_users),
        'total_projects': len(all_projects),
        'total_submissions': len(all_submissions),
        'active_projects': len([p for p in all_projects if p.is_active()]),
        'recent_submissions': sorted(all_submissions, key=lambda x: x.timestamp, reverse=True)[:10]
    }
    
    # Get database stats
    if hasattr(db, 'get_stats'):
        db_stats = db.get_stats()
    else:
        db_stats = {}
    
    return render_template(
        'dashboard/admin.html',
        stats=stats,
        db_stats=db_stats,
        projects=all_projects,
        users=all_users
    )
