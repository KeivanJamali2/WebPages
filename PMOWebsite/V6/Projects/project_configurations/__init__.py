"""
=============================================================================
Project Configurations Package
=============================================================================

This package contains individual configuration files for each project.
Each project has its own Python file with all the necessary configuration.

USAGE:
    from Projects.project_configurations import load_project_config
    
    config = load_project_config("Project-01")
    
ADDING A NEW PROJECT:
    1. Copy _DEFAULT_TEMPLATE.py to Project_XX.py (use underscore, not dash)
    2. Fill in all the values
    3. Set is_configured = True
    4. The system will automatically find and load it
"""

import os
import importlib
import copy
from pathlib import Path


# Cache for loaded configurations
_config_cache = {}


def get_project_config_path():
    """Get the path to the project_configurations directory."""
    return Path(__file__).parent


def list_available_projects():
    """
    List all available project configuration files.
    
    Returns:
        List of project codes (e.g., ["Project-01", "Project-02"])
    """
    config_path = get_project_config_path()
    projects = []
    
    for file in config_path.glob("Project_*.py"):
        # Convert filename to project code: Project_01.py -> Project-01
        project_code = file.stem.replace("_", "-")
        projects.append(project_code)
    
    return sorted(projects)


def load_project_config(project_code, use_cache=True):
    """
    Load configuration for a specific project.
    
    Args:
        project_code: Project code (e.g., "Project-01")
        use_cache: Whether to use cached config (default: True)
        
    Returns:
        Configuration dictionary for the project
        
    Raises:
        FileNotFoundError: If project config file doesn't exist
    """
    if use_cache and project_code in _config_cache:
        return copy.deepcopy(_config_cache[project_code])
    
    # Convert project code to module name: Project-01 -> Project_01
    module_name = project_code.replace("-", "_")
    
    try:
        # Import the project-specific module
        module = importlib.import_module(f".{module_name}", package="Projects.project_configurations")
        
        # Get the configuration
        config = module.get_configuration()
        
        # Cache it
        _config_cache[project_code] = config
        
        return copy.deepcopy(config)
        
    except ModuleNotFoundError:
        raise FileNotFoundError(f"Configuration file for {project_code} not found. "
                               f"Expected file: Projects/project_configurations/{module_name}.py")


def load_project_info(project_code):
    """
    Load basic project information.
    
    Args:
        project_code: Project code (e.g., "Project-01")
        
    Returns:
        Project info dictionary
    """
    module_name = project_code.replace("-", "_")
    
    try:
        module = importlib.import_module(f".{module_name}", package="Projects.project_configurations")
        return module.get_project_info()
    except ModuleNotFoundError:
        raise FileNotFoundError(f"Configuration file for {project_code} not found.")


def is_project_configured(project_code):
    """
    Check if a project configuration has been filled in.
    
    Args:
        project_code: Project code (e.g., "Project-01")
        
    Returns:
        True if is_configured = True in the config file
    """
    module_name = project_code.replace("-", "_")
    
    try:
        module = importlib.import_module(f".{module_name}", package="Projects.project_configurations")
        return getattr(module, 'is_configured', False)
    except ModuleNotFoundError:
        return False


def clear_config_cache():
    """Clear the configuration cache."""
    global _config_cache
    _config_cache = {}


def reload_project_config(project_code):
    """
    Force reload a project configuration (useful during development).
    
    Args:
        project_code: Project code (e.g., "Project-01")
        
    Returns:
        Fresh configuration dictionary
    """
    module_name = project_code.replace("-", "_")
    full_module_name = f"Projects.project_configurations.{module_name}"
    
    # Remove from cache
    if project_code in _config_cache:
        del _config_cache[project_code]
    
    # Reload the module
    if full_module_name in importlib.sys.modules:
        importlib.reload(importlib.sys.modules[full_module_name])
    
    return load_project_config(project_code, use_cache=False)


# =============================================================================
# HELPER FUNCTIONS FOR ACCESSING SPECIFIC CONFIG SECTIONS
# =============================================================================

def get_human_resources(project_code):
    """Get list of human resource positions for a project."""
    config = load_project_config(project_code)
    return config.get("Human_Resources", [])


def get_human_resources_rates(project_code):
    """Get planned days and rates for human resources."""
    config = load_project_config(project_code)
    return config.get("Human_Resources_Rates", {})


def get_equipment_types(project_code):
    """Get equipment types and models for a project."""
    config = load_project_config(project_code)
    return config.get("Tools_And_Equipments", {})


def get_equipment_costs(project_code):
    """Get equipment costs (hourly rates and planned quantities)."""
    config = load_project_config(project_code)
    return config.get("Equipment_Costs", {})


def get_materials(project_code):
    """Get materials and their units."""
    config = load_project_config(project_code)
    return config.get("Incoming_Materials_And_Goods", {})


def get_material_prices(project_code):
    """Get material prices and planned totals. (Deprecated: Material_Prices removed from config.)"""
    config = load_project_config(project_code)
    return config.get("Material_Prices", {})


def get_activities(project_code):
    """Get activities and their units."""
    config = load_project_config(project_code)
    return config.get("Daily_Activity_Report", {})


def get_activity_budget(project_code):
    """Get activity budgets (planned amounts and unit prices)."""
    config = load_project_config(project_code)
    return config.get("Activity_Budget", {})


def get_project_issues(project_code):
    """Get list of project issue types."""
    config = load_project_config(project_code)
    return config.get("Project_Issues", [])


def get_climate_conditions(project_code):
    """Get climate condition fields."""
    config = load_project_config(project_code)
    return config.get("Climate_Condition", [])
