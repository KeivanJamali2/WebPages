"""
Project Model

Represents a project in the PMO system.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Project:
    """
    Project model representing a company project.
    
    Attributes:
        project_id: Unique project identifier (e.g., PRJ001)
        name: Project name
        description: Project description
        status: Project status (active, completed, on-hold, etc.)
        start_date: Project start date
        end_date: Project end date (optional)
        created_at: Timestamp when project was created
    """
    
    project_id: str
    name: str
    description: str
    status: str = 'active'
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    created_at: Optional[str] = None
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.status = self.status.lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert project to dictionary format for database storage.
        
        Returns:
            Dictionary with all project fields
        """
        return {
            'project_id': self.project_id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """
        Create a Project instance from a dictionary.
        
        Args:
            data: Dictionary containing project fields
        
        Returns:
            Project instance
        """
        return cls(
            project_id=data.get('project_id', ''),
            name=data.get('name', ''),
            description=data.get('description', ''),
            status=data.get('status', 'active'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            created_at=data.get('created_at')
        )
    
    def is_active(self) -> bool:
        """Check if project is active."""
        return self.status == 'active'
    
    def is_completed(self) -> bool:
        """Check if project is completed."""
        return self.status == 'completed'
    
    def update_status(self, new_status: str) -> None:
        """Update project status."""
        self.status = new_status.lower()
    
    def __repr__(self) -> str:
        """String representation of project."""
        return f"Project(id='{self.project_id}', name='{self.name}', status='{self.status}')"
    
    def __str__(self) -> str:
        """User-friendly string representation."""
        return f"{self.name} ({self.project_id}) - {self.status.capitalize()}"


def create_project(db, project_id: str, name: str, description: str, 
                   status: str = 'active', start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> Optional[Project]:
    """
    Create a new project and add to database.
    
    Args:
        db: Database instance
        project_id: Unique project identifier
        name: Project name
        description: Project description
        status: Project status (default: active)
        start_date: Start date (optional)
        end_date: End date (optional)
    
    Returns:
        Project instance if created successfully, None otherwise
    """
    try:
        project = Project(
            project_id=project_id,
            name=name,
            description=description,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
        
        success = db.add_project(project.project_id, project.to_dict())
        
        if success:
            return project
        return None
    except Exception as e:
        print(f"Error creating project: {e}")
        return None


def get_project_by_id(db, project_id: str) -> Optional[Project]:
    """
    Get a project by its ID.
    
    Args:
        db: Database instance
        project_id: Project identifier
    
    Returns:
        Project instance if found, None otherwise
    """
    project_data = db.get_project(project_id)
    if project_data:
        return Project.from_dict(project_data)
    return None


def get_all_projects(db) -> List[Project]:
    """
    Get all projects from the database.
    
    Args:
        db: Database instance
    
    Returns:
        List of Project instances
    """
    projects_data = db.get_all_projects()
    return [Project.from_dict(data) for data in projects_data]


def update_project_status(db, project_id: str, new_status: str) -> bool:
    """
    Update a project's status in the database.
    
    Args:
        db: Database instance
        project_id: Project identifier
        new_status: New status
    
    Returns:
        True if successful, False otherwise
    """
    return db.update_project(project_id, {'status': new_status.lower()})
