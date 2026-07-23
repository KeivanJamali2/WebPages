"""
=============================================================================
Schedule & Time Analysis Module
=============================================================================

Provides schedule and time-related analysis including:
- Working days tracking
- Weather impact analysis
- Issue impact on schedule
- Estimated completion date
- Schedule variance analysis
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from collections import defaultdict


class ScheduleAnalysis:
    """Analyze schedule and time-related metrics."""
    
    def __init__(self, db, project_id, project_config=None):
        """
        Initialize the analysis.
        
        Args:
            db: SQLAlchemy database instance
            project_id: Project ID to analyze
            project_config: Project configuration dictionary
        """
        self.db = db
        self.project_id = project_id
        self.project_config = project_config or {}
        
        self.project_info = self.project_config.get('Project_Info', {})
    
    def get_working_days_analysis(self):
        """
        Analyze working days patterns.
        
        Returns:
            dict: {
                'total_working_days': int,
                'calendar_days': int,
                'efficiency_rate': float,
                'by_month': dict,
                'by_weekday': dict
            }
        """
        from models.daily_form import DailyFormSubmission
        
        # Get all forms
        forms = self.db.session.query(
            DailyFormSubmission.form_date
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).order_by(
            DailyFormSubmission.form_date
        ).all()
        
        if not forms:
            return {
                'total_working_days': 0,
                'calendar_days': 0,
                'efficiency_rate': 0,
                'by_month': {},
                'by_weekday': {},
                'streak_info': {}
            }
        
        dates = [f.form_date for f in forms]
        total_working_days = len(dates)
        
        # Calculate calendar days
        first_date = dates[0]
        last_date = dates[-1]
        calendar_days = (last_date - first_date).days + 1
        
        efficiency_rate = (total_working_days / calendar_days * 100) if calendar_days > 0 else 0
        
        # Group by month
        by_month = defaultdict(int)
        for d in dates:
            by_month[d.strftime('%Y-%m')] += 1
        
        # Group by weekday
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        by_weekday = defaultdict(int)
        for d in dates:
            by_weekday[weekdays[d.weekday()]] += 1
        
        # Calculate work streak
        date_set = set(dates)
        current_streak = 0
        max_streak = 0
        current_date = last_date
        
        while current_date >= first_date:
            if current_date in date_set:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
            current_date -= timedelta(days=1)
        
        # Current streak (from last date)
        current_streak = 0
        check_date = last_date
        while check_date in date_set:
            current_streak += 1
            check_date -= timedelta(days=1)
        
        return {
            'total_working_days': total_working_days,
            'calendar_days': calendar_days,
            'efficiency_rate': efficiency_rate,
            'first_date': first_date.isoformat(),
            'last_date': last_date.isoformat(),
            'by_month': dict(by_month),
            'by_weekday': dict(by_weekday),
            'streak_info': {
                'current_streak': current_streak,
                'max_streak': max_streak
            }
        }
    
    def get_weather_impact(self):
        """
        Analyze weather impact on work.
        
        Returns:
            dict: {
                'total_days_analyzed': int,
                'weather_distribution': dict,
                'productivity_by_weather': dict,
                'lost_days_weather': int
            }
        """
        from models.daily_form import DailyFormSubmission, ClimateCondition, ConstructionOperation
        
        # Get climate data with productivity
        climate_data = self.db.session.query(
            ClimateCondition.weather_type,
            ClimateCondition.climate_effect,
            func.count(func.distinct(DailyFormSubmission.id)).label('days'),
            func.sum(ConstructionOperation.amount).label('total_work')
        ).select_from(DailyFormSubmission).join(
            ClimateCondition, ClimateCondition.daily_form_id == DailyFormSubmission.id
        ).outerjoin(
            ConstructionOperation, ConstructionOperation.daily_form_id == DailyFormSubmission.id
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).group_by(
            ClimateCondition.weather_type,
            ClimateCondition.climate_effect
        ).all()
        
        weather_distribution = defaultdict(lambda: {'days': 0, 'total_work': 0})
        work_status_distribution = defaultdict(int)
        total_days = 0
        
        for data in climate_data:
            weather = data.weather_type or 'Unknown'
            work_status = data.climate_effect or 'Unknown'
            days = int(data.days or 0)
            work = float(data.total_work or 0)
            
            weather_distribution[weather]['days'] += days
            weather_distribution[weather]['total_work'] += work
            work_status_distribution[work_status] += days
            total_days += days
        
        # Calculate productivity by weather
        productivity_by_weather = {}
        for weather, data in weather_distribution.items():
            days = data['days']
            work = data['total_work']
            productivity_by_weather[weather] = {
                'days': days,
                'total_work': work,
                'avg_work_per_day': work / days if days > 0 else 0,
                'percent_of_total': (days / total_days * 100) if total_days > 0 else 0
            }
        
        # Count days with work stopped due to weather (handle various formats)
        lost_days = (
            work_status_distribution.get('stopped', 0) + 
            work_status_distribution.get('Stopped', 0) + 
            work_status_distribution.get('work_stopped', 0)
        )
        slow_days = (
            work_status_distribution.get('slow_progress', 0) +
            work_status_distribution.get('Slow Progress', 0)
        )
        
        return {
            'total_days_analyzed': total_days,
            'weather_distribution': dict(weather_distribution),
            'work_status_distribution': dict(work_status_distribution),
            'productivity_by_weather': productivity_by_weather,
            'lost_days_weather': lost_days,
            'slow_days_weather': slow_days
        }
    
    def get_issue_impact(self):
        """
        Analyze impact of issues on schedule.
        
        Returns:
            dict: {
                'total_issues': int,
                'delays_caused': dict,
                'days_lost_to_issues': int,
                'critical_issues': list
            }
        """
        from models.daily_form import DailyFormSubmission, ProjectIssue
        
        # Get issues
        issues = self.db.session.query(
            ProjectIssue
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).all()
        
        total_issues = len(issues)
        issues_by_category = defaultdict(list)
        critical_issues = []
        
        for issue in issues:
            issues_by_category[issue.issue_type or 'Other'].append({
                'description': issue.notes,
                'effect': issue.effect
            })
            
            # Check for critical issues (keywords)
            critical_keywords = ['stop', 'halt', 'delay', 'emergency', 'critical', 'accident', 'توقف', 'بحران']
            description = (issue.notes or '').lower()
            effect = (issue.effect or '').lower()
            if any(kw in description or kw in effect for kw in critical_keywords):
                critical_issues.append({
                    'category': issue.issue_type,
                    'description': issue.notes,
                    'effect': issue.effect
                })
        
        # Estimate days lost (simplified - count days with critical issues)
        days_with_issues = self.db.session.query(
            func.count(func.distinct(DailyFormSubmission.form_date))
        ).join(
            ProjectIssue
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).scalar() or 0
        
        delays_by_category = {
            category: len(issues_list) 
            for category, issues_list in issues_by_category.items()
        }
        
        return {
            'total_issues': total_issues,
            'issues_by_category': {k: len(v) for k, v in issues_by_category.items()},
            'delays_caused': delays_by_category,
            'days_with_issues': days_with_issues,
            'critical_issues': critical_issues[:10]  # Top 10
        }
    
    def get_estimated_completion(self):
        """
        Calculate estimated completion date.
        
        Returns:
            dict: {
                'planned_end_date': str,
                'estimated_completion': str,
                'variance_days': int,
                'completion_percent': float,
                'days_remaining': int,
                'confidence': str
            }
        """
        from analysis.physical_progress import PhysicalProgressAnalysis
        
        # Get progress
        progress_analysis = PhysicalProgressAnalysis(self.db, self.project_id, self.project_config)
        overall = progress_analysis.get_overall_progress()
        velocity = progress_analysis.get_progress_velocity()
        
        completion_percent = overall['weighted_progress']
        daily_progress = velocity.get('last_7_days', 0)  # Use recent velocity
        
        # Get planned dates
        planned_start = self.project_info.get('start_date')
        planned_end = self.project_info.get('end_date')
        
        # Calculate remaining work
        remaining_percent = 100 - completion_percent
        
        # Estimate days needed
        if daily_progress > 0 and overall['total_planned_value'] > 0:
            remaining_value = overall['total_planned_value'] - overall['total_actual_value']
            # Estimate based on current velocity
            working_days = self.get_working_days_analysis()
            efficiency = working_days['efficiency_rate'] / 100 if working_days['efficiency_rate'] > 0 else 0.7
            
            # Days needed (accounting for non-working days)
            days_needed = remaining_value / (velocity['daily_average'] or 1) / efficiency if velocity['daily_average'] > 0 else 0
            
            estimated_completion = datetime.now().date() + timedelta(days=int(days_needed))
        else:
            estimated_completion = None
            days_needed = 0
        
        # Calculate variance
        variance_days = 0
        if planned_end and estimated_completion:
            try:
                planned = datetime.strptime(planned_end, '%Y-%m-%d').date()
                variance_days = (estimated_completion - planned).days
            except:
                pass
        
        # Determine confidence
        if velocity['trend'] == 'increasing':
            confidence = 'high'
        elif velocity['trend'] == 'decreasing':
            confidence = 'low'
        else:
            confidence = 'medium'
        
        return {
            'planned_start_date': planned_start,
            'planned_end_date': planned_end,
            'estimated_completion': estimated_completion.isoformat() if estimated_completion else None,
            'variance_days': variance_days,
            'completion_percent': completion_percent,
            'days_remaining': int(days_needed) if days_needed else None,
            'confidence': confidence,
            'status': 'on_track' if variance_days <= 0 else ('at_risk' if variance_days <= 14 else 'delayed')
        }
    
    def get_schedule_variance(self):
        """
        Calculate detailed schedule variance analysis.
        
        Returns:
            dict: {
                'planned_progress': float,
                'actual_progress': float,
                'variance': float,
                'variance_percent': float,
                'spi': float (Schedule Performance Index)
            }
        """
        from analysis.physical_progress import PhysicalProgressAnalysis
        
        # Get progress
        progress_analysis = PhysicalProgressAnalysis(self.db, self.project_id, self.project_config)
        overall = progress_analysis.get_overall_progress()
        
        actual_progress = overall['weighted_progress']
        
        # Calculate planned progress based on time elapsed
        planned_start = self.project_info.get('start_date')
        planned_end = self.project_info.get('end_date')
        
        if planned_start and planned_end:
            try:
                start = datetime.strptime(planned_start, '%Y-%m-%d').date()
                end = datetime.strptime(planned_end, '%Y-%m-%d').date()
                today = datetime.now().date()
                
                total_days = (end - start).days or 1
                elapsed_days = max(0, (today - start).days)
                time_percent = min(elapsed_days / total_days * 100, 100)
                
                # Planned progress (assuming linear)
                planned_progress = time_percent
            except:
                planned_progress = 50
        else:
            planned_progress = 50  # Default assumption
        
        # Calculate variance
        variance = actual_progress - planned_progress
        variance_percent = (variance / planned_progress * 100) if planned_progress > 0 else 0
        
        # Schedule Performance Index
        spi = actual_progress / planned_progress if planned_progress > 0 else 1
        
        return {
            'planned_progress': planned_progress,
            'actual_progress': actual_progress,
            'variance': variance,
            'variance_percent': variance_percent,
            'spi': round(spi, 3),
            'interpretation': 'ahead' if spi > 1.05 else ('behind' if spi < 0.95 else 'on schedule'),
            'time_elapsed_percent': planned_progress
        }
    
    def get_summary(self):
        """
        Get complete schedule summary.
        
        Returns:
            dict: Complete schedule analysis summary
        """
        return {
            'working_days': self.get_working_days_analysis(),
            'weather_impact': self.get_weather_impact(),
            'issue_impact': self.get_issue_impact(),
            'estimated_completion': self.get_estimated_completion(),
            'schedule_variance': self.get_schedule_variance()
        }
