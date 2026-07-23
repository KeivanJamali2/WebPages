"""
Main routes - dashboard and common pages.
"""
from flask import Blueprint, render_template, session, redirect, url_for
from utils.auth import login_required, get_current_user
from models import db, User, Project, DailyFormSubmission, Notification

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page - redirect to login or dashboard."""
    if 'user' in session:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - different view based on role."""
    user = get_current_user()
    lang = session.get('lang', 'en')
    
    # Get user from database
    db_user = User.query.filter_by(username=user['username']).first()
    
    # Get statistics based on role
    stats = get_dashboard_stats(user, db_user)
    
    # Get recent forms
    recent_forms = get_recent_forms(user, db_user, limit=5)
    
    # Get unread notifications count
    unread_count = 0
    if db_user:
        unread_count = Notification.query.filter_by(
            user_id=db_user.id, 
            is_read=False
        ).count()
    
    return render_template(
        'dashboard.html',
        user=user,
        stats=stats,
        recent_forms=recent_forms,
        unread_count=unread_count,
        lang=lang
    )


def get_dashboard_stats(user, db_user):
    """Get statistics for dashboard based on user role."""
    stats = {}
    
    if user['role'] == 'boss':
        # Boss sees everything
        stats['total_forms'] = DailyFormSubmission.query.count()
        stats['pending_forms'] = DailyFormSubmission.query.filter_by(status='pending').count()
        stats['approved_forms'] = DailyFormSubmission.query.filter_by(status='approved').count()
        stats['rejected_forms'] = DailyFormSubmission.query.filter_by(status='rejected').count()
        stats['total_projects'] = Project.query.filter_by(is_active=True).count()
        stats['total_employees'] = User.query.filter_by(role='employee').count()
        
    elif user['role'] == 'admin':
        # Admin sees all forms
        stats['total_forms'] = DailyFormSubmission.query.count()
        stats['pending_forms'] = DailyFormSubmission.query.filter_by(status='pending').count()
        stats['approved_forms'] = DailyFormSubmission.query.filter_by(status='approved').count()
        stats['rejected_forms'] = DailyFormSubmission.query.filter_by(status='rejected').count()
        stats['total_projects'] = Project.query.filter_by(is_active=True).count()
        
    else:
        # Employee sees only their forms
        if db_user:
            stats['total_forms'] = DailyFormSubmission.query.filter_by(submitted_by=db_user.id).count()
            stats['pending_forms'] = DailyFormSubmission.query.filter_by(
                submitted_by=db_user.id, status='pending'
            ).count()
            stats['approved_forms'] = DailyFormSubmission.query.filter_by(
                submitted_by=db_user.id, status='approved'
            ).count()
            stats['rejected_forms'] = DailyFormSubmission.query.filter_by(
                submitted_by=db_user.id, status='rejected'
            ).count()
        else:
            stats = {'total_forms': 0, 'pending_forms': 0, 'approved_forms': 0, 'rejected_forms': 0}
    
    return stats


def get_recent_forms(user, db_user, limit=5):
    """Get recent forms based on user role."""
    query = DailyFormSubmission.query
    
    if user['role'] == 'employee' and db_user:
        query = query.filter_by(submitted_by=db_user.id)
    elif user['role'] == 'admin':
        # Admin sees pending forms first
        query = query.filter(DailyFormSubmission.status.in_(['pending', 'approved', 'rejected']))
    
    return query.order_by(DailyFormSubmission.created_at.desc()).limit(limit).all()
