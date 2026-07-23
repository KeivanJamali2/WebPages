"""
=============================================================================
Analysis Engine - Combined Analysis Module
=============================================================================

This module combines all analysis modules and provides:
- Unified interface for all analyses
- Data aggregation for dashboards
- Plot data generation
- Report generation
"""

from datetime import datetime
from collections import defaultdict
import jdatetime

# Import all analysis modules
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


# Bilingual text support
TRANSLATIONS = {
    'en': {
        'progress_declining': 'Progress velocity is declining - investigate causes',
        'cost_below_target': 'Cost performance is below target - review spending',
        'schedule_behind': 'Schedule performance is behind - consider acceleration',
        'safety_attention': 'Safety compliance needs attention',
        'work_output_up': 'Work output increased compared to last week',
        'work_output_down': 'Work output decreased compared to last week',
        'productivity_up': 'Productivity has improved',
        'productivity_down': 'Productivity has declined',
        'issues_up': 'More issues reported this week',
        'issues_down': 'Fewer issues reported this week',
        'no_issues': 'No issues detected',
        'on_track': 'On Track',
        'days_late': 'days late',
        'ahead_schedule': 'ahead of schedule',
        'behind_schedule': 'behind schedule',
        'on_schedule': 'on schedule',
        'under_budget': 'under budget',
        'over_budget': 'over budget',
        'on_budget': 'on budget',
        'good': 'Good',
        'attention': 'Needs Attention',
        'critical': 'Critical',
        'increasing': 'increasing',
        'decreasing': 'decreasing',
        'stable': 'stable',
    },
    'fa': {
        'progress_declining': 'سرعت پیشرفت در حال کاهش است - علل را بررسی کنید',
        'cost_below_target': 'عملکرد هزینه زیر هدف است - هزینه‌ها را بررسی کنید',
        'schedule_behind': 'عملکرد زمان‌بندی عقب است - شتاب‌دهی را در نظر بگیرید',
        'safety_attention': 'انطباق ایمنی نیاز به توجه دارد',
        'work_output_up': 'خروجی کار نسبت به هفته گذشته افزایش یافت',
        'work_output_down': 'خروجی کار نسبت به هفته گذشته کاهش یافت',
        'productivity_up': 'بهره‌وری بهبود یافته است',
        'productivity_down': 'بهره‌وری کاهش یافته است',
        'issues_up': 'مشکلات بیشتری این هفته گزارش شده',
        'issues_down': 'مشکلات کمتری این هفته گزارش شده',
        'no_issues': 'مشکلی شناسایی نشد',
        'on_track': 'در مسیر',
        'days_late': 'روز تأخیر',
        'ahead_schedule': 'جلوتر از برنامه',
        'behind_schedule': 'عقب‌تر از برنامه',
        'on_schedule': 'طبق برنامه',
        'under_budget': 'زیر بودجه',
        'over_budget': 'بالاتر از بودجه',
        'on_budget': 'طبق بودجه',
        'good': 'خوب',
        'attention': 'نیاز به توجه',
        'critical': 'بحرانی',
        'increasing': 'در حال افزایش',
        'decreasing': 'در حال کاهش',
        'stable': 'پایدار',
    }
}


def get_text(key, lang='en'):
    """Get translated text."""
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)


