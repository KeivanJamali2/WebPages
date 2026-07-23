"""
Data Loader Utility

Functions for loading initial data from text files into the database.
"""

import os
from typing import List, Tuple
from models.user import create_user
from models.project import create_project


def load_users_from_file(db, file_path: str) -> Tuple[int, int]:
    """
    Load users from a pipe-delimited text file.
    
    File format (pipe-delimited):
    email|national_id|name|phone|password|role
    
    Example:
    admin@company.com|1234567890|John Doe|+98 910 151 1983|admin123|admin
    
    Args:
        db: Database instance
        file_path: Path to the users.txt file
    
    Returns:
        Tuple of (successful_count, failed_count)
    """
    if not os.path.exists(file_path):
        print(f"[DataLoader] File not found: {file_path}")
        return (0, 0)
    
    successful = 0
    failed = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Skip empty lines and comments
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse line
                parts = line.split('|')
                if len(parts) != 6:
                    print(f"[DataLoader] Line {line_num}: Invalid format (expected 6 fields, got {len(parts)})")
                    failed += 1
                    continue
                
                email, national_id, name, phone, password, role = [p.strip() for p in parts]
                
                # Create user
                user = create_user(
                    db=db,
                    email=email,
                    national_id=national_id,
                    name=name,
                    phone=phone,
                    password=password,
                    role=role
                )
                
                if user:
                    print(f"[DataLoader] Loaded user: {email} ({role})")
                    successful += 1
                else:
                    print(f"[DataLoader] Line {line_num}: Failed to create user {email}")
                    failed += 1
        
        print(f"[DataLoader] Users loaded: {successful} successful, {failed} failed")
        return (successful, failed)
    
    except Exception as e:
        print(f"[DataLoader] Error loading users: {e}")
        return (successful, failed)


def load_projects_from_file(db, file_path: str) -> Tuple[int, int]:
    """
    Load projects from a pipe-delimited text file.
    
    File format (pipe-delimited):
    project_id|name|description|status|start_date|end_date
    
    Example:
    PRJ001|Website Redesign|Redesign company website|active|2025-01-01|
    
    Args:
        db: Database instance
        file_path: Path to the projects.txt file
    
    Returns:
        Tuple of (successful_count, failed_count)
    """
    if not os.path.exists(file_path):
        print(f"[DataLoader] File not found: {file_path}")
        return (0, 0)
    
    successful = 0
    failed = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Skip empty lines and comments
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse line
                parts = line.split('|')
                if len(parts) != 6:
                    print(f"[DataLoader] Line {line_num}: Invalid format (expected 6 fields, got {len(parts)})")
                    failed += 1
                    continue
                
                project_id, name, description, status, start_date, end_date = [p.strip() for p in parts]
                
                # Handle empty optional fields
                start_date = start_date if start_date else None
                end_date = end_date if end_date else None
                
                # Create project
                project = create_project(
                    db=db,
                    project_id=project_id,
                    name=name,
                    description=description,
                    status=status or 'active',
                    start_date=start_date,
                    end_date=end_date
                )
                
                if project:
                    print(f"[DataLoader] Loaded project: {project_id} - {name}")
                    successful += 1
                else:
                    print(f"[DataLoader] Line {line_num}: Failed to create project {project_id}")
                    failed += 1
        
        print(f"[DataLoader] Projects loaded: {successful} successful, {failed} failed")
        return (successful, failed)
    
    except Exception as e:
        print(f"[DataLoader] Error loading projects: {e}")
        return (successful, failed)


def initialize_database(db, users_file: str, projects_file: str = None):
    """
    Initialize database with data from files.
    
    Args:
        db: Database instance
        users_file: Path to users.txt
        projects_file: Path to projects.txt (optional)
    """
    print("[DataLoader] Initializing database...")
    
    # Load users
    users_loaded, users_failed = load_users_from_file(db, users_file)
    
    # Load projects if file provided
    projects_loaded = 0
    projects_failed = 0
    if projects_file and os.path.exists(projects_file):
        projects_loaded, projects_failed = load_projects_from_file(db, projects_file)
    
    print(f"[DataLoader] Initialization complete!")
    print(f"  Users: {users_loaded} loaded, {users_failed} failed")
    print(f"  Projects: {projects_loaded} loaded, {projects_failed} failed")
    
    return {
        'users': {'loaded': users_loaded, 'failed': users_failed},
        'projects': {'loaded': projects_loaded, 'failed': projects_failed}
    }
