"""
Statistics Manager for tracking user activity and analytics.
Logs all user actions with timestamps, email, and tool usage.
"""

import pandas as pd
import os
from datetime import datetime
from typing import Optional


class StatisticsManager:
    """Manages statistics logging and analytics for the automation website."""
    
    # Tool names for tracking
    TOOLS = [
        'Connect to Me',
        'Share Files', 
        'Generic Processing',
        'PPK Processing',
        'CSDP Processing',
        'Image Processing',
        'Delete Empty Processing',
        'Culvert Processing',
        'Chat-GPT'
    ]
    
    def __init__(self, statistics_dir: str):
        """
        Initialize the statistics manager.
        
        Args:
            statistics_dir: Directory path where statistics CSV files are stored
        """
        self.statistics_dir = statistics_dir
        os.makedirs(statistics_dir, exist_ok=True)
        self.current_version = self._initialize_history_version()
    
    def _initialize_history_version(self) -> int:
        """
        Find the latest history file version.
        
        Returns:
            Latest version number, or 0 if no files exist
        """
        if not os.path.exists(self.statistics_dir):
            return 0
            
        existing_files = [
            f for f in os.listdir(self.statistics_dir) 
            if f.startswith('history_V') and f.endswith('.csv')
        ]
        
        if existing_files:
            versions = [int(f.split('_V')[1].split('.csv')[0]) for f in existing_files]
            return max(versions)
        
        return 0
    
    def _get_current_history_file(self) -> str:
        """Get the path to the current history file."""
        return os.path.join(self.statistics_dir, f"history_V{self.current_version}.csv")
    
    def _create_new_history_file(self) -> pd.DataFrame:
        """
        Create a new history DataFrame with proper structure.
        
        Returns:
            New empty DataFrame with proper columns
        """
        columns = ["Date", "IP Address", "User Email", "User Name"] + self.TOOLS + ["Downloads"]
        data = pd.DataFrame(0, index=range(1), columns=columns)
        return data
    
    def _load_or_create_history(self) -> tuple[pd.DataFrame, str]:
        """
        Load existing history file or create a new one if needed.
        
        Returns:
            Tuple of (DataFrame, file_path)
        """
        file_path = self._get_current_history_file()
        
        try:
            data = pd.read_csv(file_path, index_col=0)
            
            # Check if structure is correct
            expected_cols = len(["Date", "IP Address", "User Email", "User Name"] + self.TOOLS + ["Downloads"])
            if len(data.columns) != expected_cols:
                raise ValueError("Column count mismatch")
                
        except (FileNotFoundError, ValueError):
            # Create new version
            self.current_version += 1
            file_path = self._get_current_history_file()
            data = self._create_new_history_file()
        
        return data, file_path
    
    def add_to_history(
        self, 
        tool_name: str, 
        user_email: Optional[str] = None,
        user_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        status: str = "success"
    ) -> None:
        """
        Add an entry to the history log.
        
        Args:
            tool_name: Name of the tool used (e.g., 'Generic Processing', 'Share Files')
            user_email: Email of the user (from session)
            user_name: Name of the user (from session)
            ip_address: IP address of the request
            status: Status of the action ('success', 'failed', 'unauthorized', etc.)
        """
        data, file_path = self._load_or_create_history()
        
        # Determine which column to increment
        tool_index = None
        if tool_name in self.TOOLS:
            tool_index = self.TOOLS.index(tool_name)
        elif tool_name.startswith('Download:'):
            # It's a download
            tool_index = len(self.TOOLS)  # Downloads column
        
        # Create new row
        timestamp = datetime.now().strftime("%Y/%m/%d | %H:%M:%S")
        new_row = [
            timestamp,
            ip_address or "Unknown",
            user_email or "Anonymous",
            user_name or "Anonymous"
        ] + [0] * len(self.TOOLS) + [0]  # Initialize all tool counters to 0
        
        # Set the appropriate tool counter to 1
        if tool_index is not None:
            new_row[4 + tool_index] = 1  # +4 for the first 4 columns
        
        # Add the new row
        data.loc[len(data)] = new_row
        
        # Update summary row (row 0) - sum of all activities
        data.iloc[0, 4:] = data.iloc[1:, 4:].sum().values
        data.iloc[0, 0] = len(data) - 1  # Total number of activities
        data.iloc[0, 1] = len(data.iloc[1:]['User Email'].unique())  # Unique users
        data.iloc[0, 2] = "Summary"
        data.iloc[0, 3] = "Summary"
        
        # Save to file
        data.to_csv(file_path)
    
    def get_statistics_summary(self) -> dict:
        """
        Get a summary of all statistics.
        
        Returns:
            Dictionary with statistics summary
        """
        data, _ = self._load_or_create_history()
        
        if len(data) < 2:
            return {
                'total_activities': 0,
                'unique_users': 0,
                'tool_usage': {},
                'total_downloads': 0
            }
        
        summary_row = data.iloc[0]
        
        tool_usage = {}
        for i, tool in enumerate(self.TOOLS):
            tool_usage[tool] = int(summary_row.iloc[4 + i])
        
        return {
            'total_activities': int(summary_row.iloc[0]),
            'unique_users': int(summary_row.iloc[1]) if pd.notna(summary_row.iloc[1]) else 0,
            'tool_usage': tool_usage,
            'total_downloads': int(summary_row.iloc[-1])
        }
    
    def get_user_activity(self, user_email: str, limit: int = 50) -> pd.DataFrame:
        """
        Get recent activity for a specific user.
        
        Args:
            user_email: Email of the user
            limit: Maximum number of records to return
            
        Returns:
            DataFrame with user's activity
        """
        data, _ = self._load_or_create_history()
        
        if len(data) < 2:
            return pd.DataFrame()
        
        user_data = data[data['User Email'] == user_email].iloc[1:]  # Skip summary row
        return user_data.tail(limit)
    
    def get_recent_activity(self, limit: int = 100) -> pd.DataFrame:
        """
        Get recent activity across all users.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            DataFrame with recent activity
        """
        data, _ = self._load_or_create_history()
        
        if len(data) < 2:
            return pd.DataFrame()
        
        return data.iloc[1:].tail(limit)  # Skip summary row
