"""
Comment model for form review comments.
"""
from datetime import datetime
from . import db


class Comment(db.Model):
    """Comment model for form review comments."""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    daily_form_id = db.Column(db.Integer, db.ForeignKey('daily_form_submissions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    
    # Comment type: review, rejection, general
    comment_type = db.Column(db.String(50), default='general')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='comments')
    
    def __repr__(self):
        return f'<Comment {self.id} by {self.user.username if self.user else "Unknown"}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'daily_form_id': self.daily_form_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'content': self.content,
            'comment_type': self.comment_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
