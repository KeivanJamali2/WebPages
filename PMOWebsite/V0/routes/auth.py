"""
Authentication Routes

Handles user login and logout functionality.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models.user import authenticate_user, get_user_by_id
from utils.decorators import guest_only
from utils.i18n import translate as _

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
@guest_only
def login():
    """
    Handle user login.
    
    GET: Display login form
    POST: Process login credentials
    """
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        
        # Validate input
        if not identifier or not password:
            flash(_('messages.provide_credentials'), 'danger')
            return render_template('auth/login.html')
        
        # Get database from app context
        db = current_app.config['db']
        
        # Authenticate user
        user = authenticate_user(db, identifier, password)
        
        if user:
            # Store user info in session
            session['user_id'] = user.email
            session['user_name'] = user.name
            session['user_role'] = user.role
            session.permanent = False
            
            flash(_('messages.welcome_back').format(name=user.name), 'success')
            
            # Redirect based on role
            if user.is_admin():
                return redirect(url_for('dashboard.admin'))
            else:
                return redirect(url_for('dashboard.home'))
        else:
            flash(_('messages.invalid_credentials'), 'danger')
            return render_template('auth/login.html')
    
    # GET request - show login form
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """Handle user logout."""
    user_name = session.get('user_name', _('common.user'))
    
    # Clear session
    session.clear()
    
    flash(_('messages.goodbye').format(name=user_name), 'info')
    return redirect(url_for('auth.login'))
