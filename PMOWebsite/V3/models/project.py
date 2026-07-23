"""
Project model for managing construction projects.
"""
from datetime import datetime
from . import db


class Project(db.Model):
    """Project model - stores project information."""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    project_code = db.Column(db.String(50), unique=True, nullable=False)  # e.g., "Project-01"
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255))
    contract_number = db.Column(db.String(100))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date, nullable=True)  # Nullable for ongoing projects
    is_ongoing = db.Column(db.Boolean, default=True)
    budget = db.Column(db.Float)
    owner = db.Column(db.String(255))  # Company/organization name
    manager = db.Column(db.String(100))  # Project manager name
    description = db.Column(db.Text)
    
    # Status: 'active', 'inactive', 'removed'
    status = db.Column(db.String(20), default='active', nullable=False)
    
    # Keep is_active for backward compatibility (computed property)
    @property
    def is_active(self):
        return self.status == 'active'
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    daily_forms = db.relationship('DailyFormSubmission', backref='project', lazy='dynamic')
    
    def __repr__(self):
        return f'<Project {self.project_code}: {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_code': self.project_code,
            'name': self.name,
            'location': self.location,
            'contract_number': self.contract_number,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_ongoing': self.is_ongoing,
            'budget': self.budget,
            'owner': self.owner,
            'manager': self.manager,
            'description': self.description,
            'status': self.status,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def get_active_projects():
        """Get all active projects."""
        return Project.query.filter_by(status='active').all()
    
    @staticmethod
    def get_visible_projects():
        """Get all non-removed projects (active + inactive)."""
        return Project.query.filter(Project.status != 'removed').all()
