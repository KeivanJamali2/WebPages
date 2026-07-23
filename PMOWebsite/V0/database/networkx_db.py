"""
NetworkX Database Implementation

In-memory graph database using NetworkX library.
This implementation stores all data in RAM and is suitable for development
and small-scale deployments. For production with larger data, migrate to Neo4j.

The graph structure:
- Nodes: Users, Projects, FormSubmissions (each with a 'type' attribute)
- Edges: SUBMITTED (User -> Submission), BELONGS_TO (Submission -> Project)
"""

import networkx as nx
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from .base_db import BaseDatabase


class NetworkXDatabase(BaseDatabase):
    """
    NetworkX implementation of the database interface.
    
    Uses a directed graph to store nodes (users, projects, submissions) and
    their relationships. All data is stored in memory.
    
    Attributes:
        graph: NetworkX DiGraph instance
    """
    
    def __init__(self):
        """Initialize an empty directed graph."""
        self.graph = nx.DiGraph()
        print("[NetworkXDB] Database initialized")
    
    # ==================== User Operations ====================
    
    def add_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """Add a new user node to the graph."""
        try:
            if self.graph.has_node(user_id):
                print(f"[NetworkXDB] User {user_id} already exists")
                return False
            
            # Add node with type marker
            node_data = {'type': 'user', **user_data}
            self.graph.add_node(user_id, **node_data)
            print(f"[NetworkXDB] Added user: {user_id}")
            return True
        except Exception as e:
            print(f"[NetworkXDB] Error adding user: {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by ID."""
        try:
            if not self.graph.has_node(user_id):
                return None
            
            node_data = dict(self.graph.nodes[user_id])
            if node_data.get('type') != 'user':
                return None
            
            # Add the ID to the returned data
            node_data['id'] = user_id
            return node_data
        except Exception as e:
            print(f"[NetworkXDB] Error getting user: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('type') == 'user' and node_data.get('email') == email:
                result = dict(node_data)
                result['id'] = node_id
                return result
        return None
    
    def get_user_by_national_id(self, national_id: str) -> Optional[Dict[str, Any]]:
        """Get user by national ID."""
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('type') == 'user' and node_data.get('national_id') == national_id:
                result = dict(node_data)
                result['id'] = node_id
                return result
        return None
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user information."""
        try:
            if not self.graph.has_node(user_id):
                print(f"[NetworkXDB] User {user_id} not found")
                return False
            
            # Update node attributes
            for key, value in updates.items():
                self.graph.nodes[user_id][key] = value
            
            print(f"[NetworkXDB] Updated user: {user_id}")
            return True
        except Exception as e:
            print(f"[NetworkXDB] Error updating user: {e}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user from the database."""
        try:
            if not self.graph.has_node(user_id):
                return False
            
            self.graph.remove_node(user_id)
            print(f"[NetworkXDB] Deleted user: {user_id}")
            return True
        except Exception as e:
            print(f"[NetworkXDB] Error deleting user: {e}")
            return False
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users in the database."""
        users = []
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('type') == 'user':
                user_data = dict(node_data)
                user_data['id'] = node_id
                users.append(user_data)
        return users
    
    # ==================== Project Operations ====================
    
    def add_project(self, project_id: str, project_data: Dict[str, Any]) -> bool:
        """Add a new project node to the graph."""
        try:
            if self.graph.has_node(project_id):
                print(f"[NetworkXDB] Project {project_id} already exists")
                return False
            
            node_data = {'type': 'project', **project_data}
            self.graph.add_node(project_id, **node_data)
            print(f"[NetworkXDB] Added project: {project_id}")
            return True
        except Exception as e:
            print(f"[NetworkXDB] Error adding project: {e}")
            return False
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        try:
            if not self.graph.has_node(project_id):
                return None
            
            node_data = dict(self.graph.nodes[project_id])
            if node_data.get('type') != 'project':
                return None
            
            node_data['id'] = project_id
            return node_data
        except Exception as e:
            print(f"[NetworkXDB] Error getting project: {e}")
            return None
    
    def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update project information."""
        try:
            if not self.graph.has_node(project_id):
                print(f"[NetworkXDB] Project {project_id} not found")
                return False
            
            for key, value in updates.items():
                self.graph.nodes[project_id][key] = value
            
            print(f"[NetworkXDB] Updated project: {project_id}")
            return True
        except Exception as e:
            print(f"[NetworkXDB] Error updating project: {e}")
            return False
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        try:
            if not self.graph.has_node(project_id):
                return False
            
            self.graph.remove_node(project_id)
            print(f"[NetworkXDB] Deleted project: {project_id}")
            return True
        except Exception as e:
            print(f"[NetworkXDB] Error deleting project: {e}")
            return False
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects in the database."""
        projects = []
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('type') == 'project':
                project_data = dict(node_data)
                project_data['id'] = node_id
                projects.append(project_data)
        return projects
    
    # ==================== Form Submission Operations ====================
    
    def add_submission(self, submission_id: str, submission_data: Dict[str, Any]) -> bool:
        """Add a form submission to the database."""
        try:
            if self.graph.has_node(submission_id):
                print(f"[NetworkXDB] Submission {submission_id} already exists")
                return False
            
            node_data = {'type': 'submission', **submission_data}
            self.graph.add_node(submission_id, **node_data)
            print(f"[NetworkXDB] Added submission: {submission_id}")
            return True
        except Exception as e:
            print(f"[NetworkXDB] Error adding submission: {e}")
            return False
    
    def get_submission(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """Get form submission by ID."""
        try:
            if not self.graph.has_node(submission_id):
                return None
            
            node_data = dict(self.graph.nodes[submission_id])
            if node_data.get('type') != 'submission':
                return None
            
            node_data['id'] = submission_id
            return node_data
        except Exception as e:
            print(f"[NetworkXDB] Error getting submission: {e}")
            return None
    
    def get_all_submissions(self) -> List[Dict[str, Any]]:
        """Get all form submissions."""
        submissions = []
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('type') == 'submission':
                submission_data = dict(node_data)
                submission_data['id'] = node_id
                submissions.append(submission_data)
        return submissions
    
    # ==================== Relationship Operations ====================
    
    def link_user_to_submission(self, user_id: str, submission_id: str) -> bool:
        """Create User -[SUBMITTED]-> Submission relationship."""
        try:
            if not self.graph.has_node(user_id) or not self.graph.has_node(submission_id):
                print(f"[NetworkXDB] User or submission not found")
                return False
            
            self.graph.add_edge(user_id, submission_id, relation='SUBMITTED')
            print(f"[NetworkXDB] Linked user {user_id} to submission {submission_id}")
            return True
        except Exception as e:
            print(f"[NetworkXDB] Error linking user to submission: {e}")
            return False
    
    def link_submission_to_project(self, submission_id: str, project_id: str) -> bool:
        """Create Submission -[BELONGS_TO]-> Project relationship."""
        try:
            if not self.graph.has_node(submission_id) or not self.graph.has_node(project_id):
                print(f"[NetworkXDB] Submission or project not found")
                return False
            
            self.graph.add_edge(submission_id, project_id, relation='BELONGS_TO')
            print(f"[NetworkXDB] Linked submission {submission_id} to project {project_id}")
            return True
        except Exception as e:
            print(f"[NetworkXDB] Error linking submission to project: {e}")
            return False
    
    def get_user_submissions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all submissions by a specific user."""
        submissions = []
        try:
            if not self.graph.has_node(user_id):
                return submissions
            
            # Find all nodes connected by SUBMITTED edges
            for successor in self.graph.successors(user_id):
                edge_data = self.graph.get_edge_data(user_id, successor)
                if edge_data and edge_data.get('relation') == 'SUBMITTED':
                    submission_data = dict(self.graph.nodes[successor])
                    submission_data['id'] = successor
                    submissions.append(submission_data)
        except Exception as e:
            print(f"[NetworkXDB] Error getting user submissions: {e}")
        
        return submissions
    
    def get_project_submissions(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all submissions for a specific project."""
        submissions = []
        try:
            if not self.graph.has_node(project_id):
                return submissions
            
            # Find all nodes connected by incoming BELONGS_TO edges
            for predecessor in self.graph.predecessors(project_id):
                edge_data = self.graph.get_edge_data(predecessor, project_id)
                if edge_data and edge_data.get('relation') == 'BELONGS_TO':
                    submission_data = dict(self.graph.nodes[predecessor])
                    submission_data['id'] = predecessor
                    submissions.append(submission_data)
        except Exception as e:
            print(f"[NetworkXDB] Error getting project submissions: {e}")
        
        return submissions
    
    # ==================== Utility Operations ====================
    
    def clear_all(self) -> bool:
        """Clear all data from the database."""
        try:
            self.graph.clear()
            print("[NetworkXDB] All data cleared")
            return True
        except Exception as e:
            print(f"[NetworkXDB] Error clearing data: {e}")
            return False
    
    def export_data(self) -> Dict[str, Any]:
        """Export all database data for backup."""
        try:
            data = {
                'nodes': [],
                'edges': [],
                'export_date': datetime.now().isoformat()
            }
            
            # Export nodes
            for node_id, node_data in self.graph.nodes(data=True):
                node_export = {'id': node_id, 'data': dict(node_data)}
                data['nodes'].append(node_export)
            
            # Export edges
            for source, target, edge_data in self.graph.edges(data=True):
                edge_export = {
                    'source': source,
                    'target': target,
                    'data': dict(edge_data)
                }
                data['edges'].append(edge_export)
            
            print(f"[NetworkXDB] Exported {len(data['nodes'])} nodes and {len(data['edges'])} edges")
            return data
        except Exception as e:
            print(f"[NetworkXDB] Error exporting data: {e}")
            return {}
    
    def import_data(self, data: Dict[str, Any]) -> bool:
        """Import data from backup."""
        try:
            # Clear existing data
            self.graph.clear()
            
            # Import nodes
            for node in data.get('nodes', []):
                self.graph.add_node(node['id'], **node['data'])
            
            # Import edges
            for edge in data.get('edges', []):
                self.graph.add_edge(edge['source'], edge['target'], **edge['data'])
            
            print(f"[NetworkXDB] Imported {len(data.get('nodes', []))} nodes and {len(data.get('edges', []))} edges")
            return True
        except Exception as e:
            print(f"[NetworkXDB] Error importing data: {e}")
            return False
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        stats = {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'users': len([n for n, d in self.graph.nodes(data=True) if d.get('type') == 'user']),
            'projects': len([n for n, d in self.graph.nodes(data=True) if d.get('type') == 'project']),
            'submissions': len([n for n, d in self.graph.nodes(data=True) if d.get('type') == 'submission'])
        }
        return stats