class AnalysisEngine:
    """
    Unified analysis engine that combines all analysis modules.
    
    Usage:
        engine = AnalysisEngine(db, project_id, project_config, lang='fa')
        
        # Get all analyses
        full_report = engine.get_full_report()
        
        # Get specific analysis
        progress = engine.physical_progress.get_overall_progress()
        
        # Get dashboard data
        dashboard = engine.get_boss_dashboard()
    """
    
    def __init__(self, db, project_id, project_config=None, lang='en'):
        """
        Initialize the analysis engine.
        
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
        
        # Initialize all analysis modules
        self.physical_progress = PhysicalProgressAnalysis(db, project_id, project_config)
        self.financial = FinancialAnalysis(db, project_id, project_config)
        self.resources = ResourceAnalysis(db, project_id, project_config)
        self.materials = MaterialAnalysis(db, project_id, project_config)
        self.schedule = ScheduleAnalysis(db, project_id, project_config)
        self.safety = SafetyAnalysis(db, project_id, project_config)
        self.issues = IssueAnalysis(db, project_id, project_config)
        self.kpi = KPIAnalysis(db, project_id, project_config, lang)
        self.comparative = ComparativeAnalysis(db, project_id, project_config, lang)
    
    def get_full_report(self):
        """
        Generate a complete analysis report.
        
        Returns:
            dict: Complete analysis report with all modules
        """
        return {
            'generated_at': datetime.now().isoformat(),
            'project_id': self.project_id,
            'physical_progress': self.physical_progress.get_summary(),
            'financial': self.financial.get_summary(),
            'resources': self.resources.get_summary(),
            'materials': self.materials.get_summary(),
            'schedule': self.schedule.get_summary(),
            'safety': self.safety.get_summary(),
            'issues': self.issues.get_summary(),
            'kpi': self.kpi.get_summary(),
            'comparative': self.comparative.get_summary()
        }
    
    def get_boss_dashboard(self):
        """
        Get data specifically for the boss dashboard.
        
        Returns:
            dict: {
                'overview': Executive summary data,
                'summary': Aggregated metrics,
                'details': Detailed data for plots
            }
        """
        # Get KPI data for overview
        kpi_summary = self.kpi.get_summary()
        health_score = kpi_summary['health_score']
        performance = kpi_summary['performance_indices']
        burn_rate = kpi_summary['burn_rate']
        completion = kpi_summary['completion']
        
        # Get progress data
        progress = self.physical_progress.get_overall_progress()
        velocity = self.physical_progress.get_progress_velocity()
        
        # Get financial summary
        budget_actual = self.financial.get_budget_vs_actual()
        evm = self.financial.get_evm_analysis()
        
        # Get schedule data
        schedule_variance = self.schedule.get_schedule_variance()
        estimated_completion = self.schedule.get_estimated_completion()
        
        # Get safety data
        safety_summary = self.safety.get_summary()
        days_without_incident = safety_summary['days_without_incident']
        
        # Get issues summary
        issues_summary = self.issues.get_summary()
        
        # Get comparative data
        weekly_report = self.comparative.get_weekly_report(4)
        mom_comparison = self.comparative.get_month_over_month(3)
        
        # =====================================================================
        # OVERVIEW - Executive summary for presenting to project owners
        # =====================================================================
        overview = {
            'health_score': health_score,
            'key_metrics': {
                'progress_percent': round(progress['weighted_progress'], 1),
                'budget_spent_percent': round(burn_rate['percent_burned'], 1),
                'schedule_status': schedule_variance['interpretation'],
                'cpi': performance['current']['cpi'],
                'spi': performance['current']['spi'],
                'days_safe': days_without_incident['current_streak']
            },
            'status_summary': {
                'overall': health_score['grade'],
                'cost': 'good' if performance['current']['cpi'] >= 1 else 'attention',
                'schedule': 'good' if performance['current']['spi'] >= 1 else 'attention',
                'safety': 'good' if days_without_incident['current_streak'] > 7 else 'monitor'
            },
            'recommendations': health_score['recommendations'],
            'completion': {
                'estimated_date': to_jalali(completion['estimated_date']) if self.lang == 'fa' else completion['estimated_date'],
                'planned_date': to_jalali(estimated_completion['planned_end_date']) if self.lang == 'fa' else estimated_completion['planned_end_date'],
                'variance_days': estimated_completion['variance_days'],
                'confidence': completion['confidence']
            }
        }
        
        # =====================================================================
        # SUMMARY - Aggregated metrics and trends
        # =====================================================================
        summary = {
            'progress': {
                'overall': progress,
                'velocity': velocity,
                'by_activity_count': {
                    'total': progress['activities_count'],
                    'completed': progress['activities_completed'],
                    'in_progress': progress['activities_count'] - progress['activities_completed']
                }
            },
            'financial': {
                'budget_overview': {
                    'total_budget': budget_actual['budget']['total'],
                    'spent': budget_actual['actual']['total'],
                    'remaining': budget_actual['burn_rate']['remaining'],
                    'burn_rate_percent': burn_rate['percent_burned']
                },
                'evm_summary': {
                    'cpi': evm['CPI'],
                    'spi': schedule_variance['spi'],
                    'eac': evm['EAC'],
                    'interpretation': evm['interpretation']
                }
            },
            'schedule': {
                'variance': schedule_variance,
                'estimated_completion': estimated_completion,
                'working_days': self.schedule.get_working_days_analysis()
            },
            'safety': {
                'incident_rate': safety_summary['incident_rate'],
                'compliance': safety_summary['inspection_compliance'],
                'streak': days_without_incident
            },
            'issues': {
                'total': issues_summary['by_category']['total_issues'],
                'by_category': issues_summary['by_category']['by_category'],
                'trend': issues_summary['frequency_trend']['trend_direction'],
                'resolution_rate': issues_summary['duration']['resolution_rate']
            },
            'weekly_highlights': weekly_report['highlights'],
            'month_over_month_change': mom_comparison['month_over_month_change']
        }
        
        # =====================================================================
        # DETAILS - Detailed data for charts and plots
        # =====================================================================
        progress_trend = self.physical_progress.get_progress_trend(30, 'daily')
        
        # Convert dates to Jalali if Persian language
        if self.lang == 'fa':
            for item in progress_trend:
                if 'date' in item:
                    item['date_display'] = to_jalali(item['date'])
        
        details = {
            'progress_trend': progress_trend,
            'progress_by_activity': self.physical_progress.get_progress_by_activity(),
            'roadmap_coverage': self.physical_progress.get_roadmap_coverage(),
            'financial_trend': self._get_financial_trend_data(),
            'cost_breakdown': self._get_cost_breakdown_data(),
            'resource_utilization': self.resources.get_equipment_utilization(),
            'manhours_trend': self.resources.get_manhours_analysis()['trend'],
            'material_inventory': self.materials.get_inventory_levels(),
            'material_consumption': self.materials.get_material_consumption(),
            'at_risk_materials': self._localize_at_risk_materials(self.materials.get_at_risk_materials()),
            'weather_impact': self.schedule.get_weather_impact(),
            'safety_trend': safety_summary['trend']['monthly_data'],
            'issue_frequency': issues_summary['frequency_trend']['monthly_trend'],
            'weekly_data': self._localize_weekly_data(weekly_report['weeks']),
            'monthly_comparison': mom_comparison['months']
        }
        
        return {
            'overview': overview,
            'summary': summary,
            'details': details
        }
    
    def _get_financial_trend_data(self):
        """Get financial trend data for plotting."""
        from models.daily_form import DailyFormSubmission
        
        # Get all form dates
        forms = self.db.session.query(
            DailyFormSubmission.form_date
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).order_by(
            DailyFormSubmission.form_date
        ).all()
        
        trend = []
        cumulative = 0
        
        for form in forms:
            cost = self.financial.get_daily_cost_breakdown(form.form_date)
            daily_total = cost['total_cost']
            cumulative += daily_total
            
            trend.append({
                'date': form.form_date.isoformat(),
                'daily_cost': daily_total,
                'cumulative_cost': cumulative,
                'labor': cost['labor_cost'],
                'equipment': cost['equipment_cost'],
                'material': cost['material_cost'],
                'activity': cost['activity_cost']
            })
        
        return trend
    
    def _get_cost_breakdown_data(self):
        """Get cost breakdown data for pie charts."""
        budget_actual = self.financial.get_budget_vs_actual()
        
        if self.lang == 'fa':
            return {
                'by_category': [
                    {'name': 'نیروی کار', 'value': budget_actual['actual']['labor']},
                    {'name': 'تجهیزات', 'value': budget_actual['actual']['equipment']},
                    {'name': 'مواد', 'value': budget_actual['actual']['material']},
                    {'name': 'فعالیت‌ها', 'value': budget_actual['actual']['activity']}
                ],
                'budget_vs_actual': [
                    {'name': 'بودجه', 'value': budget_actual['budget']['total']},
                    {'name': 'واقعی', 'value': budget_actual['actual']['total']}
                ]
            }
        
        return {
            'by_category': [
                {'name': 'Labor', 'value': budget_actual['actual']['labor']},
                {'name': 'Equipment', 'value': budget_actual['actual']['equipment']},
                {'name': 'Materials', 'value': budget_actual['actual']['material']},
                {'name': 'Activities', 'value': budget_actual['actual']['activity']}
            ],
            'budget_vs_actual': [
                {'name': 'Budget', 'value': budget_actual['budget']['total']},
                {'name': 'Actual', 'value': budget_actual['actual']['total']}
            ]
        }
    
    def _localize_weekly_data(self, weeks):
        """Localize weekly data dates to Jalali if Persian."""
        if self.lang != 'fa':
            return weeks
        
        for week in weeks:
            if 'week_start' in week:
                week['week_start'] = to_jalali(week['week_start'])
            if 'week_end' in week:
                week['week_end'] = to_jalali(week['week_end'])
            if 'week_label' in week:
                # Translate week label
                week['week_label'] = week['week_label'].replace('Week of', 'هفته')
        
        return weeks
    
    def _localize_at_risk_materials(self, materials):
        """Localize at-risk materials messages to Persian if needed."""
        if self.lang != 'fa' or not materials:
            return materials
        
        translations = {
            'high': 'بالا',
            'medium': 'متوسط',
            'low': 'کم',
            'Consider ordering more': 'سفارش بیشتر را در نظر بگیرید',
            'Stock running low': 'موجودی در حال اتمام',
            'Critical shortage': 'کمبود بحرانی',
        }
        
        for mat in materials:
            if 'risk_level' in mat:
                mat['risk_level'] = translations.get(mat['risk_level'], mat['risk_level'])
            if 'recommendation' in mat:
                for eng, fa in translations.items():
                    mat['recommendation'] = mat['recommendation'].replace(eng, fa)
        
        return materials
    
    def get_plot_data(self, plot_type):
        """
        Get data formatted for specific plot types.
        
        Args:
            plot_type: Type of plot ('progress_trend', 'cost_breakdown', etc.)
            
        Returns:
            dict: Data formatted for the specific plot
        """
        plot_generators = {
            'progress_trend': self._plot_progress_trend,
            'progress_by_activity': self._plot_progress_by_activity,
            'cost_breakdown': self._plot_cost_breakdown,
            'budget_vs_actual': self._plot_budget_vs_actual,
            'resource_utilization': self._plot_resource_utilization,
            'safety_trend': self._plot_safety_trend,
            'issue_distribution': self._plot_issue_distribution,
            'weekly_performance': self._plot_weekly_performance,
            'evm_chart': self._plot_evm_chart
        }
        
        generator = plot_generators.get(plot_type)
        if generator:
            return generator()
        else:
            return {'error': f'Unknown plot type: {plot_type}'}
    
    def _plot_progress_trend(self):
        """Generate progress trend plot data."""
        trend = self.physical_progress.get_progress_trend(30, 'daily')
        return {
            'type': 'line',
            'title': 'Progress Trend',
            'data': {
                'labels': [t['date_display'] for t in trend],
                'datasets': [{
                    'label': 'Cumulative Progress (%)',
                    'data': [t['cumulative_progress'] for t in trend]
                }]
            }
        }
    
    def _plot_progress_by_activity(self):
        """Generate progress by activity plot data."""
        progress = self.physical_progress.get_progress_by_activity()
        return {
            'type': 'bar',
            'title': 'Progress by Activity',
            'data': {
                'labels': list(progress.keys()),
                'datasets': [{
                    'label': 'Progress %',
                    'data': [p['progress_percent'] for p in progress.values()]
                }]
            }
        }
    
    def _plot_cost_breakdown(self):
        """Generate cost breakdown pie chart data."""
        budget = self.financial.get_budget_vs_actual()
        return {
            'type': 'pie',
            'title': 'Cost Distribution',
            'data': {
                'labels': ['Labor', 'Equipment', 'Materials', 'Activities'],
                'datasets': [{
                    'data': [
                        budget['actual']['labor'],
                        budget['actual']['equipment'],
                        budget['actual']['material'],
                        budget['actual']['activity']
                    ]
                }]
            }
        }
    
    def _plot_budget_vs_actual(self):
        """Generate budget vs actual comparison."""
        budget = self.financial.get_budget_vs_actual()
        return {
            'type': 'bar',
            'title': 'Budget vs Actual',
            'data': {
                'labels': ['Total Budget'],
                'datasets': [
                    {'label': 'Budget', 'data': [budget['budget']['total']]},
                    {'label': 'Actual', 'data': [budget['actual']['total']]}
                ]
            }
        }
    
    def _plot_resource_utilization(self):
        """Generate resource utilization chart."""
        utilization = self.resources.get_equipment_utilization()
        return {
            'type': 'bar',
            'title': 'Equipment Utilization',
            'data': {
                'labels': list(utilization.keys()),
                'datasets': [{
                    'label': 'Utilization %',
                    'data': [u['utilization_rate'] for u in utilization.values()]
                }]
            }
        }
    
    def _plot_safety_trend(self):
        """Generate safety trend chart."""
        trend = self.safety.get_safety_trend()
        return {
            'type': 'line',
            'title': 'Safety Compliance Trend',
            'data': {
                'labels': [t['month'] for t in trend['monthly_data']],
                'datasets': [{
                    'label': 'Safe Rate %',
                    'data': [t['safe_rate'] for t in trend['monthly_data']]
                }]
            }
        }
    
    def _plot_issue_distribution(self):
        """Generate issue distribution chart."""
        issues = self.issues.get_issues_by_category()
        return {
            'type': 'pie',
            'title': 'Issues by Category',
            'data': {
                'labels': list(issues['by_category'].keys()),
                'datasets': [{
                    'data': list(issues['by_category'].values())
                }]
            }
        }
    
    def _plot_weekly_performance(self):
        """Generate weekly performance chart."""
        weekly = self.comparative.get_weekly_report(4)
        return {
            'type': 'bar',
            'title': 'Weekly Performance',
            'data': {
                'labels': [w['week_label'] for w in weekly['weeks']],
                'datasets': [
                    {'label': 'Work Output', 'data': [w['work_output'] for w in weekly['weeks']]},
                    {'label': 'Man-hours', 'data': [w['manhours'] for w in weekly['weeks']]}
                ]
            }
        }
    
    def _plot_evm_chart(self):
        """Generate EVM chart."""
        evm = self.financial.get_evm_analysis()
        return {
            'type': 'bar',
            'title': 'Earned Value Analysis',
            'data': {
                'labels': ['PV', 'EV', 'AC'],
                'datasets': [{
                    'label': 'Value',
                    'data': [evm['PV'], evm['EV'], evm['AC']]
                }]
            },
            'indicators': {
                'CPI': evm['CPI'],
                'SPI': evm['SPI'],
                'interpretation': evm['interpretation']
            }
        }
    
    def check_data_availability(self):
        """
        Check what data is available for analysis.
        
        Returns:
            dict: Data availability status for each module
        """
        from models.daily_form import DailyFormSubmission
        
        # Check for forms
        form_count = self.db.session.query(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).count()
        
        return {
            'has_data': form_count > 0,
            'form_count': form_count,
            'modules': {
                'physical_progress': form_count > 0,
                'financial': form_count > 0,
                'resources': form_count > 0,
                'materials': form_count > 0,
                'schedule': form_count > 0,
                'safety': form_count > 0,
                'issues': form_count > 0,
                'kpi': form_count > 0,
                'comparative': form_count > 1  # Need multiple forms for comparison
            },
            'message': 'Ready for analysis' if form_count > 0 else 'No daily forms submitted yet. Add data to see analysis.'
        }
