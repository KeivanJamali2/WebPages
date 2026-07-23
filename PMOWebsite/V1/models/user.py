"""
User model for authentication and role management.
"""
from datetime import datetime
from . import db


class User(db.Model):
    """User model - loaded from user.txt file but stored in DB for relationships."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Plain text as per user.txt
    phone_number = db.Column(db.String(20))
    national_id = db.Column(db.String(20))
    email = db.Column(db.String(120))
    role = db.Column(db.String(20), nullable=False)  # boss, admin, employee
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    daily_forms = db.relationship('DailyFormSubmission', backref='submitted_by_user', lazy='dynamic',
                                   foreign_keys='DailyFormSubmission.submitted_by')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def is_boss(self):
        return self.role == 'boss'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_employee(self):
        return self.role == 'employee'
    
    def can_view_all_forms(self):
        """Boss and Admin can view all forms."""
        return self.role in ['boss', 'admin']
    
    def can_approve_forms(self):
        """Only Admin can approve/reject forms."""
        return self.role == 'admin'
    
    def can_manage_projects(self):
        """Only Boss can create/edit projects."""
        return self.role == 'boss'
    
    def can_view_analytics(self):
        """Only Boss can view analytics."""
        return self.role == 'boss'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'phone_number': self.phone_number,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
