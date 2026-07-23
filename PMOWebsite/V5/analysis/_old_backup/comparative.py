"""
=============================================================================
Comparative Analysis Module
=============================================================================

Provides comparative analysis including:
- Month over month comparison
- Project vs project comparison
- Actual vs planned comparison
- Weekly performance reports
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_
from collections import defaultdict
import calendar


# Bilingual highlights
COMPARATIVE_TRANSLATIONS = {
    'en': {
        'work_output_up': 'Work output increased compared to last week',
        'work_output_down': 'Work output decreased compared to last week',
        'productivity_up': 'Productivity has improved',
        'productivity_down': 'Productivity has declined',
        'issues_up': 'More issues reported this week',
        'issues_down': 'Fewer issues reported this week',
    },
    'fa': {
        'work_output_up': 'خروجی کار نسبت به هفته گذشته افزایش یافت',
        'work_output_down': 'خروجی کار نسبت به هفته گذشته کاهش یافت',
        'productivity_up': 'بهره‌وری بهبود یافته است',
        'productivity_down': 'بهره‌وری کاهش یافته است',
        'issues_up': 'مشکلات بیشتری این هفته گزارش شده',
        'issues_down': 'مشکلات کمتری این هفته گزارش شده',
    }
}


class ComparativeAnalysis:
    """Provide comparative analysis across time periods and projects."""
    
    def __init__(self, db, project_id, project_config=None, lang='en'):
        """
        Initialize the analysis.
        
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
    
    def get_month_over_month(self, num_months=6):
        """
        Compare metrics across months.
        
        Args:
            num_months: Number of months to compare
            
        Returns:
            dict: {
                'months': list of month data,
                'metrics': dict of metric comparisons,
                'trends': dict
            }
        """
        from models.daily_form import DailyFormSubmission, ConstructionOperation, HumanResource, ToolEquipment
        
        # Get monthly data
        months_data = []
        now = datetime.now()
        
        for i in range(num_months - 1, -1, -1):
            target_date = now - timedelta(days=30 * i)
            year = target_date.year
            month = target_date.month
            
            first_day = datetime(year, month, 1).date()
            last_day = datetime(year, month, calendar.monthrange(year, month)[1]).date()
            
            # Get forms for this month
            forms = self.db.session.query(DailyFormSubmission).filter(
                DailyFormSubmission.project_id == self.project_id,
                DailyFormSubmission.status == 'approved',
                DailyFormSubmission.form_date >= first_day,
                DailyFormSubmission.form_date <= last_day
            ).all()
            
            # Calculate metrics
            form_ids = [f.id for f in forms]
            
            if form_ids:
                # Work output
                work_output = self.db.session.query(
                    func.sum(ConstructionOperation.amount)
                ).filter(
                    ConstructionOperation.daily_form_id.in_(form_ids)
                ).scalar() or 0
                
                # Man-hours
                manhours = self.db.session.query(
                    func.sum(HumanResource.working_hours * HumanResource.count)
                ).filter(
                    HumanResource.daily_form_id.in_(form_ids)
                ).scalar() or 0
                
                # Equipment hours
                equipment_hours = self.db.session.query(
                    func.sum(ToolEquipment.working_hours * ToolEquipment.count_active)
                ).filter(
                    ToolEquipment.daily_form_id.in_(form_ids)
                ).scalar() or 0
            else:
                work_output = 0
                manhours = 0
                equipment_hours = 0
            
            months_data.append({
                'month': target_date.strftime('%Y-%m'),
                'month_name': target_date.strftime('%B %Y'),
                'working_days': len(forms),
                'work_output': float(work_output),
                'manhours': float(manhours),
                'equipment_hours': float(equipment_hours),
                'productivity': float(work_output) / float(manhours) if manhours > 0 else 0
            })
        
        # Calculate trends and changes
        if len(months_data) >= 2:
            latest = months_data[-1]
            previous = months_data[-2]
            
            changes = {
                'work_output': {
                    'value': latest['work_output'] - previous['work_output'],
                    'percent': ((latest['work_output'] - previous['work_output']) / previous['work_output'] * 100) if previous['work_output'] > 0 else 0
                },
                'manhours': {
                    'value': latest['manhours'] - previous['manhours'],
                    'percent': ((latest['manhours'] - previous['manhours']) / previous['manhours'] * 100) if previous['manhours'] > 0 else 0
                },
                'productivity': {
                    'value': latest['productivity'] - previous['productivity'],
                    'percent': ((latest['productivity'] - previous['productivity']) / previous['productivity'] * 100) if previous['productivity'] > 0 else 0
                }
            }
        else:
            changes = {}
        
        return {
            'months': months_data,
            'month_over_month_change': changes,
            'summary': {
                'total_work': sum(m['work_output'] for m in months_data),
                'total_manhours': sum(m['manhours'] for m in months_data),
                'average_monthly_output': sum(m['work_output'] for m in months_data) / len(months_data) if months_data else 0
            }
        }
    
    def get_project_comparison(self, other_project_ids=None):
        """
        Compare this project against other projects.
        
        Args:
            other_project_ids: List of project IDs to compare against
            
        Returns:
            dict: {
                'projects': list of project metrics,
                'ranking': dict,
                'benchmarks': dict
            }
        """
        from models.daily_form import DailyFormSubmission, ConstructionOperation, HumanResource
        from models.project import Project
        
        # Get all projects if not specified
        if not other_project_ids:
            projects = self.db.session.query(Project.id, Project.project_name).all()
            project_ids = [p.id for p in projects]
        else:
            project_ids = [self.project_id] + list(other_project_ids)
        
        projects_data = []
        
        for pid in project_ids:
            # Get project info
            project = self.db.session.query(Project).filter(Project.id == pid).first()
            if not project:
                continue
            
            # Get metrics
            forms = self.db.session.query(DailyFormSubmission).filter(
                DailyFormSubmission.project_id == pid,
                DailyFormSubmission.status == 'approved'
            ).all()
            
            form_ids = [f.id for f in forms]
            
            if form_ids:
                work_output = self.db.session.query(
                    func.sum(ConstructionOperation.amount)
                ).filter(
                    ConstructionOperation.daily_form_id.in_(form_ids)
                ).scalar() or 0
                
                manhours = self.db.session.query(
                    func.sum(HumanResource.working_hours * HumanResource.count)
                ).filter(
                    HumanResource.daily_form_id.in_(form_ids)
                ).scalar() or 0
            else:
                work_output = 0
                manhours = 0
            
            projects_data.append({
                'id': pid,
                'name': project.project_name,
                'working_days': len(forms),
                'work_output': float(work_output),
                'manhours': float(manhours),
                'productivity': float(work_output) / float(manhours) if manhours > 0 else 0,
                'is_current': pid == self.project_id
            })
        
        # Calculate rankings
        if projects_data:
            # Sort by different metrics
            by_output = sorted(projects_data, key=lambda x: x['work_output'], reverse=True)
            by_productivity = sorted(projects_data, key=lambda x: x['productivity'], reverse=True)
            
            # Find current project ranking
            current_output_rank = next((i + 1 for i, p in enumerate(by_output) if p['is_current']), None)
            current_productivity_rank = next((i + 1 for i, p in enumerate(by_productivity) if p['is_current']), None)
            
            # Calculate benchmarks (average)
            benchmarks = {
                'avg_output': sum(p['work_output'] for p in projects_data) / len(projects_data),
                'avg_productivity': sum(p['productivity'] for p in projects_data) / len(projects_data),
                'avg_manhours': sum(p['manhours'] for p in projects_data) / len(projects_data)
            }
        else:
            current_output_rank = None
            current_productivity_rank = None
            benchmarks = {}
        
        return {
            'projects': projects_data,
            'ranking': {
                'by_output': current_output_rank,
                'by_productivity': current_productivity_rank,
                'total_projects': len(projects_data)
            },
            'benchmarks': benchmarks
        }
    
    def get_actual_vs_planned(self):
        """
        Comprehensive actual vs planned comparison.
        
        Returns:
            dict: {
                'progress': dict,
                'budget': dict,
                'schedule': dict,
                'resources': dict
            }
        """
        from analysis.physical_progress import PhysicalProgressAnalysis
        from analysis.financial import FinancialAnalysis
        from analysis.resources import ResourceAnalysis
        from analysis.schedule import ScheduleAnalysis
        
        # Progress comparison
        progress_analysis = PhysicalProgressAnalysis(self.db, self.project_id, self.project_config)
        progress_by_activity = progress_analysis.get_progress_by_activity()
        overall = progress_analysis.get_overall_progress()
        
        progress_comparison = {
            'overall': {
                'planned': 100,  # Target
                'actual': overall['weighted_progress'],
                'variance': overall['weighted_progress'] - 100,
                'status': 'complete' if overall['weighted_progress'] >= 100 else 'in_progress'
            },
            'by_activity': {
                name: {
                    'planned': data['planned'],
                    'actual': data['actual'],
                    'variance': data['actual'] - data['planned'],
                    'variance_percent': ((data['actual'] - data['planned']) / data['planned'] * 100) if data['planned'] > 0 else 0,
                    'unit': data['unit']
                }
                for name, data in progress_by_activity.items()
            }
        }
        
        # Budget comparison
        financial_analysis = FinancialAnalysis(self.db, self.project_id, self.project_config)
        budget_actual = financial_analysis.get_budget_vs_actual()
        
        budget_comparison = {
            'total': {
                'planned': budget_actual['budget']['total'],
                'actual': budget_actual['actual']['total'],
                'variance': budget_actual['variance']['total'],
                'variance_percent': budget_actual['variance']['percent']
            },
            'categories': {
                'activity': {
                    'planned': budget_actual['budget'].get('activity', 0),
                    'actual': budget_actual['actual'].get('activity', 0)
                },
                'equipment': {
                    'planned': budget_actual['budget'].get('equipment', 0),
                    'actual': budget_actual['actual'].get('equipment', 0)
                },
                'material': {
                    'planned': budget_actual['budget'].get('material', 0),
                    'actual': budget_actual['actual'].get('material', 0)
                }
            }
        }
        
        # Schedule comparison
        schedule_analysis = ScheduleAnalysis(self.db, self.project_id, self.project_config)
        schedule_variance = schedule_analysis.get_schedule_variance()
        estimated = schedule_analysis.get_estimated_completion()
        
        schedule_comparison = {
            'progress': {
                'planned': schedule_variance['planned_progress'],
                'actual': schedule_variance['actual_progress'],
                'variance': schedule_variance['variance']
            },
            'completion': {
                'planned_date': estimated['planned_end_date'],
                'estimated_date': estimated['estimated_completion'],
                'variance_days': estimated['variance_days']
            },
            'spi': schedule_variance['spi']
        }
        
        # Resource comparison
        resource_analysis = ResourceAnalysis(self.db, self.project_id, self.project_config)
        planned_vs_actual = resource_analysis.get_planned_vs_actual_resources()
        
        resource_comparison = {
            'equipment': planned_vs_actual['equipment'],
            'human_resources': planned_vs_actual['human_resources']
        }
        
        return {
            'progress': progress_comparison,
            'budget': budget_comparison,
            'schedule': schedule_comparison,
            'resources': resource_comparison
        }
    
    def get_weekly_report(self, weeks_back=4):
        """
        Generate weekly performance reports.
        
        Args:
            weeks_back: Number of weeks to include
            
        Returns:
            dict: {
                'weeks': list of weekly data,
                'summary': dict,
                'highlights': list
            }
        """
        from models.daily_form import DailyFormSubmission, ConstructionOperation, HumanResource, ProjectIssue
        
        weeks_data = []
        now = datetime.now().date()
        
        for i in range(weeks_back - 1, -1, -1):
            # Calculate week boundaries
            week_end = now - timedelta(days=now.weekday() + 7 * i)
            week_start = week_end - timedelta(days=6)
            
            # Get forms for this week
            forms = self.db.session.query(DailyFormSubmission).filter(
                DailyFormSubmission.project_id == self.project_id,
                DailyFormSubmission.status == 'approved',
                DailyFormSubmission.form_date >= week_start,
                DailyFormSubmission.form_date <= week_end
            ).all()
            
            form_ids = [f.id for f in forms]
            
            if form_ids:
                # Work metrics
                work_output = self.db.session.query(
                    func.sum(ConstructionOperation.amount)
                ).filter(
                    ConstructionOperation.daily_form_id.in_(form_ids)
                ).scalar() or 0
                
                # Man-hours
                manhours = self.db.session.query(
                    func.sum(HumanResource.working_hours * HumanResource.count)
                ).filter(
                    HumanResource.daily_form_id.in_(form_ids)
                ).scalar() or 0
                
                # Issues
                issues_count = self.db.session.query(
                    func.count(ProjectIssue.id)
                ).filter(
                    ProjectIssue.daily_form_id.in_(form_ids)
                ).scalar() or 0
            else:
                work_output = 0
                manhours = 0
                issues_count = 0
            
            weeks_data.append({
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'week_label': f"Week of {week_start.strftime('%b %d')}",
                'working_days': len(forms),
                'work_output': float(work_output),
                'manhours': float(manhours),
                'productivity': float(work_output) / float(manhours) if manhours > 0 else 0,
                'issues': issues_count
            })
        
        # Generate highlights
        highlights = []
        trans = COMPARATIVE_TRANSLATIONS.get(self.lang, COMPARATIVE_TRANSLATIONS['en'])
        
        if len(weeks_data) >= 2:
            latest = weeks_data[-1]
            previous = weeks_data[-2]
            
            # Work output change
            if latest['work_output'] > previous['work_output'] * 1.1 and previous['work_output'] > 0:
                pct = ((latest['work_output']/previous['work_output'])-1)*100
                if self.lang == 'fa':
                    highlights.append(f"📈 خروجی کار {pct:.1f}% افزایش یافت")
                else:
                    highlights.append(f"📈 Work output increased by {pct:.1f}% this week")
            elif latest['work_output'] < previous['work_output'] * 0.9 and previous['work_output'] > 0:
                pct = (1-(latest['work_output']/previous['work_output']))*100
                if self.lang == 'fa':
                    highlights.append(f"📉 خروجی کار {pct:.1f}% کاهش یافت")
                else:
                    highlights.append(f"📉 Work output decreased by {pct:.1f}% this week")
            
            # Productivity change
            if latest['productivity'] > previous['productivity'] * 1.1:
                if self.lang == 'fa':
                    highlights.append("⚡ بهره‌وری این هفته بهبود یافته است")
                else:
                    highlights.append("⚡ Productivity improved this week")
            
            # Issues
            if latest['issues'] == 0:
                if self.lang == 'fa':
                    highlights.append("✅ این هفته مشکلی گزارش نشده است")
                else:
                    highlights.append("✅ No issues reported this week")
            elif latest['issues'] > previous['issues']:
                if self.lang == 'fa':
                    highlights.append(f"⚠️ مشکلات بیشتری نسبت به هفته قبل گزارش شده ({latest['issues']} در مقابل {previous['issues']})")
                else:
                    highlights.append(f"⚠️ More issues reported than last week ({latest['issues']} vs {previous['issues']})")
        
        # Summary
        total_output = sum(w['work_output'] for w in weeks_data)
        total_manhours = sum(w['manhours'] for w in weeks_data)
        total_issues = sum(w['issues'] for w in weeks_data)
        
        return {
            'weeks': weeks_data,
            'summary': {
                'period': f"{weeks_data[0]['week_start']} to {weeks_data[-1]['week_end']}",
                'total_working_days': sum(w['working_days'] for w in weeks_data),
                'total_work_output': total_output,
                'total_manhours': total_manhours,
                'average_weekly_output': total_output / len(weeks_data) if weeks_data else 0,
                'average_productivity': total_output / total_manhours if total_manhours > 0 else 0,
                'total_issues': total_issues
            },
            'highlights': highlights
        }
    
    def get_summary(self):
        """
        Get complete comparative analysis summary.
        
        Returns:
            dict: Complete comparative analysis
        """
        return {
            'month_over_month': self.get_month_over_month(3),
            'actual_vs_planned': self.get_actual_vs_planned(),
            'weekly_report': self.get_weekly_report(4)
        }
