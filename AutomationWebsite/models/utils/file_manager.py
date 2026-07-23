"""
File Manager for handling all file operations.
Centralizes upload, download, save, and delete operations.
"""

import os
from werkzeug.utils import secure_filename
from flask import send_file, send_from_directory
from typing import List, Optional, Tuple


class FileManager:
    """Manages all file operations for the automation website."""
    
    ALLOWED_EXTENSIONS = {'csv', 'txt', 'xlsx', 'xls', 'dwg', 'pdf'}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
    
    def __init__(self, base_dir: str):
        """
        Initialize the file manager.
        
        Args:
            base_dir: Base directory for the application
        """
        self.base_dir = base_dir
        self.upload_folder_send = os.path.join(base_dir, 'Files', 'send_to_others')
        self.upload_folder_received = os.path.join(base_dir, 'Files', 'received_from_others')
        self.upload_folder_share = os.path.join(base_dir, 'Files', 'share')
        self.result_dir = os.path.join(base_dir, 'Files', 'result')
        self.movie_folder = os.path.join(base_dir, 'Files', 'share')
        self.app_folder = os.path.join(base_dir, 'Files', 'apps')
        
        # Ensure all directories exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create all necessary directories if they don't exist."""
        directories = [
            self.upload_folder_send,
            self.upload_folder_received,
            self.upload_folder_share,
            self.result_dir,
            self.movie_folder,
            self.app_folder
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def allowed_file(self, filename: str) -> bool:
        """
        Check if a file has an allowed extension.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if file extension is allowed, False otherwise
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    def save_uploaded_file(self, file, folder: str, custom_filename: Optional[str] = None) -> Tuple[bool, str, str]:
        """
        Save an uploaded file to a specific folder.
        
        Args:
            file: FileStorage object from Flask request
            folder: Target folder ('send', 'received', 'share', 'result')
            custom_filename: Optional custom filename to use
            
        Returns:
            Tuple of (success: bool, filepath: str, message: str)
        """
        if not file or file.filename == '':
            return False, '', 'No file selected'
        
        # Get the appropriate folder
        folder_map = {
            'send': self.upload_folder_send,
            'received': self.upload_folder_received,
            'share': self.upload_folder_share,
            'result': self.result_dir
        }
        
        target_folder = folder_map.get(folder, self.result_dir)
        
        # Secure the filename
        filename = custom_filename if custom_filename else secure_filename(file.filename)
        filepath = os.path.join(target_folder, filename)
        
        try:
            file.save(filepath)
            return True, filepath, 'File saved successfully'
        except Exception as e:
            return False, '', f'Error saving file: {str(e)}'
    
    def save_multiple_files(self, files: List, folder: str) -> Tuple[bool, List[str], str]:
        """
        Save multiple uploaded files.
        
        Args:
            files: List of FileStorage objects
            folder: Target folder name
            
        Returns:
            Tuple of (success: bool, filepaths: List[str], message: str)
        """
        if not files or all(file.filename == '' for file in files):
            return False, [], 'No files selected'
        
        saved_files = []
        errors = []
        
        for file in files:
            if file and file.filename != '':
                success, filepath, message = self.save_uploaded_file(file, folder)
                if success:
                    saved_files.append(filepath)
                else:
                    errors.append(message)
        
        if errors:
            return False, saved_files, '; '.join(errors)
        
        return True, saved_files, f'{len(saved_files)} files saved successfully'
    
    def get_file_list(self, folder: str) -> List[str]:
        """
        Get list of files in a specific folder.
        
        Args:
            folder: Folder name ('send', 'received', 'share', 'result')
            
        Returns:
            List of filenames
        """
        folder_map = {
            'send': self.upload_folder_send,
            'received': self.upload_folder_received,
            'share': self.upload_folder_share,
            'result': self.result_dir
        }
        
        target_folder = folder_map.get(folder, self.result_dir)
        
        try:
            if os.path.exists(target_folder):
                return [f for f in os.listdir(target_folder) if os.path.isfile(os.path.join(target_folder, f))]
            return []
        except Exception as e:
            print(f"Error listing files: {e}")
            return []
    
    def download_file(self, filename: str, folder: str):
        """
        Send a file for download.
        
        Args:
            filename: Name of the file to download
            folder: Folder name where file is located
            
        Returns:
            Flask send_file response
        """
        folder_map = {
            'send': self.upload_folder_send,
            'received': self.upload_folder_received,
            'share': self.upload_folder_share,
            'result': self.result_dir,
            'apps': self.app_folder
        }
        
        target_folder = folder_map.get(folder, self.result_dir)
        filepath = os.path.join(target_folder, filename)
        
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            raise FileNotFoundError(f"File {filename} not found")
    
    def delete_file(self, filename: str, folder: str) -> Tuple[bool, str]:
        """
        Delete a file from a specific folder.
        
        Args:
            filename: Name of the file to delete
            folder: Folder name where file is located
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        folder_map = {
            'send': self.upload_folder_send,
            'received': self.upload_folder_received,
            'share': self.upload_folder_share,
            'result': self.result_dir
        }
        
        target_folder = folder_map.get(folder, self.result_dir)
        filepath = os.path.join(target_folder, filename)
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True, 'File deleted successfully'
            else:
                return False, 'File not found'
        except Exception as e:
            return False, f'Error deleting file: {str(e)}'
    
    def get_movie_file(self) -> Optional[str]:
        """
        Get the first movie file found in the movie folder.
        
        Returns:
            Movie filename or None if not found
        """
        movie_extensions = {'mp4', 'avi', 'mkv', 'm4v', 'mov', 'wmv'}
        
        try:
            if os.path.exists(self.movie_folder):
                for filename in os.listdir(self.movie_folder):
                    if '.' in filename and filename.rsplit('.', 1)[1].lower() in movie_extensions:
                        return filename
        except Exception as e:
            print(f"Error finding movie file: {e}")
        
        return None
    
    def cleanup_old_results(self, max_age_days: int = 7) -> Tuple[int, str]:
        """
        Clean up old result files.
        
        Args:
            max_age_days: Maximum age of files to keep in days
            
        Returns:
            Tuple of (count: int, message: str)
        """
        import time
        
        count = 0
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        try:
            for filename in os.listdir(self.result_dir):
                filepath = os.path.join(self.result_dir, filename)
                if os.path.isfile(filepath):
                    file_age = current_time - os.path.getmtime(filepath)
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        count += 1
            
            return count, f'Cleaned up {count} old files'
        except Exception as e:
            return 0, f'Error during cleanup: {str(e)}'
