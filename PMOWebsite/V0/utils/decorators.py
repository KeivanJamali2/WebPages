"""
Route Decorators

Decorators for route protection and access control.
"""

from functools import wraps
from flask import session, redirect, url_for, flash, abort
from typing import Callable, List, Optional


def require_login(f: Callable) -> Callable:
    """
    Decorator to require user login for a route.
    
    If user is not logged in, redirects to login page.
    
    Usage:
        @app.route('/dashboard')
        @require_login
        def dashboard():
            return render_template('dashboard.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def require_role(required_role: str) -> Callable:
    """
    Decorator to require a specific role for a route.
    
    Args:
        required_role: Role required to access the route (e.g., 'admin', 'employee')
    
    Usage:
        @app.route('/admin')
        @require_login
        @require_role('admin')
        def admin_dashboard():
            return render_template('admin.html')
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is logged in
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            # Check if user has required role
            user_role = session.get('user_role', '')
            if user_role != required_role.lower():
                flash(f'Access denied. This page requires {required_role} role.', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_any_role(required_roles: List[str]) -> Callable:
    """
    Decorator to require any of the specified roles for a route.
    
    Args:
        required_roles: List of acceptable roles
    
    Usage:
        @app.route('/reports')
        @require_login
        @require_any_role(['admin', 'manager'])
        def reports():
            return render_template('reports.html')
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is logged in
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            # Check if user has any of the required roles
            user_role = session.get('user_role', '')
            if user_role not in [r.lower() for r in required_roles]:
                flash(f'Access denied. This page requires one of: {", ".join(required_roles)}', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def guest_only(f: Callable) -> Callable:
    """
    Decorator to allow only guests (non-logged-in users).
    
    If user is logged in, redirects to dashboard.
    Useful for login and registration pages.
    
    Usage:
        @app.route('/login')
        @guest_only
        def login():
            return render_template('login.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            return redirect(url_for('dashboard.home'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user_id() -> Optional[str]:
    """
    Get the current logged-in user's ID from session.
    
    Returns:
        User ID if logged in, None otherwise
    """
    return session.get('user_id')


def get_current_user_role() -> Optional[str]:
    """
    Get the current logged-in user's role from session.
    
    Returns:
        User role if logged in, None otherwise
    """
    return session.get('user_role')


def get_current_user_name() -> Optional[str]:
    """
    Get the current logged-in user's name from session.
    
    Returns:
        User name if logged in, None otherwise
    """
    return session.get('user_name')


def is_logged_in() -> bool:
    """
    Check if a user is currently logged in.
    
    Returns:
        True if user is logged in, False otherwise
    """
    return 'user_id' in session


def is_admin() -> bool:
    """
    Check if the current user is an admin.
    
    Returns:
        True if user is admin, False otherwise
    """
    return session.get('user_role') == 'admin'
