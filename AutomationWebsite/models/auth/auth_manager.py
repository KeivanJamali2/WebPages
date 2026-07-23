"""
Authentication Manager for email and password-based login system.
Users are manually registered in users.csv with email, name, password, and allowed tools.
Passwords are stored as plain text for simplicity.
"""

import pandas as pd
import os
from functools import wraps
from flask import session, redirect, url_for, flash
from typing import List, Optional, Dict


class AuthManager:
    """Manages user authentication and authorization based on email, password, and CSV file."""
    
    def __init__(self, users_csv_path: str):
        """
        Initialize the authentication manager.
        
        Args:
            users_csv_path: Path to the users.csv file containing user data
                           Format: email, name, password, allowed_tools
        """
        self.users_csv_path = users_csv_path
        self._users_cache = None
        self._load_users()
    
    def _load_users(self) -> None:
        """Load users from CSV file into memory."""
        try:
            if os.path.exists(self.users_csv_path):
                self._users_cache = pd.read_csv(self.users_csv_path)
            else:
                # Create default users file if it doesn't exist
                self._users_cache = pd.DataFrame(columns=['email', 'name', 'password', 'allowed_tools'])
                os.makedirs(os.path.dirname(self.users_csv_path), exist_ok=True)
                self._users_cache.to_csv(self.users_csv_path, index=False)
        except Exception as e:
            print(f"Error loading users: {e}")
            self._users_cache = pd.DataFrame(columns=['email', 'name', 'password', 'allowed_tools'])
    
    def reload_users(self) -> None:
        """Reload users from CSV file (useful after manual updates)."""
        self._load_users()
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, any]]:
        """
        Authenticate a user by email and password.
        
        Args:
            email: User's email address
            password: User's password (plain text)
            
        Returns:
            Dictionary with user info if authenticated, None otherwise
        """
        # Reload users on each authentication to pick up changes without restart
        self._load_users()
        
        if self._users_cache is None or self._users_cache.empty:
            return None
        
        user_data = self._users_cache[self._users_cache['email'].str.lower() == email.lower()]
        
        if user_data.empty:
            return None
        
        user = user_data.iloc[0]
        
        # Check password (plain text comparison)
        stored_password = str(user['password']) if pd.notna(user['password']) else ""
        if stored_password != password:
            return None
        
        # Parse allowed tools
        allowed_tools_str = str(user['allowed_tools']) if pd.notna(user['allowed_tools']) else ""
        allowed_tools = [tool.strip() for tool in allowed_tools_str.split(',') if tool.strip()]
        
        return {
            'email': user['email'],
            'name': user['name'],
            'allowed_tools': allowed_tools
        }
    
    def login_user(self, email: str, password: str) -> bool:
        """
        Login a user by setting session variables.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            True if login successful, False otherwise
        """
        user = self.authenticate_user(email, password)
        if user:
            session['user_email'] = user['email']
            session['user_name'] = user['name']
            session['allowed_tools'] = user['allowed_tools']
            session['logged_in'] = True
            return True
        return False
    
    def logout_user(self) -> None:
        """Logout the current user by clearing session."""
        session.clear()
    
    def is_logged_in(self) -> bool:
        """Check if a user is currently logged in."""
        return session.get('logged_in', False)
    
    def get_current_user(self) -> Optional[Dict[str, any]]:
        """Get the currently logged-in user's information."""
        if not self.is_logged_in():
            return None
        
        return {
            'email': session.get('user_email'),
            'name': session.get('user_name'),
            'allowed_tools': session.get('allowed_tools', [])
        }
    
    def has_access_to_tool(self, tool_name: str) -> bool:
        """
        Check if the current user has access to a specific tool.
        
        Args:
            tool_name: Name of the tool (e.g., 'generic', 'ppk', 'csdp')
            
        Returns:
            True if user has access, False otherwise
        """
        if not self.is_logged_in():
            return False
        
        allowed_tools = session.get('allowed_tools', [])
        return tool_name.lower() in [t.lower() for t in allowed_tools]
    
    def get_allowed_tools(self) -> List[str]:
        """Get list of tools the current user has access to."""
        if not self.is_logged_in():
            return []
        return session.get('allowed_tools', [])
    
    def change_password(self, email: str, old_password: str, new_password: str) -> tuple[bool, str]:
        """
        Change a user's password.
        
        Args:
            email: User's email address
            old_password: Current password for verification
            new_password: New password to set
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Verify old password
        user = self.authenticate_user(email, old_password)
        if not user:
            return False, "Current password is incorrect"
        
        # Validate new password
        if len(new_password) < 4:
            return False, "New password must be at least 4 characters long"
        
        if new_password == old_password:
            return False, "New password must be different from current password"
        
        try:
            # Update password in CSV (plain text)
            self._users_cache.loc[
                self._users_cache['email'].str.lower() == email.lower(), 
                'password'
            ] = new_password
            
            # Save to file
            self._users_cache.to_csv(self.users_csv_path, index=False)
            
            return True, "Password changed successfully"
        
        except Exception as e:
            print(f"Error changing password: {e}")
            return False, "An error occurred while changing password"
    
    def create_user(self, email: str, name: str, password: str, allowed_tools: List[str]) -> tuple[bool, str]:
        """
        Create a new user (admin function).
        
        Args:
            email: User's email address
            name: User's full name
            password: Initial password (plain text)
            allowed_tools: List of tools user can access
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Check if user already exists
        if not self._users_cache[self._users_cache['email'].str.lower() == email.lower()].empty:
            return False, "User with this email already exists"
        
        # Validate password
        if len(password) < 4:
            return False, "Password must be at least 4 characters long"
        
        try:
            # Create new user
            new_user = pd.DataFrame([{
                'email': email,
                'name': name,
                'password': password,
                'allowed_tools': ','.join(allowed_tools)
            }])
            
            # Append to users
            self._users_cache = pd.concat([self._users_cache, new_user], ignore_index=True)
            
            # Save to file
            self._users_cache.to_csv(self.users_csv_path, index=False)
            
            return True, f"User {email} created successfully"
        
        except Exception as e:
            print(f"Error creating user: {e}")
            return False, "An error occurred while creating user"


# Decorator for routes that require login
def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Decorator for routes that require specific tool access
def tool_access_required(tool_name: str):
    """
    Decorator to require access to a specific tool.
    
    Args:
        tool_name: Name of the tool to check access for
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                flash('Please log in to access this page.')
                return redirect(url_for('login'))
            
            allowed_tools = session.get('allowed_tools', [])
            if tool_name.lower() not in [t.lower() for t in allowed_tools]:
                flash(f'You do not have access to {tool_name}.')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Tool name mappings for cleaner code
TOOL_NAMES = {
    'connect': 'connect',
    'share': 'share',
    'generic': 'generic',
    'ppk': 'ppk',
    'csdp': 'csdp',
    'image': 'image',
    'delete_distance': 'delete_distance',
    'culvert': 'culvert',
    'assistant': 'assistant'
}
