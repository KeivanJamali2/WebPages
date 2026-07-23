"""
Analysis Package for PMO Website
=================================

This package provides:
- DataService: Helper class to query daily forms & project data from the database.
- AnalysisEngine: Stub engine (to be implemented by the user for engineering analysis).

USAGE:
    from analysis import DataService, AnalysisEngine

    # DataService — get raw data from database
    service = DataService(db, project_id)
    forms = service.get_all_forms()
    hr_data = service.get_human_resources()
    ...

    # AnalysisEngine — your custom analysis (implement yourself)
    engine = AnalysisEngine(db, project_id, project_config)
    result = engine.run()
"""

from .data_service import DataService
from .engine import AnalysisEngine

__all__ = [
    'DataService',
    'AnalysisEngine',
]
