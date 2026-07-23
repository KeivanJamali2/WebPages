"""
=============================================================================
Detailed Analysis Engine - Comprehensive Analysis Module
=============================================================================

This module provides 40+ detailed analyses organized into 9 categories:
1. Physical Progress (پیشرفت فیزیکی)
2. Financial Analysis (تحلیل مالی)
3. Resource Utilization (استفاده از منابع)
4. Material Management (مدیریت مصالح)
5. Schedule & Time (تحلیل زمانی)
6. Safety & HSE (ایمنی)
7. Issue Tracking (پیگیری مشکلات)
8. Executive KPIs (شاخص‌های کلیدی)
9. Comparative Reports (گزارش‌های مقایسه‌ای)

Each analysis handles missing data gracefully.
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, extract
from collections import defaultdict
import jdatetime

# Import analysis modules
from analysis.physical_progress import PhysicalProgressAnalysis
from analysis.financial import FinancialAnalysis
from analysis.resources import ResourceAnalysis
from analysis.materials import MaterialAnalysis
from analysis.schedule import ScheduleAnalysis
from analysis.safety import SafetyAnalysis
from analysis.issues import IssueAnalysis
from analysis.kpi import KPIAnalysis
from analysis.comparative import ComparativeAnalysis


def to_jalali(date_obj, format_str='%Y/%m/%d'):
    """Convert a date to Jalali (Persian calendar) format."""
    if date_obj is None:
        return None
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
        except:
            return date_obj
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    try:
        jalali_date = jdatetime.date.fromgregorian(date=date_obj)
        return jalali_date.strftime(format_str)
    except:
        return str(date_obj)


# Bilingual analysis translations
DETAIL_TRANSLATIONS = {
    'en': {
        # Categories
        'cat_physical': 'Physical Progress',
        'cat_financial': 'Financial Analysis',
        'cat_resources': 'Resource Utilization',
        'cat_materials': 'Material Management',
        'cat_schedule': 'Schedule & Time',
        'cat_safety': 'Safety & HSE',
        'cat_issues': 'Issue Tracking',
        'cat_kpi': 'Executive KPIs',
        'cat_comparative': 'Comparative Reports',
        
        # Physical Progress Analyses
        'progress_by_activity': 'Progress by Activity',
        'overall_progress': 'Overall Physical Progress',
        'progress_trend': 'Progress Trend',
        'progress_velocity': 'Progress Velocity',
        'roadmap_coverage': 'Roadmap Coverage',
        
        # Financial Analyses
        'daily_cost': 'Daily Cost Breakdown',
        'monthly_cost': 'Monthly Cost Breakdown',
        'budget_vs_actual': 'Budget vs Actual',
        'cost_per_activity': 'Cost per Activity',
        'evm_analysis': 'Earned Value (EVM)',
        'cost_forecast': 'Cost Forecast (EAC)',
        
        # Resource Analyses
        'equipment_utilization': 'Equipment Utilization Rate',
        'equipment_downtime': 'Equipment Downtime',
        'planned_vs_actual_eq': 'Planned vs Actual Equipment',
        'manhours_by_position': 'Man-Hours by Position',
        'hr_cost_distribution': 'HR Cost Distribution',
        
        # Material Analyses
        'material_consumption': 'Material Consumption Progress',
        'current_inventory': 'Current Inventory',
        'material_cost': 'Material Cost Spent',
        'supply_rate': 'Supply Rate Analysis',
        'at_risk_materials': 'Materials at Risk',
        
        # Schedule Analyses
        'working_days': 'Working Days Analysis',
        'weather_impact': 'Weather Impact Days',
        'issue_impact': 'Issue Impact on Schedule',
        'estimated_completion': 'Estimated Completion Date',
        'schedule_variance': 'Schedule Variance (SV)',
        
        # Safety Analyses
        'incident_rate': 'Incident Rate',
        'inspection_compliance': 'Inspection Compliance',
        'near_miss': 'Near-Miss Tracking',
        'safety_trend': 'Safety Trend',
        'days_without_incident': 'Days Without Incident',
        
        # Issue Analyses
        'issues_by_category': 'Issues by Category',
        'issue_frequency': 'Issue Frequency Trend',
        'problem_locations': 'Most Problematic Locations',
        'issue_duration': 'Issue Duration Analysis',
        
        # KPI Analyses
        'health_score': 'Project Health Score',
        'cpi_analysis': 'Cost Performance Index (CPI)',
        'spi_analysis': 'Schedule Performance Index (SPI)',
        'burn_rate': 'Budget Burn Rate',
        'days_to_completion': 'Days to Completion',
        
        # Comparative Analyses
        'month_over_month': 'This Month vs Last Month',
        'project_comparison': 'Project vs Project',
        'actual_vs_planned': 'Actual vs Planned (All)',
        'weekly_report': 'Weekly Progress Report',
        
        # Status messages
        'no_data': 'Insufficient data for this analysis',
        'loading': 'Loading...',
        'error': 'Error loading analysis',
        'needs_config': 'Requires project configuration',
    },
    'fa': {
        # Categories
        'cat_physical': 'پیشرفت فیزیکی',
        'cat_financial': 'تحلیل مالی',
        'cat_resources': 'استفاده از منابع',
        'cat_materials': 'مدیریت مصالح',
        'cat_schedule': 'تحلیل زمانی',
        'cat_safety': 'ایمنی و HSE',
        'cat_issues': 'پیگیری مشکلات',
        'cat_kpi': 'شاخص‌های کلیدی',
        'cat_comparative': 'گزارش‌های مقایسه‌ای',
        
        # Physical Progress Analyses
        'progress_by_activity': 'پیشرفت بر حسب فعالیت',
        'overall_progress': 'پیشرفت فیزیکی کل',
        'progress_trend': 'روند پیشرفت',
        'progress_velocity': 'سرعت پیشرفت',
        'roadmap_coverage': 'پوشش نقشه راه',
        
        # Financial Analyses
        'daily_cost': 'تفکیک هزینه روزانه',
        'monthly_cost': 'تفکیک هزینه ماهانه',
        'budget_vs_actual': 'بودجه در مقابل واقعی',
        'cost_per_activity': 'هزینه هر فعالیت',
        'evm_analysis': 'ارزش کسب شده (EVM)',
        'cost_forecast': 'پیش‌بینی هزینه (EAC)',
        
        # Resource Analyses
        'equipment_utilization': 'نرخ بهره‌وری تجهیزات',
        'equipment_downtime': 'زمان خرابی تجهیزات',
        'planned_vs_actual_eq': 'تجهیزات برنامه‌ریزی در مقابل واقعی',
        'manhours_by_position': 'نفر-ساعت بر حسب سمت',
        'hr_cost_distribution': 'توزیع هزینه نیروی انسانی',
        
        # Material Analyses
        'material_consumption': 'پیشرفت مصرف مصالح',
        'current_inventory': 'موجودی فعلی',
        'material_cost': 'هزینه مصالح',
        'supply_rate': 'تحلیل نرخ تأمین',
        'at_risk_materials': 'مصالح در خطر',
        
        # Schedule Analyses
        'working_days': 'تحلیل روزهای کاری',
        'weather_impact': 'تأثیر آب و هوا',
        'issue_impact': 'تأثیر مشکلات بر زمان‌بندی',
        'estimated_completion': 'تاریخ تخمینی اتمام',
        'schedule_variance': 'انحراف زمان‌بندی (SV)',
        
        # Safety Analyses
        'incident_rate': 'نرخ حوادث',
        'inspection_compliance': 'انطباق بازرسی',
        'near_miss': 'رصد رویدادهای نزدیک',
        'safety_trend': 'روند ایمنی',
        'days_without_incident': 'روز بدون حادثه',
        
        # Issue Analyses
        'issues_by_category': 'مشکلات بر حسب دسته',
        'issue_frequency': 'روند تکرار مشکلات',
        'problem_locations': 'مکان‌های پرمشکل',
        'issue_duration': 'تحلیل مدت زمان مشکلات',
        
        # KPI Analyses
        'health_score': 'امتیاز سلامت پروژه',
        'cpi_analysis': 'شاخص عملکرد هزینه (CPI)',
        'spi_analysis': 'شاخص عملکرد زمان‌بندی (SPI)',
        'burn_rate': 'نرخ مصرف بودجه',
        'days_to_completion': 'روز تا اتمام',
        
        # Comparative Analyses
        'month_over_month': 'این ماه در مقابل ماه قبل',
        'project_comparison': 'مقایسه پروژه‌ها',
        'actual_vs_planned': 'واقعی در مقابل برنامه (همه)',
        'weekly_report': 'گزارش پیشرفت هفتگی',
        
        # Status messages
        'no_data': 'داده کافی برای این تحلیل موجود نیست',
        'loading': 'در حال بارگذاری...',
        'error': 'خطا در بارگذاری تحلیل',
        'needs_config': 'نیاز به پیکربندی پروژه دارد',
    }
}


def get_text(key, lang='en'):
    """Get translated text."""
    return DETAIL_TRANSLATIONS.get(lang, DETAIL_TRANSLATIONS['en']).get(key, key)


class DetailedAnalysisEngine:
    """
    Comprehensive analysis engine providing 40+ detailed analyses.
    
    Each analysis method returns a standardized format:
    {
        'success': bool,
        'title': str,
        'data': dict or list,
        'chart_type': str (optional),
        'message': str (if no data)
    }
    """
    
    def __init__(self, db, project_id, project_config=None, lang='en'):
        """
        Initialize the detailed analysis engine.
        
        Args:
            db: SQLAlchemy database instance
            project_id: Project ID to analyze
            project_config: Project configuration dictionary
            lang: Language for output ('en' or 'fa')
        """
        self.db = db
        self.project_id = project_id
        self.project_config = project_config or {}
        self.lang = lang
        
        # Initialize sub-modules
        self.physical_progress = PhysicalProgressAnalysis(db, project_id, project_config)
        self.financial = FinancialAnalysis(db, project_id, project_config)
        self.resources = ResourceAnalysis(db, project_id, project_config)
        self.materials = MaterialAnalysis(db, project_id, project_config)
        self.schedule = ScheduleAnalysis(db, project_id, project_config)
        self.safety = SafetyAnalysis(db, project_id, project_config)
        self.issues = IssueAnalysis(db, project_id, project_config)
        self.kpi = KPIAnalysis(db, project_id, project_config, lang)
        self.comparative = ComparativeAnalysis(db, project_id, project_config, lang)
    
    def _format_date(self, date_obj):
        """Format date based on language."""
        if self.lang == 'fa':
            return to_jalali(date_obj)
        return date_obj.isoformat() if hasattr(date_obj, 'isoformat') else str(date_obj)
    
    def _no_data_response(self, title_key):
        """Return a standardized no-data response."""
        return {
            'success': False,
            'title': get_text(title_key, self.lang),
            'message': get_text('no_data', self.lang),
            'data': None
        }
    
    def get_analysis_categories(self):
        """
        Get all analysis categories with their analyses.
        
        Returns:
            list: Categories with nested analyses
        """
        return [
            {
                'id': 'physical',
                'title': get_text('cat_physical', self.lang),
                'icon': '📈',
                'color': '#10b981',
                'analyses': [
                    {'id': 'progress_by_activity', 'title': get_text('progress_by_activity', self.lang)},
                    {'id': 'overall_progress', 'title': get_text('overall_progress', self.lang)},
                    {'id': 'progress_trend', 'title': get_text('progress_trend', self.lang)},
                    {'id': 'progress_velocity', 'title': get_text('progress_velocity', self.lang)},
                    {'id': 'roadmap_coverage', 'title': get_text('roadmap_coverage', self.lang)},
                ]
            },
            {
                'id': 'financial',
                'title': get_text('cat_financial', self.lang),
                'icon': '💰',
                'color': '#3b82f6',
                'analyses': [
                    {'id': 'daily_cost', 'title': get_text('daily_cost', self.lang)},
                    {'id': 'monthly_cost', 'title': get_text('monthly_cost', self.lang)},
                    {'id': 'budget_vs_actual', 'title': get_text('budget_vs_actual', self.lang)},
                    {'id': 'cost_per_activity', 'title': get_text('cost_per_activity', self.lang)},
                    {'id': 'evm_analysis', 'title': get_text('evm_analysis', self.lang)},
                    {'id': 'cost_forecast', 'title': get_text('cost_forecast', self.lang)},
                ]
            },
            {
                'id': 'resources',
                'title': get_text('cat_resources', self.lang),
                'icon': '🔧',
                'color': '#6366f1',
                'analyses': [
                    {'id': 'equipment_utilization', 'title': get_text('equipment_utilization', self.lang)},
                    {'id': 'equipment_downtime', 'title': get_text('equipment_downtime', self.lang)},
                    {'id': 'planned_vs_actual_eq', 'title': get_text('planned_vs_actual_eq', self.lang)},
                    {'id': 'manhours_by_position', 'title': get_text('manhours_by_position', self.lang)},
                    {'id': 'hr_cost_distribution', 'title': get_text('hr_cost_distribution', self.lang)},
                ]
            },
            {
                'id': 'materials',
                'title': get_text('cat_materials', self.lang),
                'icon': '📦',
                'color': '#f59e0b',
                'analyses': [
                    {'id': 'material_consumption', 'title': get_text('material_consumption', self.lang)},
                    {'id': 'current_inventory', 'title': get_text('current_inventory', self.lang)},
                    {'id': 'material_cost', 'title': get_text('material_cost', self.lang)},
                    {'id': 'supply_rate', 'title': get_text('supply_rate', self.lang)},
                    {'id': 'at_risk_materials', 'title': get_text('at_risk_materials', self.lang)},
                ]
            },
            {
                'id': 'schedule',
                'title': get_text('cat_schedule', self.lang),
                'icon': '📅',
                'color': '#8b5cf6',
                'analyses': [
                    {'id': 'working_days', 'title': get_text('working_days', self.lang)},
                    {'id': 'weather_impact', 'title': get_text('weather_impact', self.lang)},
                    {'id': 'issue_impact', 'title': get_text('issue_impact', self.lang)},
                    {'id': 'estimated_completion', 'title': get_text('estimated_completion', self.lang)},
                    {'id': 'schedule_variance', 'title': get_text('schedule_variance', self.lang)},
                ]
            },
            {
                'id': 'safety',
                'title': get_text('cat_safety', self.lang),
                'icon': '🛡️',
                'color': '#ef4444',
                'analyses': [
                    {'id': 'incident_rate', 'title': get_text('incident_rate', self.lang)},
                    {'id': 'inspection_compliance', 'title': get_text('inspection_compliance', self.lang)},
                    {'id': 'near_miss', 'title': get_text('near_miss', self.lang)},
                    {'id': 'safety_trend', 'title': get_text('safety_trend', self.lang)},
                    {'id': 'days_without_incident', 'title': get_text('days_without_incident', self.lang)},
                ]
            },
            {
                'id': 'issues',
                'title': get_text('cat_issues', self.lang),
                'icon': '⚠️',
                'color': '#f97316',
                'analyses': [
                    {'id': 'issues_by_category', 'title': get_text('issues_by_category', self.lang)},
                    {'id': 'issue_frequency', 'title': get_text('issue_frequency', self.lang)},
                    {'id': 'problem_locations', 'title': get_text('problem_locations', self.lang)},
                    {'id': 'issue_duration', 'title': get_text('issue_duration', self.lang)},
                ]
            },
            {
                'id': 'kpi',
                'title': get_text('cat_kpi', self.lang),
                'icon': '🎯',
                'color': '#ec4899',
                'analyses': [
                    {'id': 'health_score', 'title': get_text('health_score', self.lang)},
                    {'id': 'cpi_analysis', 'title': get_text('cpi_analysis', self.lang)},
                    {'id': 'spi_analysis', 'title': get_text('spi_analysis', self.lang)},
                    {'id': 'burn_rate', 'title': get_text('burn_rate', self.lang)},
                    {'id': 'days_to_completion', 'title': get_text('days_to_completion', self.lang)},
                ]
            },
            {
                'id': 'comparative',
                'title': get_text('cat_comparative', self.lang),
                'icon': '📊',
                'color': '#14b8a6',
                'analyses': [
                    {'id': 'month_over_month', 'title': get_text('month_over_month', self.lang)},
                    {'id': 'actual_vs_planned', 'title': get_text('actual_vs_planned', self.lang)},
                    {'id': 'weekly_report', 'title': get_text('weekly_report', self.lang)},
                ]
            },
        ]
    
    def get_analysis(self, analysis_id):
        """
        Get a specific analysis by ID.
        
        Args:
            analysis_id: The analysis identifier
            
        Returns:
            dict: Analysis result
        """
        analysis_map = {
            # Physical Progress
            'progress_by_activity': self.get_progress_by_activity,
            'overall_progress': self.get_overall_progress,
            'progress_trend': self.get_progress_trend,
            'progress_velocity': self.get_progress_velocity,
            'roadmap_coverage': self.get_roadmap_coverage,
            
            # Financial
            'daily_cost': self.get_daily_cost,
            'monthly_cost': self.get_monthly_cost,
            'budget_vs_actual': self.get_budget_vs_actual,
            'cost_per_activity': self.get_cost_per_activity,
            'evm_analysis': self.get_evm_analysis,
            'cost_forecast': self.get_cost_forecast,
            
            # Resources
            'equipment_utilization': self.get_equipment_utilization,
            'equipment_downtime': self.get_equipment_downtime,
            'planned_vs_actual_eq': self.get_planned_vs_actual_equipment,
            'manhours_by_position': self.get_manhours_by_position,
            'hr_cost_distribution': self.get_hr_cost_distribution,
            
            # Materials
            'material_consumption': self.get_material_consumption,
            'current_inventory': self.get_current_inventory,
            'material_cost': self.get_material_cost,
            'supply_rate': self.get_supply_rate,
            'at_risk_materials': self.get_at_risk_materials,
            
            # Schedule
            'working_days': self.get_working_days,
            'weather_impact': self.get_weather_impact,
            'issue_impact': self.get_issue_impact,
            'estimated_completion': self.get_estimated_completion,
            'schedule_variance': self.get_schedule_variance,
            
            # Safety
            'incident_rate': self.get_incident_rate,
            'inspection_compliance': self.get_inspection_compliance,
            'near_miss': self.get_near_miss,
            'safety_trend': self.get_safety_trend,
            'days_without_incident': self.get_days_without_incident,
            
            # Issues
            'issues_by_category': self.get_issues_by_category,
            'issue_frequency': self.get_issue_frequency,
            'problem_locations': self.get_problem_locations,
            'issue_duration': self.get_issue_duration,
            
            # KPI
            'health_score': self.get_health_score,
            'cpi_analysis': self.get_cpi_analysis,
            'spi_analysis': self.get_spi_analysis,
            'burn_rate': self.get_burn_rate,
            'days_to_completion': self.get_days_to_completion,
            
            # Comparative
            'month_over_month': self.get_month_over_month,
            'actual_vs_planned': self.get_actual_vs_planned,
            'weekly_report': self.get_weekly_report,
        }
        
        handler = analysis_map.get(analysis_id)
        if handler:
            try:
                return handler()
            except Exception as e:
                return {
                    'success': False,
                    'title': analysis_id,
                    'message': f"{get_text('error', self.lang)}: {str(e)}",
                    'data': None
                }
        
        return {
            'success': False,
            'title': analysis_id,
            'message': f"Unknown analysis: {analysis_id}",
            'data': None
        }
    
    # =========================================================================
    # PHYSICAL PROGRESS ANALYSES
    # =========================================================================
    
    def get_progress_by_activity(self):
        """Progress percentage for each activity type."""
        try:
            data = self.physical_progress.get_progress_by_activity()
            
            if not data:
                return self._no_data_response('progress_by_activity')
            
            # Format for display
            activities = []
            for name, info in data.items():
                activities.append({
                    'name': name,
                    'actual': round(info['actual'], 2),
                    'planned': round(info['planned'], 2),
                    'progress': round(info['progress_percent'], 1),
                    'remaining': round(info['remaining'], 2),
                    'unit': info['unit']
                })
            
            # Sort by progress
            activities.sort(key=lambda x: x['progress'], reverse=True)
            
            return {
                'success': True,
                'title': get_text('progress_by_activity', self.lang),
                'chart_type': 'horizontal_bar',
                'data': {
                    'activities': activities,
                    'labels': [a['name'] for a in activities],
                    'values': [a['progress'] for a in activities],
                    'total_activities': len(activities),
                    'completed': sum(1 for a in activities if a['progress'] >= 100)
                }
            }
        except Exception as e:
            return self._no_data_response('progress_by_activity')
    
    def get_overall_progress(self):
        """Overall project physical progress with weighted average."""
        try:
            data = self.physical_progress.get_overall_progress()
            
            return {
                'success': True,
                'title': get_text('overall_progress', self.lang),
                'chart_type': 'gauge',
                'data': {
                    'weighted_progress': round(data['weighted_progress'], 1),
                    'simple_progress': round(data['simple_progress'], 1),
                    'total_planned_value': round(data['total_planned_value'], 0),
                    'total_actual_value': round(data['total_actual_value'], 0),
                    'activities_count': data['activities_count'],
                    'activities_completed': data['activities_completed'],
                    'completion_rate': round((data['activities_completed'] / data['activities_count'] * 100) if data['activities_count'] > 0 else 0, 1)
                }
            }
        except Exception as e:
            return self._no_data_response('overall_progress')
    
    def get_progress_trend(self):
        """Progress trend over time (daily/weekly/monthly)."""
        try:
            daily = self.physical_progress.get_progress_trend(30, 'daily')
            weekly = self.physical_progress.get_progress_trend(90, 'weekly')
            
            if not daily:
                return self._no_data_response('progress_trend')
            
            # Format dates for display
            for item in daily:
                if 'date' in item:
                    item['date_display'] = self._format_date(item['date']) if isinstance(item['date'], str) else item['date']
            
            for item in weekly:
                if 'date' in item:
                    item['date_display'] = self._format_date(item['date']) if isinstance(item['date'], str) else item['date']
            
            return {
                'success': True,
                'title': get_text('progress_trend', self.lang),
                'chart_type': 'line',
                'data': {
                    'daily': daily,
                    'weekly': weekly,
                    'labels': [d['date_display'] for d in daily],
                    'values': [d['cumulative_progress'] for d in daily]
                }
            }
        except Exception as e:
            return self._no_data_response('progress_trend')
    
    def get_progress_velocity(self):
        """Progress velocity (rate of work completion)."""
        try:
            data = self.physical_progress.get_progress_velocity()
            
            # Translate trend
            trend_text = data['trend']
            if self.lang == 'fa':
                trend_map = {
                    'increasing': 'در حال افزایش',
                    'decreasing': 'در حال کاهش',
                    'stable': 'پایدار'
                }
                trend_text = trend_map.get(data['trend'], data['trend'])
            
            return {
                'success': True,
                'title': get_text('progress_velocity', self.lang),
                'chart_type': 'metric_card',
                'data': {
                    'daily_average': round(data['daily_average'], 2),
                    'weekly_average': round(data['weekly_average'], 2),
                    'last_7_days': round(data['last_7_days'], 2),
                    'last_30_days': round(data['last_30_days'], 2),
                    'trend': data['trend'],
                    'trend_text': trend_text,
                    'working_days': data['working_days'],
                    'trend_direction': 'up' if data['trend'] == 'increasing' else ('down' if data['trend'] == 'decreasing' else 'stable')
                }
            }
        except Exception as e:
            return self._no_data_response('progress_velocity')
    
    def get_roadmap_coverage(self):
        """Visual roadmap showing completed vs remaining sections."""
        try:
            data = self.physical_progress.get_roadmap_coverage()
            
            if not data['activities']:
                return self._no_data_response('roadmap_coverage')
            
            # Format for visualization
            activities = []
            for name, info in data['activities'].items():
                activities.append({
                    'name': name,
                    'total_length': round(info['total_length'], 2),
                    'coverage_percent': round(info['coverage_percent'], 1),
                    'segments': info['segments'][:10]  # Limit for display
                })
            
            return {
                'success': True,
                'title': get_text('roadmap_coverage', self.lang),
                'chart_type': 'roadmap',
                'data': {
                    'activities': activities,
                    'global_min': data['global_min'],
                    'global_max': data['global_max'],
                    'total_range': data['total_coverage']
                }
            }
        except Exception as e:
            return self._no_data_response('roadmap_coverage')
    
    # =========================================================================
    # FINANCIAL ANALYSES
    # =========================================================================
    
    def get_daily_cost(self):
        """Cost breakdown for a specific date."""
        try:
            data = self.financial.get_daily_cost_breakdown()
            
            if data['total_cost'] == 0:
                return self._no_data_response('daily_cost')
            
            # Format for display
            date_display = self._format_date(data['date'])
            
            return {
                'success': True,
                'title': get_text('daily_cost', self.lang),
                'chart_type': 'pie_and_table',
                'data': {
                    'date': date_display,
                    'labor_cost': round(data['labor_cost'], 0),
                    'equipment_cost': round(data['equipment_cost'], 0),
                    'material_cost': round(data['material_cost'], 0),
                    'activity_cost': round(data['activity_cost'], 0),
                    'total_cost': round(data['total_cost'], 0),
                    'chart_data': [
                        {'name': 'نیروی کار' if self.lang == 'fa' else 'Labor', 'value': data['labor_cost']},
                        {'name': 'تجهیزات' if self.lang == 'fa' else 'Equipment', 'value': data['equipment_cost']},
                        {'name': 'مصالح' if self.lang == 'fa' else 'Materials', 'value': data['material_cost']},
                        {'name': 'فعالیت‌ها' if self.lang == 'fa' else 'Activities', 'value': data['activity_cost']},
                    ],
                    'details': data['details']
                }
            }
        except Exception as e:
            return self._no_data_response('daily_cost')
    
    def get_monthly_cost(self):
        """Monthly financial breakdown with daily totals."""
        try:
            data = self.financial.get_monthly_breakdown()
            
            if not data['daily_costs']:
                return self._no_data_response('monthly_cost')
            
            # Format dates
            for day in data['daily_costs']:
                day['date_display'] = self._format_date(day['date'])
            
            month_name = data['month_name']
            if self.lang == 'fa':
                try:
                    jdate = jdatetime.date(data['year'], data['month'], 1)
                    month_name = jdate.strftime('%B')
                except:
                    pass
            
            return {
                'success': True,
                'title': get_text('monthly_cost', self.lang),
                'chart_type': 'bar_and_table',
                'data': {
                    'year': data['year'],
                    'month': data['month'],
                    'month_name': month_name,
                    'working_days': data['working_days'],
                    'daily_costs': data['daily_costs'],
                    'totals': data['totals'],
                    'daily_average': round(data['averages']['daily_cost'], 0),
                    'chart_labels': [d['date_display'] for d in data['daily_costs']],
                    'chart_values': [d['total'] for d in data['daily_costs']]
                }
            }
        except Exception as e:
            return self._no_data_response('monthly_cost')
    
    def get_budget_vs_actual(self):
        """Compare budget vs actual spending."""
        try:
            data = self.financial.get_budget_vs_actual()
            
            return {
                'success': True,
                'title': get_text('budget_vs_actual', self.lang),
                'chart_type': 'comparison_bar',
                'data': {
                    'budget': {
                        'total': round(data['budget']['total'], 0),
                        'activity': round(data['budget'].get('activity', 0), 0),
                        'equipment': round(data['budget'].get('equipment', 0), 0),
                        'material': round(data['budget'].get('material', 0), 0)
                    },
                    'actual': {
                        'total': round(data['actual']['total'], 0),
                        'labor': round(data['actual']['labor'], 0),
                        'equipment': round(data['actual']['equipment'], 0),
                        'material': round(data['actual']['material'], 0),
                        'activity': round(data['actual']['activity'], 0)
                    },
                    'variance': {
                        'total': round(data['variance']['total'], 0),
                        'percent': round(data['variance']['percent'], 1)
                    },
                    'burn_rate_percent': round(data['burn_rate']['percent'], 1),
                    'status': 'under' if data['variance']['total'] > 0 else ('over' if data['variance']['total'] < 0 else 'on'),
                    'status_text': ('زیر بودجه' if self.lang == 'fa' else 'Under Budget') if data['variance']['total'] > 0 else (('بالاتر از بودجه' if self.lang == 'fa' else 'Over Budget') if data['variance']['total'] < 0 else ('طبق بودجه' if self.lang == 'fa' else 'On Budget'))
                }
            }
        except Exception as e:
            return self._no_data_response('budget_vs_actual')
    
    def get_cost_per_activity(self):
        """Cost breakdown by activity type."""
        try:
            # Get progress by activity and calculate costs
            progress = self.physical_progress.get_progress_by_activity()
            
            if not progress:
                return self._no_data_response('cost_per_activity')
            
            activities = []
            total_cost = 0
            
            for name, info in progress.items():
                cost = info['actual'] * info.get('price_per_unit', 0)
                total_cost += cost
                activities.append({
                    'name': name,
                    'amount': round(info['actual'], 2),
                    'unit': info['unit'],
                    'price_per_unit': info.get('price_per_unit', 0),
                    'total_cost': round(cost, 0)
                })
            
            # Sort by cost
            activities.sort(key=lambda x: x['total_cost'], reverse=True)
            
            return {
                'success': True,
                'title': get_text('cost_per_activity', self.lang),
                'chart_type': 'horizontal_bar',
                'data': {
                    'activities': activities,
                    'total_cost': round(total_cost, 0),
                    'labels': [a['name'] for a in activities[:10]],
                    'values': [a['total_cost'] for a in activities[:10]]
                }
            }
        except Exception as e:
            return self._no_data_response('cost_per_activity')
    
    def get_evm_analysis(self):
        """Earned Value Management analysis."""
        try:
            data = self.financial.get_evm_analysis()
            
            # Translate interpretation
            interpretation = data['interpretation']
            if self.lang == 'fa':
                schedule_map = {'ahead': 'جلوتر از برنامه', 'behind': 'عقب‌تر از برنامه', 'on schedule': 'طبق برنامه'}
                cost_map = {'under budget': 'زیر بودجه', 'over budget': 'بالاتر از بودجه', 'on budget': 'طبق بودجه'}
                health_map = {'good': 'خوب', 'warning': 'هشدار', 'critical': 'بحرانی'}
                
                interpretation = {
                    'schedule': schedule_map.get(interpretation['schedule'], interpretation['schedule']),
                    'cost': cost_map.get(interpretation['cost'], interpretation['cost']),
                    'health': health_map.get(interpretation['health'], interpretation['health'])
                }
            
            return {
                'success': True,
                'title': get_text('evm_analysis', self.lang),
                'chart_type': 'evm_chart',
                'data': {
                    'PV': round(data['PV'], 0),
                    'EV': round(data['EV'], 0),
                    'AC': round(data['AC'], 0),
                    'SV': round(data['SV'], 0),
                    'CV': round(data['CV'], 0),
                    'CPI': round(data['CPI'], 2),
                    'SPI': round(data['SPI'], 2),
                    'EAC': round(data['EAC'], 0),
                    'interpretation': interpretation,
                    'formulas': {
                        'CPI': 'EV / AC',
                        'SPI': 'EV / PV',
                        'EAC': 'Budget / CPI'
                    }
                }
            }
        except Exception as e:
            return self._no_data_response('evm_analysis')
    
    def get_cost_forecast(self):
        """Estimate At Completion (EAC) based on current burn rate."""
        try:
            budget_data = self.financial.get_budget_vs_actual()
            evm_data = self.financial.get_evm_analysis()
            
            budget = budget_data['budget']['total']
            actual = budget_data['actual']['total']
            cpi = evm_data['CPI']
            
            # Different EAC formulas
            eac_cpi = budget / cpi if cpi > 0 else 0  # EAC based on CPI
            eac_typical = actual + (budget - evm_data['EV'])  # EAC typical
            
            return {
                'success': True,
                'title': get_text('cost_forecast', self.lang),
                'chart_type': 'forecast_card',
                'data': {
                    'budget': round(budget, 0),
                    'actual_spent': round(actual, 0),
                    'remaining_budget': round(budget - actual, 0),
                    'eac_cpi': round(eac_cpi, 0),
                    'eac_typical': round(eac_typical, 0),
                    'variance_at_completion': round(budget - eac_cpi, 0),
                    'burn_rate_percent': round(budget_data['burn_rate']['percent'], 1),
                    'cpi': round(cpi, 2),
                    'forecast_status': 'under' if eac_cpi < budget else ('over' if eac_cpi > budget else 'on')
                }
            }
        except Exception as e:
            return self._no_data_response('cost_forecast')
    
    # =========================================================================
    # RESOURCE ANALYSES
    # =========================================================================
    
    def get_equipment_utilization(self):
        """Equipment utilization rates."""
        try:
            data = self.resources.get_equipment_utilization()
            
            if not data:
                return self._no_data_response('equipment_utilization')
            
            equipment_list = []
            for name, info in data.items():
                equipment_list.append({
                    'name': name,
                    'total_hours': round(info['total_hours'], 1),
                    'utilization_rate': round(info['utilization_rate'], 1),
                    'planned_quantity': info['planned_quantity'],
                    'days_used': info['days_used']
                })
            
            # Sort by utilization
            equipment_list.sort(key=lambda x: x['utilization_rate'], reverse=True)
            
            return {
                'success': True,
                'title': get_text('equipment_utilization', self.lang),
                'chart_type': 'bar_with_target',
                'data': {
                    'equipment': equipment_list,
                    'labels': [e['name'] for e in equipment_list[:10]],
                    'values': [e['utilization_rate'] for e in equipment_list[:10]],
                    'target': 80,  # 80% utilization target
                    'average_utilization': round(sum(e['utilization_rate'] for e in equipment_list) / len(equipment_list), 1) if equipment_list else 0
                }
            }
        except Exception as e:
            return self._no_data_response('equipment_utilization')
    
    def get_equipment_downtime(self):
        """Equipment downtime analysis."""
        try:
            data = self.resources.get_equipment_downtime()
            
            if not data:
                return self._no_data_response('equipment_downtime')
            
            equipment_list = []
            for name, info in data.items():
                equipment_list.append({
                    'name': name,
                    'total_days': info['total_days'],
                    'days_used': info['days_used'],
                    'downtime_days': info['downtime_days'],
                    'availability_rate': round(info['availability_rate'], 1)
                })
            
            # Sort by downtime
            equipment_list.sort(key=lambda x: x['downtime_days'], reverse=True)
            
            return {
                'success': True,
                'title': get_text('equipment_downtime', self.lang),
                'chart_type': 'stacked_bar',
                'data': {
                    'equipment': equipment_list,
                    'labels': [e['name'] for e in equipment_list[:10]],
                    'used_values': [e['days_used'] for e in equipment_list[:10]],
                    'downtime_values': [e['downtime_days'] for e in equipment_list[:10]],
                    'total_downtime': sum(e['downtime_days'] for e in equipment_list)
                }
            }
        except Exception as e:
            return self._no_data_response('equipment_downtime')
    
    def get_planned_vs_actual_equipment(self):
        """Compare planned vs actual equipment usage."""
        try:
            data = self.resources.get_planned_vs_actual_resources()
            
            equipment = data.get('equipment', {})
            if not equipment:
                return self._no_data_response('planned_vs_actual_eq')
            
            items = []
            for name, info in equipment.items():
                items.append({
                    'name': name,
                    'planned': round(info['planned_hours'], 1),
                    'actual': round(info['actual_hours'], 1),
                    'variance': round(info['variance'], 1),
                    'variance_percent': round(info['variance_percent'], 1),
                    'status': info['status']
                })
            
            return {
                'success': True,
                'title': get_text('planned_vs_actual_eq', self.lang),
                'chart_type': 'grouped_bar',
                'data': {
                    'items': items,
                    'labels': [i['name'] for i in items[:10]],
                    'planned_values': [i['planned'] for i in items[:10]],
                    'actual_values': [i['actual'] for i in items[:10]]
                }
            }
        except Exception as e:
            return self._no_data_response('planned_vs_actual_eq')
    
    def get_manhours_by_position(self):
        """Man-hours breakdown by job position."""
        try:
            data = self.resources.get_manhours_analysis()
            
            by_role = data.get('by_role', {})
            if not by_role:
                return self._no_data_response('manhours_by_position')
            
            positions = []
            for name, info in by_role.items():
                positions.append({
                    'name': name,
                    'total_hours': round(info['total_hours'], 1),
                    'headcount': info['total_headcount'],
                    'days_worked': info['days_worked'],
                    'avg_daily': round(info['avg_daily_hours'], 1)
                })
            
            # Sort by hours
            positions.sort(key=lambda x: x['total_hours'], reverse=True)
            
            return {
                'success': True,
                'title': get_text('manhours_by_position', self.lang),
                'chart_type': 'pie_and_bar',
                'data': {
                    'positions': positions,
                    'labels': [p['name'] for p in positions],
                    'values': [p['total_hours'] for p in positions],
                    'total_manhours': round(data.get('total_manhours', 0), 1)
                }
            }
        except Exception as e:
            return self._no_data_response('manhours_by_position')
    
    def get_hr_cost_distribution(self):
        """HR cost distribution by position."""
        try:
            data = self.resources.get_manhours_analysis()
            
            by_role = data.get('by_role', {})
            if not by_role:
                return self._no_data_response('hr_cost_distribution')
            
            positions = []
            total_cost = 0
            for name, info in by_role.items():
                cost = info['total_hours'] * info.get('hourly_rate', 0)
                total_cost += cost
                positions.append({
                    'name': name,
                    'hours': round(info['total_hours'], 1),
                    'rate': info.get('hourly_rate', 0),
                    'cost': round(cost, 0)
                })
            
            # Sort by cost
            positions.sort(key=lambda x: x['cost'], reverse=True)
            
            return {
                'success': True,
                'title': get_text('hr_cost_distribution', self.lang),
                'chart_type': 'donut',
                'data': {
                    'positions': positions,
                    'labels': [p['name'] for p in positions],
                    'values': [p['cost'] for p in positions],
                    'total_cost': round(total_cost, 0)
                }
            }
        except Exception as e:
            return self._no_data_response('hr_cost_distribution')
    
    # =========================================================================
    # MATERIAL ANALYSES
    # =========================================================================
    
    def get_material_consumption(self):
        """Material consumption progress."""
        try:
            data = self.materials.get_material_consumption()
            
            if not data:
                return self._no_data_response('material_consumption')
            
            materials = []
            for name, info in data.items():
                if info['total_received'] > 0 or info['planned_total'] > 0:
                    planned = info.get('planned_total', 0)
                    used = info['total_used']
                    progress = (used / planned * 100) if planned > 0 else 0
                    
                    materials.append({
                        'name': name,
                        'unit': info.get('unit', ''),
                        'received': round(info['total_received'], 2),
                        'used': round(used, 2),
                        'planned': round(planned, 2),
                        'progress': round(min(progress, 100), 1),
                        'daily_avg': round(info['daily_average'], 2)
                    })
            
            # Sort by progress
            materials.sort(key=lambda x: x['progress'], reverse=True)
            
            return {
                'success': True,
                'title': get_text('material_consumption', self.lang),
                'chart_type': 'progress_bars',
                'data': {
                    'materials': materials,
                    'labels': [m['name'] for m in materials[:10]],
                    'values': [m['progress'] for m in materials[:10]]
                }
            }
        except Exception as e:
            return self._no_data_response('material_consumption')
    
    def get_current_inventory(self):
        """Current material inventory levels."""
        try:
            data = self.materials.get_inventory_levels()
            
            if not data:
                return self._no_data_response('current_inventory')
            
            materials = []
            status_translate = {
                'good': 'خوب' if self.lang == 'fa' else 'Good',
                'adequate': 'کافی' if self.lang == 'fa' else 'Adequate',
                'low': 'کم' if self.lang == 'fa' else 'Low',
                'critical': 'بحرانی' if self.lang == 'fa' else 'Critical',
                'no_usage': 'بدون مصرف' if self.lang == 'fa' else 'No Usage'
            }
            
            for name, info in data.items():
                materials.append({
                    'name': name,
                    'unit': info.get('unit', ''),
                    'received': round(info['received'], 2),
                    'used': round(info['used'], 2),
                    'in_stock': round(info['in_stock'], 2),
                    'stock_days': round(info['stock_days'], 1) if info['stock_days'] else None,
                    'status': info['status'],
                    'status_text': status_translate.get(info['status'], info['status'])
                })
            
            # Sort by status (critical first)
            status_order = {'critical': 0, 'low': 1, 'adequate': 2, 'good': 3, 'no_usage': 4}
            materials.sort(key=lambda x: status_order.get(x['status'], 5))
            
            return {
                'success': True,
                'title': get_text('current_inventory', self.lang),
                'chart_type': 'inventory_table',
                'data': {
                    'materials': materials,
                    'critical_count': sum(1 for m in materials if m['status'] == 'critical'),
                    'low_count': sum(1 for m in materials if m['status'] == 'low')
                }
            }
        except Exception as e:
            return self._no_data_response('current_inventory')
    
    def get_material_cost(self):
        """Cost spent on materials."""
        try:
            data = self.materials.get_material_cost_spent()
            
            if data['total_cost'] == 0:
                return self._no_data_response('material_cost')
            
            materials = []
            for name, info in data['by_material'].items():
                materials.append({
                    'name': name,
                    'quantity': round(info['quantity'], 2),
                    'price': info['price_per_unit'],
                    'cost': round(info['cost'], 0)
                })
            
            # Sort by cost
            materials.sort(key=lambda x: x['cost'], reverse=True)
            
            # Format trend dates
            trend = data.get('cost_trend', [])
            for item in trend:
                item['date_display'] = self._format_date(item['date'])
            
            return {
                'success': True,
                'title': get_text('material_cost', self.lang),
                'chart_type': 'cost_breakdown',
                'data': {
                    'materials': materials,
                    'total_cost': round(data['total_cost'], 0),
                    'planned_budget': round(data['planned_budget'], 0),
                    'budget_used_percent': round(data['budget_used_percent'], 1),
                    'remaining': round(data['remaining_budget'], 0),
                    'trend': trend,
                    'labels': [m['name'] for m in materials[:10]],
                    'values': [m['cost'] for m in materials[:10]]
                }
            }
        except Exception as e:
            return self._no_data_response('material_cost')
    
    def get_supply_rate(self):
        """Material supply rate analysis."""
        try:
            data = self.materials.get_supply_rate_analysis()
            
            if not data:
                return self._no_data_response('supply_rate')
            
            materials = []
            for name, info in data.items():
                materials.append({
                    'name': name,
                    'supply_rate': round(info.get('supply_rate', 0), 2),
                    'consistency': round(info.get('consistency', 0), 1),
                    'delivery_count': info.get('delivery_count', 0),
                    'avg_delivery_size': round(info.get('avg_delivery_size', 0), 2)
                })
            
            # Sort by supply rate
            materials.sort(key=lambda x: x['supply_rate'], reverse=True)
            
            return {
                'success': True,
                'title': get_text('supply_rate', self.lang),
                'chart_type': 'supply_analysis',
                'data': {
                    'materials': materials,
                    'labels': [m['name'] for m in materials[:10]],
                    'values': [m['supply_rate'] for m in materials[:10]]
                }
            }
        except Exception as e:
            return self._no_data_response('supply_rate')
    
    def get_at_risk_materials(self):
        """Materials running low vs usage rate."""
        try:
            data = self.materials.get_at_risk_materials()
            
            if not data:
                # No risk - this is good!
                return {
                    'success': True,
                    'title': get_text('at_risk_materials', self.lang),
                    'chart_type': 'risk_list',
                    'data': {
                        'materials': [],
                        'message': 'همه مصالح در وضعیت مناسب هستند' if self.lang == 'fa' else 'All materials are at healthy levels'
                    }
                }
            
            # Translate risk levels
            if self.lang == 'fa':
                risk_map = {'high': 'بالا', 'medium': 'متوسط', 'low': 'کم'}
                rec_map = {
                    'Consider ordering more': 'سفارش بیشتر را در نظر بگیرید',
                    'Stock running low': 'موجودی در حال اتمام',
                    'Critical shortage': 'کمبود بحرانی'
                }
                
                for mat in data:
                    mat['risk_level'] = risk_map.get(mat.get('risk_level', ''), mat.get('risk_level', ''))
                    rec = mat.get('recommendation', '')
                    for eng, fa in rec_map.items():
                        rec = rec.replace(eng, fa)
                    mat['recommendation'] = rec
            
            return {
                'success': True,
                'title': get_text('at_risk_materials', self.lang),
                'chart_type': 'risk_list',
                'data': {
                    'materials': data,
                    'high_risk_count': sum(1 for m in data if m.get('risk_level') in ['high', 'بالا']),
                    'medium_risk_count': sum(1 for m in data if m.get('risk_level') in ['medium', 'متوسط'])
                }
            }
        except Exception as e:
            return self._no_data_response('at_risk_materials')
    
    # =========================================================================
    # SCHEDULE ANALYSES
    # =========================================================================
    
    def get_working_days(self):
        """Working days vs calendar days analysis."""
        try:
            data = self.schedule.get_working_days_analysis()
            
            if data['total_working_days'] == 0:
                return self._no_data_response('working_days')
            
            # Format dates
            first_date = self._format_date(data['first_date'])
            last_date = self._format_date(data['last_date'])
            
            # Translate weekday names
            weekday_data = data.get('by_weekday', {})
            if self.lang == 'fa':
                weekday_map = {
                    'Monday': 'دوشنبه', 'Tuesday': 'سه‌شنبه', 'Wednesday': 'چهارشنبه',
                    'Thursday': 'پنج‌شنبه', 'Friday': 'جمعه', 'Saturday': 'شنبه', 'Sunday': 'یک‌شنبه'
                }
                weekday_data = {weekday_map.get(k, k): v for k, v in weekday_data.items()}
            
            return {
                'success': True,
                'title': get_text('working_days', self.lang),
                'chart_type': 'working_days_analysis',
                'data': {
                    'total_working_days': data['total_working_days'],
                    'calendar_days': data['calendar_days'],
                    'efficiency_rate': round(data['efficiency_rate'], 1),
                    'first_date': first_date,
                    'last_date': last_date,
                    'by_month': data.get('by_month', {}),
                    'by_weekday': weekday_data,
                    'current_streak': data['streak_info'].get('current_streak', 0),
                    'max_streak': data['streak_info'].get('max_streak', 0)
                }
            }
        except Exception as e:
            return self._no_data_response('working_days')
    
    def get_weather_impact(self):
        """Weather impact on work analysis."""
        try:
            data = self.schedule.get_weather_impact()
            
            if data['total_days_analyzed'] == 0:
                return self._no_data_response('weather_impact')
            
            # Format weather data
            weather_list = []
            for weather, info in data.get('productivity_by_weather', {}).items():
                weather_list.append({
                    'weather': weather,
                    'days': info['days'],
                    'total_work': round(info['total_work'], 2),
                    'avg_work': round(info['avg_work_per_day'], 2),
                    'percent': round(info['percent_of_total'], 1)
                })
            
            # Translate work status
            work_status = data.get('work_status_distribution', {})
            if self.lang == 'fa':
                status_map = {
                    'Continued': 'ادامه کار', 'work_continued': 'ادامه کار',
                    'Stopped': 'توقف', 'work_stopped': 'توقف',
                    'slow_progress': 'پیشرفت کند'
                }
                work_status = {status_map.get(k, k): v for k, v in work_status.items()}
            
            return {
                'success': True,
                'title': get_text('weather_impact', self.lang),
                'chart_type': 'weather_analysis',
                'data': {
                    'total_days': data['total_days_analyzed'],
                    'weather_types': weather_list,
                    'work_status': work_status,
                    'lost_days': data['lost_days_weather'],
                    'labels': [w['weather'] for w in weather_list],
                    'values': [w['days'] for w in weather_list]
                }
            }
        except Exception as e:
            return self._no_data_response('weather_impact')
    
    def get_issue_impact(self):
        """Impact of issues on schedule."""
        try:
            data = self.schedule.get_issue_impact()
            
            return {
                'success': True,
                'title': get_text('issue_impact', self.lang),
                'chart_type': 'issue_impact',
                'data': {
                    'total_issues': data['total_issues'],
                    'by_category': data['issues_by_category'],
                    'days_with_issues': data['days_with_issues'],
                    'critical_issues': data['critical_issues'][:5]
                }
            }
        except Exception as e:
            return self._no_data_response('issue_impact')
    
    def get_estimated_completion(self):
        """Estimated project completion date."""
        try:
            data = self.schedule.get_estimated_completion()
            
            # Format dates
            planned_end = self._format_date(data.get('planned_end_date'))
            estimated = self._format_date(data.get('estimated_completion'))
            
            # Translate confidence
            confidence = data.get('confidence', 'low')
            if self.lang == 'fa':
                conf_map = {'high': 'بالا', 'medium': 'متوسط', 'low': 'کم'}
                confidence = conf_map.get(confidence, confidence)
            
            return {
                'success': True,
                'title': get_text('estimated_completion', self.lang),
                'chart_type': 'completion_forecast',
                'data': {
                    'planned_end_date': planned_end,
                    'estimated_completion': estimated,
                    'variance_days': data.get('variance_days', 0),
                    'completion_percent': round(data.get('completion_percent', 0), 1),
                    'days_remaining': data.get('days_remaining', 0),
                    'confidence': confidence,
                    'status': 'on_track' if data.get('variance_days', 0) <= 0 else 'delayed'
                }
            }
        except Exception as e:
            return self._no_data_response('estimated_completion')
    
    def get_schedule_variance(self):
        """Schedule variance (SV) analysis."""
        try:
            data = self.schedule.get_schedule_variance()
            
            # Translate interpretation
            interpretation = data.get('interpretation', '')
            if self.lang == 'fa':
                interp_map = {'ahead': 'جلوتر از برنامه', 'behind': 'عقب‌تر از برنامه', 'on schedule': 'طبق برنامه'}
                interpretation = interp_map.get(interpretation, interpretation)
            
            return {
                'success': True,
                'title': get_text('schedule_variance', self.lang),
                'chart_type': 'variance_gauge',
                'data': {
                    'sv': round(data.get('variance', 0), 1),
                    'spi': round(data.get('spi', 1), 2),
                    'planned_progress': round(data.get('planned_progress', 0), 1),
                    'actual_progress': round(data.get('actual_progress', 0), 1),
                    'variance_percent': round(data.get('variance_percent', 0), 1),
                    'interpretation': interpretation,
                    'status': 'good' if data.get('spi', 1) >= 1 else 'warning'
                }
            }
        except Exception as e:
            return self._no_data_response('schedule_variance')
    
    # =========================================================================
    # SAFETY ANALYSES
    # =========================================================================
    
    def get_incident_rate(self):
        """Incident rate calculation."""
        try:
            data = self.safety.get_incident_rate()
            
            return {
                'success': True,
                'title': get_text('incident_rate', self.lang),
                'chart_type': 'incident_rate',
                'data': {
                    'total_incidents': data['total_incidents'],
                    'total_manhours': round(data['total_manhours'], 0),
                    'incident_rate': round(data['incident_rate'], 2),
                    'trir': data.get('trir', 0),
                    'by_type': data.get('by_type', {}),
                    'formula': 'Incidents per 1000 working days'
                }
            }
        except Exception as e:
            return self._no_data_response('incident_rate')
    
    def get_inspection_compliance(self):
        """Safety inspection compliance rate."""
        try:
            data = self.safety.get_inspection_compliance()
            
            return {
                'success': True,
                'title': get_text('inspection_compliance', self.lang),
                'chart_type': 'compliance_gauge',
                'data': {
                    'total_days': data['total_days'],
                    'total_inspections': data['total_inspections'],
                    'inspection_rate': round(data['inspection_rate'], 1),
                    'compliance_rate': round(data['compliance_rate'], 1),
                    'no_incidents': data['no_incidents'],
                    'incidents': data['incidents'],
                    'status': 'good' if data['compliance_rate'] >= 90 else ('warning' if data['compliance_rate'] >= 70 else 'critical')
                }
            }
        except Exception as e:
            return self._no_data_response('inspection_compliance')
    
    def get_near_miss(self):
        """Near-miss event tracking."""
        try:
            data = self.safety.get_near_miss_tracking()
            
            return {
                'success': True,
                'title': get_text('near_miss', self.lang),
                'chart_type': 'near_miss_tracking',
                'data': {
                    'total_near_misses': data.get('total_near_misses', 0),
                    'by_month': data.get('by_month', {}),
                    'trend': data.get('trend', []),
                    'recent': data.get('recent', [])[:5],
                    'rate_per_day': round(data.get('rate_per_day', 0), 4)
                }
            }
        except Exception as e:
            return self._no_data_response('near_miss')
    
    def get_safety_trend(self):
        """Safety trend over time."""
        try:
            data = self.safety.get_safety_trend()
            
            monthly_data = data.get('monthly_data', [])
            
            # Format months
            for item in monthly_data:
                if self.lang == 'fa':
                    try:
                        parts = item['month'].split('-')
                        jdate = jdatetime.date(int(parts[0]), int(parts[1]), 1)
                        item['month_display'] = jdate.strftime('%B %Y')
                    except:
                        item['month_display'] = item['month']
                else:
                    item['month_display'] = item['month']
            
            return {
                'success': True,
                'title': get_text('safety_trend', self.lang),
                'chart_type': 'safety_trend_chart',
                'data': {
                    'monthly_data': monthly_data,
                    'labels': [m['month_display'] for m in monthly_data],
                    'safe_rates': [m['safe_rate'] for m in monthly_data],
                    'incident_counts': [m.get('incidents', 0) for m in monthly_data],
                    'trend_direction': data.get('trend_direction', 'stable')
                }
            }
        except Exception as e:
            return self._no_data_response('safety_trend')
    
    def get_days_without_incident(self):
        """Days without incident tracking."""
        try:
            data = self.safety.get_days_without_incident()
            
            # Format last incident date
            last_incident = self._format_date(data.get('last_incident_date')) if data.get('last_incident_date') else None
            
            return {
                'success': True,
                'title': get_text('days_without_incident', self.lang),
                'chart_type': 'streak_counter',
                'data': {
                    'current_streak': data['current_streak'],
                    'max_streak': data.get('max_streak', 0),
                    'last_incident_date': last_incident,
                    'status': 'excellent' if data['current_streak'] >= 30 else ('good' if data['current_streak'] >= 14 else 'monitor')
                }
            }
        except Exception as e:
            return self._no_data_response('days_without_incident')
    
    # =========================================================================
    # ISSUE ANALYSES
    # =========================================================================
    
    def get_issues_by_category(self):
        """Issues grouped by category."""
        try:
            data = self.issues.get_issues_by_category()
            
            categories = data.get('by_category', {})
            if not categories:
                return self._no_data_response('issues_by_category')
            
            category_list = [
                {'name': name, 'count': count}
                for name, count in categories.items()
            ]
            category_list.sort(key=lambda x: x['count'], reverse=True)
            
            return {
                'success': True,
                'title': get_text('issues_by_category', self.lang),
                'chart_type': 'pie',
                'data': {
                    'categories': category_list,
                    'total_issues': data.get('total_issues', 0),
                    'labels': [c['name'] for c in category_list],
                    'values': [c['count'] for c in category_list]
                }
            }
        except Exception as e:
            return self._no_data_response('issues_by_category')
    
    def get_issue_frequency(self):
        """Issue frequency trend over time."""
        try:
            data = self.issues.get_issue_frequency_trend()
            
            monthly = data.get('monthly_trend', [])
            
            # Format months
            for item in monthly:
                if self.lang == 'fa':
                    try:
                        parts = item['month'].split('-')
                        jdate = jdatetime.date(int(parts[0]), int(parts[1]), 1)
                        item['month_display'] = jdate.strftime('%B')
                    except:
                        item['month_display'] = item['month']
                else:
                    item['month_display'] = item['month']
            
            # Translate trend
            trend = data.get('trend_direction', 'stable')
            if self.lang == 'fa':
                trend_map = {'increasing': 'در حال افزایش', 'decreasing': 'در حال کاهش', 'stable': 'پایدار'}
                trend = trend_map.get(trend, trend)
            
            return {
                'success': True,
                'title': get_text('issue_frequency', self.lang),
                'chart_type': 'trend_line',
                'data': {
                    'monthly_trend': monthly,
                    'labels': [m['month_display'] for m in monthly],
                    'values': [m['count'] for m in monthly],
                    'trend_direction': trend,
                    'daily_average': round(data.get('daily_average', 0), 2),
                    'total_issues': data.get('total_issues', 0)
                }
            }
        except Exception as e:
            return self._no_data_response('issue_frequency')
    
    def get_problem_locations(self):
        """Most problematic locations."""
        try:
            data = self.issues.get_issue_locations()
            
            hotspots = data.get('hotspots', [])
            if not hotspots:
                return self._no_data_response('problem_locations')
            
            return {
                'success': True,
                'title': get_text('problem_locations', self.lang),
                'chart_type': 'location_map',
                'data': {
                    'locations': hotspots[:10],
                    'labels': [h['category'] for h in hotspots[:10]],
                    'values': [h['total_issues'] for h in hotspots[:10]],
                    'total_categories': data.get('total_categories', 0)
                }
            }
        except Exception as e:
            return self._no_data_response('problem_locations')
    
    def get_issue_duration(self):
        """Issue duration analysis."""
        try:
            data = self.issues.get_issue_duration()
            
            if data.get('total_issues', 0) == 0:
                return self._no_data_response('issue_duration')
            
            return {
                'success': True,
                'title': get_text('issue_duration', self.lang),
                'chart_type': 'duration_analysis',
                'data': {
                    'total_issues': data.get('total_issues', 0),
                    'resolved_issues': data.get('resolved_issues', 0),
                    'pending_issues': data.get('pending_issues', 0),
                    'resolution_rate': round(data.get('resolution_rate', 0), 1),
                    'by_category': data.get('by_category', {})
                }
            }
        except Exception as e:
            return self._no_data_response('issue_duration')
    
    # =========================================================================
    # KPI ANALYSES
    # =========================================================================
    
    def get_health_score(self):
        """Overall project health score."""
        try:
            data = self.kpi.get_project_health_score()
            
            return {
                'success': True,
                'title': get_text('health_score', self.lang),
                'chart_type': 'health_gauge',
                'data': {
                    'overall_score': round(data['overall_score'], 1),
                    'grade': data['grade'],
                    'components': data.get('components', {}),
                    'recommendations': data.get('recommendations', [])
                }
            }
        except Exception as e:
            return self._no_data_response('health_score')
    
    def get_cpi_analysis(self):
        """Cost Performance Index detailed analysis."""
        try:
            data = self.kpi.get_cpi_spi_metrics()
            performance = data.get('current', {})
            evm_details = data.get('evm_details', {})
            
            cpi = performance.get('cpi', 1)
            interpretation = 'under_budget' if cpi > 1 else ('over_budget' if cpi < 1 else 'on_budget')
            
            if self.lang == 'fa':
                interp_map = {'under_budget': 'زیر بودجه', 'over_budget': 'بالاتر از بودجه', 'on_budget': 'طبق بودجه'}
                interpretation = interp_map.get(interpretation, interpretation)
            
            return {
                'success': True,
                'title': get_text('cpi_analysis', self.lang),
                'chart_type': 'performance_index',
                'data': {
                    'cpi': round(cpi, 2),
                    'ev': round(evm_details.get('EV', 0), 0),
                    'ac': round(evm_details.get('AC', 0), 0),
                    'interpretation': interpretation,
                    'formula': 'CPI = EV / AC',
                    'status': 'good' if cpi >= 1 else 'warning'
                }
            }
        except Exception as e:
            return self._no_data_response('cpi_analysis')
    
    def get_spi_analysis(self):
        """Schedule Performance Index detailed analysis."""
        try:
            data = self.kpi.get_cpi_spi_metrics()
            performance = data.get('current', {})
            evm_details = data.get('evm_details', {})
            
            spi = performance.get('spi', 1)
            interpretation = 'ahead' if spi > 1 else ('behind' if spi < 1 else 'on_schedule')
            
            if self.lang == 'fa':
                interp_map = {'ahead': 'جلوتر از برنامه', 'behind': 'عقب‌تر از برنامه', 'on_schedule': 'طبق برنامه'}
                interpretation = interp_map.get(interpretation, interpretation)
            
            return {
                'success': True,
                'title': get_text('spi_analysis', self.lang),
                'chart_type': 'performance_index',
                'data': {
                    'spi': round(spi, 2),
                    'ev': round(evm_details.get('EV', 0), 0),
                    'pv': round(evm_details.get('PV', 0), 0),
                    'interpretation': interpretation,
                    'formula': 'SPI = EV / PV',
                    'status': 'good' if spi >= 1 else 'warning'
                }
            }
        except Exception as e:
            return self._no_data_response('spi_analysis')
    
    def get_burn_rate(self):
        """Budget burn rate analysis."""
        try:
            data = self.kpi.get_burn_rate()
            
            return {
                'success': True,
                'title': get_text('burn_rate', self.lang),
                'chart_type': 'burn_rate_chart',
                'data': {
                    'daily_burn': round(data.get('daily_burn', 0), 0),
                    'weekly_burn': round(data.get('weekly_burn', 0), 0),
                    'monthly_burn': round(data.get('monthly_burn', 0), 0),
                    'total_spent': round(data.get('total_spent', 0), 0),
                    'total_budget': round(data.get('total_budget', 0), 0),
                    'percent_burned': round(data.get('percent_burned', 0), 1),
                    'remaining': round(data.get('remaining', 0), 0),
                    'status': data.get('status', 'on_budget')
                }
            }
        except Exception as e:
            return self._no_data_response('burn_rate')
    
    def get_days_to_completion(self):
        """Estimated days to project completion."""
        try:
            completion = self.kpi.get_days_to_completion()
            
            # Format date
            estimated_date = self._format_date(completion.get('estimated_date'))
            
            # Translate confidence
            confidence = completion.get('confidence', 'low')
            if self.lang == 'fa':
                conf_map = {'high': 'بالا', 'medium_high': 'متوسط رو به بالا', 'medium': 'متوسط', 'low': 'کم'}
                confidence = conf_map.get(confidence, confidence)
            
            return {
                'success': True,
                'title': get_text('days_to_completion', self.lang),
                'chart_type': 'countdown',
                'data': {
                    'days_remaining': completion.get('estimated_days', 0),
                    'estimated_date': estimated_date,
                    'confidence': confidence,
                    'progress_percent': round(completion.get('current_progress', 0), 1),
                    'scenarios': completion.get('scenarios', {}),
                    'velocity_info': completion.get('velocity_info', {})
                }
            }
        except Exception as e:
            return self._no_data_response('days_to_completion')
    
    # =========================================================================
    # COMPARATIVE ANALYSES
    # =========================================================================
    
    def get_month_over_month(self):
        """This month vs last month comparison."""
        try:
            data = self.comparative.get_month_over_month(2)
            
            months = data.get('months', [])
            if len(months) < 2:
                return self._no_data_response('month_over_month')
            
            current = months[0] if months else {}
            previous = months[1] if len(months) > 1 else {}
            changes = data.get('month_over_month_change', {})
            
            return {
                'success': True,
                'title': get_text('month_over_month', self.lang),
                'chart_type': 'comparison_table',
                'data': {
                    'current_month': current,
                    'previous_month': previous,
                    'changes': changes,
                    'metrics': ['work_output', 'manhours', 'productivity', 'issues']
                }
            }
        except Exception as e:
            return self._no_data_response('month_over_month')
    
    def get_actual_vs_planned(self):
        """Actual vs planned across all metrics."""
        try:
            # Collect comparisons across modules
            progress = self.physical_progress.get_overall_progress()
            budget = self.financial.get_budget_vs_actual()
            resources = self.resources.get_planned_vs_actual_resources()
            
            metrics = []
            
            # Progress
            metrics.append({
                'name': 'پیشرفت فیزیکی' if self.lang == 'fa' else 'Physical Progress',
                'planned': 100,
                'actual': round(progress['weighted_progress'], 1),
                'unit': '%'
            })
            
            # Budget
            metrics.append({
                'name': 'بودجه' if self.lang == 'fa' else 'Budget',
                'planned': budget['budget']['total'],
                'actual': budget['actual']['total'],
                'unit': ''
            })
            
            return {
                'success': True,
                'title': get_text('actual_vs_planned', self.lang),
                'chart_type': 'variance_table',
                'data': {
                    'metrics': metrics,
                    'equipment': resources.get('equipment', {}),
                    'hr': resources.get('human_resources', {})
                }
            }
        except Exception as e:
            return self._no_data_response('actual_vs_planned')
    
    def get_weekly_report(self):
        """Weekly progress report."""
        try:
            data = self.comparative.get_weekly_report(4)
            
            weeks = data.get('weeks', [])
            
            # Format week labels
            for week in weeks:
                if self.lang == 'fa':
                    if 'week_start' in week:
                        week['week_start'] = to_jalali(week['week_start'])
                    if 'week_end' in week:
                        week['week_end'] = to_jalali(week['week_end'])
                    if 'week_label' in week:
                        week['week_label'] = week['week_label'].replace('Week of', 'هفته')
            
            return {
                'success': True,
                'title': get_text('weekly_report', self.lang),
                'chart_type': 'weekly_comparison',
                'data': {
                    'weeks': weeks,
                    'highlights': data.get('highlights', []),
                    'labels': [w.get('week_label', '') for w in weeks],
                    'work_output': [w.get('work_output', 0) for w in weeks],
                    'manhours': [w.get('manhours', 0) for w in weeks]
                }
            }
        except Exception as e:
            return self._no_data_response('weekly_report')
