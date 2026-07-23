"""
Notification model for in-app notifications.
"""
from datetime import datetime
from . import db


class Notification(db.Model):
    """Notification model for user notifications."""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Notification type: form_submitted, form_approved, form_rejected, new_project
    notification_type = db.Column(db.String(50), nullable=False)
    
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Related form or project (optional)
    related_form_id = db.Column(db.Integer, db.ForeignKey('daily_form_submissions.id'), nullable=True)
    related_project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    is_starred = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title}>'
    
    def mark_as_read(self):
        """Mark notification as read."""
        self.is_read = True
        self.read_at = datetime.utcnow()
    
    def mark_as_unread(self):
        """Mark notification as unread."""
        self.is_read = False
        self.read_at = None
    
    def toggle_star(self):
        """Toggle starred status."""
        self.is_starred = not self.is_starred
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notification_type': self.notification_type,
            'title': self.title,
            'message': self.message,
            'related_form_id': self.related_form_id,
            'related_project_id': self.related_project_id,
            'is_read': self.is_read,
            'is_starred': self.is_starred,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }
    
    @staticmethod
    def create_form_submitted_notification(admin_users, form):
        """Create notification for admins when a form is submitted."""
        notifications = []
        for admin in admin_users:
            notification = Notification(
                user_id=admin.id,
                notification_type='form_submitted',
                title='notif_form_submitted_title',
                message=f'notif_form_submitted_msg|{form.document_code}|{form.submitted_by_user.username}',
                related_form_id=form.id
            )
            notifications.append(notification)
        return notifications
    
    @staticmethod
    def create_form_approved_notification(form):
        """Create notification for employee when form is approved."""
        return Notification(
            user_id=form.submitted_by,
            notification_type='form_approved',
            title='notif_form_approved_title',
            message=f'notif_form_approved_msg|{form.document_code}',
            related_form_id=form.id
        )
    
    @staticmethod
    def create_form_rejected_notification(form, comment):
        """Create notification for employee when form is rejected."""
        return Notification(
            user_id=form.submitted_by,
            notification_type='form_rejected',
            title='notif_form_rejected_title',
            message=f'notif_form_rejected_msg|{form.document_code}|{comment}',
            related_form_id=form.id
        )
