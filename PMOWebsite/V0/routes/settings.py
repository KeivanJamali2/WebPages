"""
Settings Routes

User settings and profile management.
"""

from flask import Blueprint, render_template, request, session, flash, redirect, url_for, current_app
from utils.decorators import require_login
from models.user import get_user_by_id, update_user_password
from models.form_submission import get_user_submissions
from utils.i18n import translate as _

# Create blueprint
settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


@settings_bp.route('/')
@require_login
def profile():
    """
    Display user profile and settings.
    """
    db = current_app.config['db']
    user_id = session.get('user_id')
    
    # Get user info
    user = get_user_by_id(db, user_id)
    
    if not user:
        flash(_('messages.user_not_found'), 'danger')
        return redirect(url_for('dashboard.home'))
    
    # Get user's submission history
    submissions = get_user_submissions(db, user_id)
    
    return render_template(
        'settings/profile.html',
        user=user,
        submissions=submissions
    )


@settings_bp.route('/change-password', methods=['POST'])
@require_login
def change_password():
    """
    Handle password change request.
    """
    db = current_app.config['db']
    user_id = session.get('user_id')
    
    # Get form data
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validate input
    if not all([current_password, new_password, confirm_password]):
        flash(_('messages.all_fields_required'), 'danger')
        return redirect(url_for('settings.profile'))
    
    # Check if new passwords match
    if new_password != confirm_password:
        flash(_('messages.passwords_not_match'), 'danger')
        return redirect(url_for('settings.profile'))
    
    # Get user and verify current password
    user = get_user_by_id(db, user_id)
    if not user or user.password != current_password:
        flash(_('messages.current_password_incorrect'), 'danger')
        return redirect(url_for('settings.profile'))
    
    # Update password
    success = update_user_password(db, user_id, new_password)
    
    if success:
        flash(_('messages.password_updated'), 'success')
    else:
        flash(_('messages.password_update_failed'), 'danger')
