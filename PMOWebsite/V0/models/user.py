"""
User Model

Represents a user in the PMO system with authentication capabilities.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class User:
    """
    User model representing a company employee or admin.
    
    Attributes:
        email: User's email address (unique identifier)
        national_id: User's national ID (unique identifier)
        name: Full name of the user
        phone: Phone number in format +98 910 151 1983
        password: Plain text password (as requested, no hashing)
        role: User role (admin, employee, etc.)
    """
    
    email: str
    national_id: str
    name: str
    phone: str
    password: str
    role: str
    
    def __post_init__(self):
        """Validate user data after initialization."""
        self.email = self.email.strip().lower()
        self.national_id = self.national_id.strip()
        self.name = self.name.strip()
        self.phone = self.phone.strip()
        self.role = self.role.strip().lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert user to dictionary format for database storage.
        
        Returns:
            Dictionary with all user fields
        """
        return {
            'email': self.email,
            'national_id': self.national_id,
            'name': self.name,
            'phone': self.phone,
            'password': self.password,
            'role': self.role
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """
        Create a User instance from a dictionary.
        
        Args:
            data: Dictionary containing user fields
        
        Returns:
            User instance
        """
        return cls(
            email=data.get('email', ''),
            national_id=data.get('national_id', ''),
            name=data.get('name', ''),
            phone=data.get('phone', ''),
            password=data.get('password', ''),
            role=data.get('role', 'employee')
        )
    
    def verify_password(self, password: str) -> bool:
        """
        Verify if the provided password matches the user's password.
        
        Args:
            password: Password to verify
        
        Returns:
            True if password matches, False otherwise
        """
        return self.password == password
    
    def update_password(self, new_password: str) -> None:
        """
        Update user's password.
        
        Args:
            new_password: New password to set
        """
        self.password = new_password
    
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == 'admin'
    
    def is_employee(self) -> bool:
        """Check if user has employee role."""
        return self.role == 'employee'
    
    def has_role(self, role: str) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            role: Role to check
        
        Returns:
            True if user has the role, False otherwise
        """
        return self.role == role.lower()
    
    def __repr__(self) -> str:
        """String representation of user (without password)."""
        return f"User(email='{self.email}', name='{self.name}', role='{self.role}')"
    
    def __str__(self) -> str:
        """User-friendly string representation."""
        return f"{self.name} ({self.email}) - {self.role.capitalize()}"


def authenticate_user(db, identifier: str, password: str) -> Optional[User]:
    """
    Authenticate a user using email or national_id and password.
    
    Args:
        db: Database instance
        identifier: Email or national ID
        password: Password to verify
    
    Returns:
        User instance if authentication successful, None otherwise
    """
    # Try to find user by email first
    user_data = db.get_user_by_email(identifier)
    
    # If not found, try national_id
    if not user_data:
        user_data = db.get_user_by_national_id(identifier)
    
    # If still not found, authentication fails
    if not user_data:
        return None
    
    # Create User instance
    user = User.from_dict(user_data)
    
    # Verify password
    if user.verify_password(password):
        return user
    
    return None


def get_user_by_id(db, user_id: str) -> Optional[User]:
    """
    Get a user by their ID (email).
    
    Args:
        db: Database instance
        user_id: User ID (email)
    
    Returns:
        User instance if found, None otherwise
    """
    user_data = db.get_user(user_id)
    if user_data:
        return User.from_dict(user_data)
    return None


def create_user(db, email: str, national_id: str, name: str, phone: str, 
                password: str, role: str = 'employee') -> Optional[User]:
    """
    Create a new user and add to database.
    
    Args:
        db: Database instance
        email: User's email
        national_id: User's national ID
        name: User's full name
        phone: User's phone number
        password: User's password
        role: User's role (default: employee)
    
    Returns:
        User instance if created successfully, None otherwise
    """
    try:
        user = User(
            email=email,
            national_id=national_id,
            name=name,
            phone=phone,
            password=password,
            role=role
        )
        
        # Add to database using email as ID
        success = db.add_user(user.email, user.to_dict())
        
        if success:
            return user
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None


def update_user_password(db, user_email: str, new_password: str) -> bool:
    """
    Update a user's password in the database.
    
    Args:
        db: Database instance
        user_email: User's email
        new_password: New password
    
    Returns:
        True if successful, False otherwise
    """
    return db.update_user(user_email, {'password': new_password})
