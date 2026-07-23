"""
Authentication routes - login, logout, language switching.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from datetime import datetime
from utils.auth import load_users_from_file, verify_user
from models import db, User
from translations import get_translation

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication."""
    # If already logged in, redirect to dashboard
    if 'user' in session:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Load users from file
        users = load_users_from_file(current_app.config['USER_FILE'])
        
        # Verify credentials
        user_data = verify_user(username, password, users)
        
        if user_data:
            # Store user in session
            session['user'] = user_data
            session.permanent = True
            
            # Sync user to database if not exists
            sync_user_to_db(user_data)
            
            # Update last login
            db_user = User.query.filter_by(username=username).first()
            if db_user:
                db_user.last_login = datetime.utcnow()
                db.session.commit()
            
            lang = session.get('lang', 'en')
            t = lambda key: get_translation(key, lang)
            flash(t('login_successful'), 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            lang = session.get('lang', 'en')
            t = lambda key: get_translation(key, lang)
            flash(t('invalid_credentials'), 'danger')
    
    lang = session.get('lang', 'en')
    return render_template('auth/login.html', lang=lang)


@auth_bp.route('/logout')
def logout():
    """Logout and clear session."""
    lang = session.get('lang', 'en')
    t = lambda key: get_translation(key, lang)
    session.pop('user', None)
    flash(t('logged_out'), 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/set-language/<lang>', methods=['POST'])
def set_language(lang):
    """Set the user's preferred language."""
    if lang in ['en', 'fa']:
        session['lang'] = lang
        return jsonify({'success': True, 'lang': lang})
    return jsonify({'success': False, 'error': 'Invalid language'}), 400


def sync_user_to_db(user_data):
    """Sync user from user.txt to database."""
    db_user = User.query.filter_by(username=user_data['username']).first()
    
    if not db_user:
        db_user = User(
            username=user_data['username'],
            password=user_data['password'],
            phone_number=user_data.get('phone_number'),
            national_id=user_data.get('national_id'),
            email=user_data.get('email'),
            role=user_data['role']
        )
        db.session.add(db_user)
        db.session.commit()
    else:
        # Update existing user data
        db_user.password = user_data['password']
        db_user.phone_number = user_data.get('phone_number')
        db_user.national_id = user_data.get('national_id')
        db_user.email = user_data.get('email')
        db_user.role = user_data['role']
        db.session.commit()
    
    return db_user


def sync_all_users():
    """Sync all users from user.txt to database."""
    from flask import current_app
    users = load_users_from_file(current_app.config['USER_FILE'])
    
    for username, user_data in users.items():
        sync_user_to_db(user_data)
