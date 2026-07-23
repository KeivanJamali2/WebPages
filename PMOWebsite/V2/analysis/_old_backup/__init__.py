"""
=============================================================================
Analysis Package for PMO Website
=============================================================================

This package contains all analysis modules for the boss dashboard.
Each module provides specific analysis functions that can be combined
for comprehensive project monitoring and reporting.

MODULES:
    - physical_progress: Physical progress analysis by activity and overall
    - financial: Cost analysis, budget tracking, earned value
    - resources: Equipment and human resources utilization
    - materials: Material consumption and inventory tracking
    - schedule: Time analysis, weather impact, completion estimates
    - safety: HSE metrics, incident tracking, compliance
    - issues: Problem tracking and categorization
    - kpi: Key Performance Indicators and health scores
    - comparative: Period-over-period and cross-project comparisons
    - engine: Combined analysis engine that integrates all modules

USAGE:
    from analysis import AnalysisEngine
    
    engine = AnalysisEngine(db, project_id, project_config)
    dashboard = engine.get_boss_dashboard()
    
    # Or use individual modules:
    from analysis import PhysicalProgressAnalysis
    progress = PhysicalProgressAnalysis(db, project_id, project_config)
"""

from .engine import AnalysisEngine
from .physical_progress import PhysicalProgressAnalysis
from .financial import FinancialAnalysis
from .resources import ResourceAnalysis
from .materials import MaterialAnalysis
from .schedule import ScheduleAnalysis
from .safety import SafetyAnalysis
from .issues import IssueAnalysis
from .kpi import KPIAnalysis
from .comparative import ComparativeAnalysis

__all__ = [
    'AnalysisEngine',
    'PhysicalProgressAnalysis',
    'FinancialAnalysis',
    'ResourceAnalysis',
    'MaterialAnalysis',
    'ScheduleAnalysis',
    'SafetyAnalysis',
    'IssueAnalysis',
    'KPIAnalysis',
    'ComparativeAnalysis'
]
