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
ALLOWED_EXCEL_EXTENSIONS = {'xlsx'}

# Analysis settings
DATE_SOURCE = 'first'  # Can be 'first' or 'last'

# City used when it cannot be inferred from a request's 'رشته محل' place string
DEFAULT_CITY = 'یزد'

# Session settings
SESSION_TYPE = 'filesystem'
PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

# Logging
LOG_FILE = BASE_DIR / 'logs' / 'app.log'
LOG_LEVEL = 'INFO'

# Create directories if they don't exist
for folder in [UPLOAD_FOLDER, DATABASE_FOLDER, PLOTS_FOLDER, DOWNLOADS_FOLDER, BASE_DIR / 'logs']:
    folder.mkdir(parents=True, exist_ok=True)

# How many employees the top-employee plots show, unless overridden on the analysis page
DEFAULT_TOP_EMPLOYEE_N = 10

# Performance scores entered on the Evaluations page run from 0 to this value.
EVALUATION_SCORE_MAX = 100

# Weights for the composite hami performance score. Must sum to 1.0.
# Each metric is standardised to a z-score first, so these weights are comparable
# even though the raw metrics are counts and hours.
HAMI_SCORE_WEIGHTS = {
    'count': 0.25,
    'first_response': 0.125,
    'duration': 0.125,
    'quality': 0.50,
}

# Fixed targets for the absolute 0-100 version of the same score. Unlike the z-score
# these do not depend on who else is in the cohort, so two periods are comparable only
# as long as these numbers are left alone. Editable on the analysis page.
HAMI_SCORE_TARGETS = {
    # Per-request hour tiers, fastest first, scored with HAMI_SCORE_TIER_CREDITS.
    'first_response_hours': [12, 24, 48, 72],
    'duration_hours': [72, 168, 336, 720],
    # Requests per hami per 30 days that counts as a full workload.
    'volume_target_30d': 30,
    # Requests per 30 days at which a hami's confidence reaches 50%.
    'confidence_half_n': 20,
    # Share of hamis, best first, that the whole-population score averages over.
    'population_top_percent': 75,
}

# Credit for a request landing in each tier: at or under the first threshold, then
# between consecutive thresholds, then past the last one. One longer than the tiers.
HAMI_SCORE_TIER_CREDITS = [100, 80, 50, 20, 0]

# Volume curve: score = 100 * r^shape / (r^shape + beta), r = load / target, with beta
# fixed so that exactly hitting the target scores CREDIT_AT_TARGET. More volume always
# scores higher, with diminishing returns and no way to exceed 100.
HAMI_SCORE_VOLUME_SHAPE = 1.5
HAMI_SCORE_VOLUME_CREDIT_AT_TARGET = 80.0

# The employee score has no timing data of its own: Response Time is graded by hand on
# the Evaluations page and arrives already on 0-100, so only the workload needs a curve.
EMPLOYEE_SCORE_WEIGHTS = {
    'count': 0.25,
    'response_time': 0.25,
    'quality': 0.50,
}

EMPLOYEE_SCORE_TARGETS = {
    # Requests answered per employee per 30 days that counts as a full workload.
    'volume_target_30d': 10,
    # Requests answered per 30 days at which an employee's confidence reaches 50%.
    'confidence_half_n': 5,
    # Share of employees, best first, that the whole-population score averages over.
    'population_top_percent': 75,
    # How many employees the best/worst panels list. The cohort is far too large to
    # fit on one axis, so the plots show both ends plus the distribution behind them.
    'top_n': 15,
}


# Helper function to load available analyses
def load_available_analyses():
    """
    Load available analysis functions from configuration file.
    
    Returns:
        list: List of dictionaries with keys: 'function_name', 'display_name', 'description'
              In the order defined in available_analyses.txt.
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
    
    return analyses


def save_analysis_config(start_date: str, end_date: str, selected_analyses: list, selected_cities: list = None,
                         faculty_totals: dict = None, top_employee_n: int = None,
                         score_weights: dict = None, score_targets: dict = None,
                         employee_weights: dict = None, employee_targets: dict = None):
    """
    Save analysis configuration to a JSON file.

    Args:
        start_date: Start date string (YYYY-MM-DD format)
        end_date: End date string (YYYY-MM-DD format)
        selected_analyses: List of selected analysis function names
        selected_cities: List of selected city names (empty = no filter, all cities)
        faculty_totals: Mapping of faculty name -> total students, entered on the analysis page
        top_employee_n: How many employees the top-employee plots should show
        score_weights: Weights for the hami performance score, keyed as HAMI_SCORE_WEIGHTS
        score_targets: Targets for the absolute score, keyed as HAMI_SCORE_TARGETS
        employee_weights: Weights for the employee score, keyed as EMPLOYEE_SCORE_WEIGHTS
        employee_targets: Targets for the employee score, keyed as EMPLOYEE_SCORE_TARGETS
    """
    import json

    config_data = {
        'start_date': start_date or '',
        'end_date': end_date or '',
        'selected_analyses': selected_analyses or [],
        'selected_cities': selected_cities or [],
        'faculty_totals': faculty_totals or {},
        'top_employee_n': top_employee_n or DEFAULT_TOP_EMPLOYEE_N,
        'score_weights': score_weights or dict(HAMI_SCORE_WEIGHTS),
        'score_targets': score_targets or dict(HAMI_SCORE_TARGETS),
        'employee_weights': employee_weights or dict(EMPLOYEE_SCORE_WEIGHTS),
        'employee_targets': employee_targets or dict(EMPLOYEE_SCORE_TARGETS)
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
        dict: Configuration with keys 'start_date', 'end_date', 'selected_analyses',
              'selected_cities', 'faculty_totals', 'top_employee_n', 'score_weights',
              'score_targets', 'employee_weights', 'employee_targets'
    """
    import json

    default_config = {
        'start_date': '',
        'end_date': '',
        'selected_analyses': [],
        'selected_cities': [],
        'faculty_totals': {},
        'top_employee_n': DEFAULT_TOP_EMPLOYEE_N,
        'score_weights': dict(HAMI_SCORE_WEIGHTS),
        'score_targets': dict(HAMI_SCORE_TARGETS),
        'employee_weights': dict(EMPLOYEE_SCORE_WEIGHTS),
        'employee_targets': dict(EMPLOYEE_SCORE_TARGETS)
    }

    if not ANALYSIS_CONFIG_FILE.exists():
        return default_config

    try:
        with open(ANALYSIS_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            return {
                'start_date': config_data.get('start_date', ''),
                'end_date': config_data.get('end_date', ''),
                'selected_analyses': config_data.get('selected_analyses', []),
                'selected_cities': config_data.get('selected_cities', []),
                'faculty_totals': config_data.get('faculty_totals', {}),
                'top_employee_n': config_data.get('top_employee_n', DEFAULT_TOP_EMPLOYEE_N),
                # Older config files predate the score, so fall back to the defaults.
                'score_weights': {**HAMI_SCORE_WEIGHTS, **config_data.get('score_weights', {})},
                'score_targets': {**HAMI_SCORE_TARGETS, **config_data.get('score_targets', {})},
                'employee_weights': {**EMPLOYEE_SCORE_WEIGHTS, **config_data.get('employee_weights', {})},
                'employee_targets': {**EMPLOYEE_SCORE_TARGETS, **config_data.get('employee_targets', {})}
            }
    except Exception as e:
        print(f"Error loading analysis config: {e}")
        return default_config
