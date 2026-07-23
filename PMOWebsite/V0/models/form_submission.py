"""
Form Submission Model

Represents a form submission in the PMO system.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FormSubmission:
    """
    Form submission model representing a submitted form.
    
    Attributes:
        submission_id: Unique submission identifier
        form_type: Type/name of the form
        user_id: ID of user who submitted the form
        project_id: ID of associated project
        file_path: Path to the txt file containing form data
        timestamp: When the form was submitted
        status: Submission status (submitted, reviewed, approved, etc.)
    """
    
    submission_id: str
    form_type: str
    user_id: str
    project_id: str
    file_path: str
    timestamp: Optional[str] = None
    status: str = 'submitted'
    
    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        self.status = self.status.lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert submission to dictionary format for database storage.
        
        Returns:
            Dictionary with all submission fields
        """
        return {
            'submission_id': self.submission_id,
            'form_type': self.form_type,
            'user_id': self.user_id,
            'project_id': self.project_id,
            'file_path': self.file_path,
            'timestamp': self.timestamp,
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FormSubmission':
        """
        Create a FormSubmission instance from a dictionary.
        
        Args:
            data: Dictionary containing submission fields
        
        Returns:
            FormSubmission instance
        """
        return cls(
            submission_id=data.get('submission_id', ''),
            form_type=data.get('form_type', ''),
            user_id=data.get('user_id', ''),
            project_id=data.get('project_id', ''),
            file_path=data.get('file_path', ''),
            timestamp=data.get('timestamp'),
            status=data.get('status', 'submitted')
        )
    
    def is_submitted(self) -> bool:
        """Check if submission is in submitted status."""
        return self.status == 'submitted'
    
    def is_reviewed(self) -> bool:
        """Check if submission has been reviewed."""
        return self.status == 'reviewed'
    
    def is_approved(self) -> bool:
        """Check if submission has been approved."""
        return self.status == 'approved'
    
    def update_status(self, new_status: str) -> None:
        """Update submission status."""
        self.status = new_status.lower()
    
    def __repr__(self) -> str:
        """String representation of submission."""
        return f"FormSubmission(id='{self.submission_id}', form='{self.form_type}', status='{self.status}')"
    
    def __str__(self) -> str:
        """User-friendly string representation."""
        return f"{self.form_type} ({self.submission_id}) - {self.status.capitalize()}"


def create_submission(db, submission_id: str, form_type: str, user_id: str,
                     project_id: str, file_path: str, 
                     status: str = 'submitted') -> Optional[FormSubmission]:
    """
    Create a new form submission and add to database with relationships.
    
    Args:
        db: Database instance
        submission_id: Unique submission identifier
        form_type: Type of form
        user_id: ID of submitting user
        project_id: ID of associated project
        file_path: Path to submission file
        status: Submission status (default: submitted)
    
    Returns:
        FormSubmission instance if created successfully, None otherwise
    """
    try:
        submission = FormSubmission(
            submission_id=submission_id,
            form_type=form_type,
            user_id=user_id,
            project_id=project_id,
            file_path=file_path,
            status=status
        )
        
        # Add submission to database
        success = db.add_submission(submission.submission_id, submission.to_dict())
        
        if not success:
            return None
        
        # Create relationships
        db.link_user_to_submission(user_id, submission.submission_id)
        db.link_submission_to_project(submission.submission_id, project_id)
        
        return submission
    except Exception as e:
        print(f"Error creating submission: {e}")
        return None


def get_submission_by_id(db, submission_id: str) -> Optional[FormSubmission]:
    """
    Get a form submission by its ID.
    
    Args:
        db: Database instance
        submission_id: Submission identifier
    
    Returns:
        FormSubmission instance if found, None otherwise
    """
    submission_data = db.get_submission(submission_id)
    if submission_data:
        return FormSubmission.from_dict(submission_data)
    return None


def get_user_submissions(db, user_id: str) -> List[FormSubmission]:
    """
    Get all submissions by a specific user.
    
    Args:
        db: Database instance
        user_id: User identifier
    
    Returns:
        List of FormSubmission instances
    """
    submissions_data = db.get_user_submissions(user_id)
    return [FormSubmission.from_dict(data) for data in submissions_data]


def get_project_submissions(db, project_id: str) -> List[FormSubmission]:
    """
    Get all submissions for a specific project.
    
    Args:
        db: Database instance
        project_id: Project identifier
    
    Returns:
        List of FormSubmission instances
    """
    submissions_data = db.get_project_submissions(project_id)
    return [FormSubmission.from_dict(data) for data in submissions_data]


def get_all_submissions(db) -> List[FormSubmission]:
    """
    Get all form submissions from the database.
    
    Args:
        db: Database instance
    
    Returns:
        List of FormSubmission instances
    """
    submissions_data = db.get_all_submissions()
    return [FormSubmission.from_dict(data) for data in submissions_data]
