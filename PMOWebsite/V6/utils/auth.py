"""
Authentication utilities - decorators and user verification.
"""
import os
import csv
from functools import wraps
from flask import session, redirect, url_for, flash, request, g
from datetime import datetime
from translations import get_translation


def get_t():
    """Get translation function for current language."""
    lang = session.get('lang', 'en')
    return lambda key: get_translation(key, lang)


def load_users_from_file(filepath):
    """Load users from user.txt file.
    
    Supports formats:
    New: username_english,username_persian,password,phone_number,national_id,email,role
    Old Full: username,password,phone_number,national_id,email,role
    Simple: username,password,role
    """
    users = {}
    if not os.path.exists(filepath):
        return users
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            # Skip header and comments
            if not row or row[0].startswith('#'):
                continue
            
            if len(row) >= 7:
                # New format with Persian username
                username = row[0].strip()
                username_persian = row[1].strip()
                users[username] = {
                    'username': username,
                    'username_persian': username_persian,
                    'password': row[2].strip(),
                    'phone_number': row[3].strip(),
                    'national_id': row[4].strip(),
                    'email': row[5].strip(),
                    'role': row[6].strip().lower()
                }
                # Also allow login with Persian username
                users[username_persian] = users[username]
            elif len(row) >= 6:
                # Old full format (no Persian username)
                username = row[0].strip()
                users[username] = {
                    'username': username,
                    'username_persian': '',
                    'password': row[1].strip(),
                    'phone_number': row[2].strip(),
                    'national_id': row[3].strip(),
                    'email': row[4].strip(),
                    'role': row[5].strip().lower()
                }
            elif len(row) >= 3:
                # Simple format
                username = row[0].strip()
                users[username] = {
                    'username': username,
                    'username_persian': '',
                    'password': row[1].strip(),
                    'phone_number': '',
                    'national_id': '',
                    'email': '',
                    'role': row[2].strip().lower()
                }
    return users


def verify_user(username, password, users_dict):
    """Verify user credentials."""
    if username in users_dict:
        if users_dict[username]['password'] == password:
            return users_dict[username]
    return None


def get_current_user():
    """Get current logged-in user from session."""
    return session.get('user', None)


def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            t = get_t()
            flash(t('please_login'), 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def boss_required(f):
    """Decorator to require boss role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            t = get_t()
            flash(t('please_login'), 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if session['user']['role'] != 'boss':
            t = get_t()
            flash(t('boss_required'), 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            t = get_t()
            flash(t('please_login'), 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if session['user']['role'] not in ['admin', 'boss']:
            t = get_t()
            flash(t('admin_required'), 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def employee_required(f):
    """Decorator to require employee role (any logged-in user)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            t = get_t()
            flash(t('please_login'), 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_only(f):
    """Decorator to require specifically admin role (not boss)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            t = get_t()
            flash(t('please_login'), 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if session['user']['role'] != 'admin':
            t = get_t()
            flash(t('admin_required'), 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def can_view_form(form, user):
    """Check if user can view a specific form."""
    if user['role'] in ['boss', 'admin']:
        return True
    # Employees can only view their own forms
    return form.submitted_by_user.username == user['username']


def can_edit_form(form, user):
    """Check if user can edit a specific form."""
    # Only the submitter can edit, and only if draft
    if form.submitted_by_user.username != user['username']:
        return False
    return form.status == 'draft'


def can_review_form(form, user):
    """Check if user can review/approve/reject a form."""
    return user['role'] == 'admin' and form.status == 'pending'
