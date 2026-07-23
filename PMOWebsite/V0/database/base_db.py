"""
Base Database Interface

This abstract base class defines the interface for all database implementations.
Any database backend (NetworkX, Neo4j, etc.) must implement these methods.
This allows easy switching between database backends without changing application code.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class BaseDatabase(ABC):
    """
    Abstract base class for database operations.
    
    All database implementations must inherit from this class and implement
    all abstract methods. This ensures a consistent interface across different
    database backends.
    """
    
    # ==================== User Operations ====================
    
    @abstractmethod
    def add_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """
        Add a new user to the database.
        
        Args:
            user_id: Unique identifier for the user (email or national_id)
            user_data: Dictionary containing user information
                      {email, national_id, name, phone, password, role}
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by their ID.
        
        Args:
            user_id: User identifier (email or national_id)
        
        Returns:
            Dict containing user data, or None if not found
        """
        pass
    
    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        pass
    
    @abstractmethod
    def get_user_by_national_id(self, national_id: str) -> Optional[Dict[str, Any]]:
        """Get user by national ID."""
        pass
    
    @abstractmethod
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update user information.
        
        Args:
            user_id: User identifier
            updates: Dictionary of fields to update
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete_user(self, user_id: str) -> bool:
        """Delete a user from the database."""
        pass
    
    @abstractmethod
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users in the database."""
        pass
    
    # ==================== Project Operations ====================
    
    @abstractmethod
    def add_project(self, project_id: str, project_data: Dict[str, Any]) -> bool:
        """
        Add a new project to the database.
        
        Args:
            project_id: Unique project identifier
            project_data: Dictionary containing project information
                         {name, description, start_date, status, etc.}
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        pass
    
    @abstractmethod
    def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update project information."""
        pass
    
    @abstractmethod
    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        pass
    
    @abstractmethod
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects in the database."""
        pass
    
    # ==================== Form Submission Operations ====================
    
    @abstractmethod
    def add_submission(self, submission_id: str, submission_data: Dict[str, Any]) -> bool:
        """
        Add a form submission to the database.
        
        Args:
            submission_id: Unique submission identifier
            submission_data: Dictionary containing submission metadata
                           {form_type, timestamp, file_path, user_id, project_id}
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_submission(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """Get form submission by ID."""
        pass
    
    @abstractmethod
    def get_all_submissions(self) -> List[Dict[str, Any]]:
        """Get all form submissions."""
        pass
    
    # ==================== Relationship Operations ====================
    
    @abstractmethod
    def link_user_to_submission(self, user_id: str, submission_id: str) -> bool:
        """
        Create a relationship between a user and a submission.
        Represents: User -[SUBMITTED]-> Submission
        """
        pass
    
    @abstractmethod
    def link_submission_to_project(self, submission_id: str, project_id: str) -> bool:
        """
        Create a relationship between a submission and a project.
        Represents: Submission -[BELONGS_TO]-> Project
        """
        pass
    
    @abstractmethod
    def get_user_submissions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all submissions by a specific user."""
        pass
    
    @abstractmethod
    def get_project_submissions(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all submissions for a specific project."""
        pass
    
    # ==================== Utility Operations ====================
    
    @abstractmethod
    def clear_all(self) -> bool:
        """Clear all data from the database. Use with caution!"""
        pass
    
    @abstractmethod
    def export_data(self) -> Dict[str, Any]:
        """
        Export all database data for backup or migration.
        
        Returns:
            Dictionary containing all database data
        """
        pass
    
    @abstractmethod
    def import_data(self, data: Dict[str, Any]) -> bool:
        """
        Import data from backup or migration.
        
        Args:
            data: Dictionary containing database data
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
