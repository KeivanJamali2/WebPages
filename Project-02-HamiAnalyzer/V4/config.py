"""
Configuration file for HamiAnalyzer Website
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Flask configuration
SECRET_KEY = os.environ.get('SECRET_KEY') or 'hami-analyzer-secret-key-change-in-production'
DEBUG = True

# File paths
UPLOAD_FOLDER = BASE_DIR / 'uploads'
DATABASE_FOLDER = BASE_DIR / 'database'
PLOTS_FOLDER = BASE_DIR / 'plots'
DOWNLOADS_FOLDER = BASE_DIR / 'downloads'
USERS_FILE = BASE_DIR / 'users.txt'
PEOPLE_INDEX_FILE = BASE_DIR / 'people_index.csv'
AVAILABLE_ANALYSES_FILE = BASE_DIR / 'available_analyses.txt'
ANALYSIS_CONFIG_FILE = BASE_DIR / 'analysis_config.json'

# Upload settings
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB max file size
ALLOWED_EXTENSIONS = {'zip'}

# Analysis settings
DATE_SOURCE = 'first'  # Can be 'first' or 'last'

# Session settings
SESSION_TYPE = 'filesystem'
PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

# Logging
LOG_FILE = BASE_DIR / 'logs' / 'app.log'
LOG_LEVEL = 'INFO'

# Create directories if they don't exist
for folder in [UPLOAD_FOLDER, DATABASE_FOLDER, PLOTS_FOLDER, DOWNLOADS_FOLDER, BASE_DIR / 'logs']:
    folder.mkdir(parents=True, exist_ok=True)

# Helper function to load available analyses
def load_available_analyses():
    """
    Load available analysis functions from configuration file.
    
    Returns:
        list: List of dictionaries with keys: 'function_name', 'display_name', 'description'
              Sorted alphabetically by display_name.
    """
    analyses = []
    
    if not AVAILABLE_ANALYSES_FILE.exists():
        return analyses
    
    try:
        with open(AVAILABLE_ANALYSES_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse line: function_name | Display Name | Description
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 3:
                    analyses.append({
                        'function_name': parts[0],
                        'display_name': parts[1],
                        'description': parts[2]
                    })
    except Exception as e:
        print(f"Error loading available analyses: {e}")
    
    # Sort analyses alphabetically by display_name
    analyses.sort(key=lambda x: x['display_name'].lower())
    
    return analyses


def save_analysis_config(start_date: str, end_date: str, selected_analyses: list):
    """
    Save analysis configuration to a JSON file.
    
    Args:
        start_date: Start date string (YYYY-MM-DD format)
        end_date: End date string (YYYY-MM-DD format)
        selected_analyses: List of selected analysis function names
    """
    import json
    
    config_data = {
        'start_date': start_date or '',
        'end_date': end_date or '',
        'selected_analyses': selected_analyses or []
    }
    
    try:
        with open(ANALYSIS_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving analysis config: {e}")


def load_analysis_config() -> dict:
    """
    Load analysis configuration from JSON file.
    
    Returns:
        dict: Configuration with keys 'start_date', 'end_date', 'selected_analyses'
    """
    import json
    
    default_config = {
        'start_date': '',
        'end_date': '',
        'selected_analyses': []
    }
    
    if not ANALYSIS_CONFIG_FILE.exists():
        return default_config
    
    try:
        with open(ANALYSIS_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            return {
                'start_date': config_data.get('start_date', ''),
                'end_date': config_data.get('end_date', ''),
                'selected_analyses': config_data.get('selected_analyses', [])
            }
    except Exception as e:
        print(f"Error loading analysis config: {e}")
        return default_config
