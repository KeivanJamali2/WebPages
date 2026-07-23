"""
=============================================================================
Physical Progress Analysis Module
=============================================================================

Provides analysis of physical construction progress including:
- Progress by activity type
- Overall project progress
- Progress trend over time
- Progress velocity
- Roadmap coverage visualization
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_
from collections import defaultdict


class PhysicalProgressAnalysis:
    """Analyze physical construction progress."""
    
    def __init__(self, db, project_id, project_config=None):
        """
        Initialize the analysis.
        
        Args:
            db: SQLAlchemy database instance
            project_id: Project ID to analyze
            project_config: Project configuration dictionary (optional)
        """
        self.db = db
        self.project_id = project_id
        self.project_config = project_config or {}
    
    def get_progress_by_activity(self):
        """
        Calculate progress percentage for each activity type.
        
        Returns:
            dict: {activity_name: {
                'actual': float,
                'planned': float,
                'unit': str,
                'progress_percent': float,
                'remaining': float
            }}
        """
        from models.daily_form import DailyFormSubmission, ConstructionOperation
        
        # Get all approved operations for this project
        operations = self.db.session.query(
            ConstructionOperation.operation_type,
            func.sum(ConstructionOperation.amount).label('total_amount'),
            ConstructionOperation.unit
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).group_by(
            ConstructionOperation.operation_type,
            ConstructionOperation.unit
        ).all()
        
        # Get planned amounts from config
        activity_budget = self.project_config.get('Activity_Budget', {})
        daily_activities = self.project_config.get('Daily_Activity_Report', {})
        
        result = {}
        
        # First, add all planned activities with 0 progress
        for activity_name, unit in daily_activities.items():
            budget_info = activity_budget.get(activity_name, {})
            planned = budget_info.get('planned_amount', 0)
            
            result[activity_name] = {
                'actual': 0,
                'planned': planned,
                'unit': unit,
                'progress_percent': 0,
                'remaining': planned,
                'price_per_unit': budget_info.get('price_per_unit', 0)
            }
        
        # Update with actual data
        for op in operations:
            activity_name = op.operation_type
            actual = float(op.total_amount or 0)
            
            if activity_name in result:
                result[activity_name]['actual'] = actual
                planned = result[activity_name]['planned']
                if planned > 0:
                    result[activity_name]['progress_percent'] = min((actual / planned) * 100, 100)
                    result[activity_name]['remaining'] = max(planned - actual, 0)
                else:
                    result[activity_name]['progress_percent'] = 100 if actual > 0 else 0
            else:
                # Activity not in config but has data
                result[activity_name] = {
                    'actual': actual,
                    'planned': 0,
                    'unit': op.unit or '',
                    'progress_percent': 100,
                    'remaining': 0,
                    'price_per_unit': 0
                }
        
        return result
    
    def get_overall_progress(self):
        """
        Calculate overall project physical progress.
        Uses weighted average based on planned amounts and prices.
        
        Returns:
            dict: {
                'weighted_progress': float (0-100),
                'simple_progress': float (0-100),
                'total_planned_value': float,
                'total_actual_value': float,
                'activities_count': int,
                'activities_completed': int
            }
        """
        progress_by_activity = self.get_progress_by_activity()
        
        total_planned_value = 0
        total_actual_value = 0
        simple_progress_sum = 0
        activities_count = 0
        activities_completed = 0
        
        for activity, data in progress_by_activity.items():
            if data['planned'] > 0:
                activities_count += 1
                planned_value = data['planned'] * data['price_per_unit']
                actual_value = data['actual'] * data['price_per_unit']
                
                total_planned_value += planned_value
                total_actual_value += actual_value
                simple_progress_sum += data['progress_percent']
                
                if data['progress_percent'] >= 100:
                    activities_completed += 1
        
        weighted_progress = 0
        if total_planned_value > 0:
            weighted_progress = (total_actual_value / total_planned_value) * 100
        
        simple_progress = 0
        if activities_count > 0:
            simple_progress = simple_progress_sum / activities_count
        
        return {
            'weighted_progress': min(weighted_progress, 100),
            'simple_progress': min(simple_progress, 100),
            'total_planned_value': total_planned_value,
            'total_actual_value': total_actual_value,
            'activities_count': activities_count,
            'activities_completed': activities_completed
        }
    
    def get_progress_trend(self, days=30, interval='daily'):
        """
        Get progress trend over time.
        
        Args:
            days: Number of days to look back
            interval: 'daily', 'weekly', or 'monthly'
            
        Returns:
            list: [{date: str, cumulative_progress: float, daily_amount: float}]
        """
        from models.daily_form import DailyFormSubmission, ConstructionOperation
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get daily totals
        daily_data = self.db.session.query(
            DailyFormSubmission.form_date,
            func.sum(ConstructionOperation.amount * 
                     func.coalesce(ConstructionOperation.amount, 0)).label('daily_value')
        ).join(
            ConstructionOperation
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved',
            DailyFormSubmission.form_date >= start_date,
            DailyFormSubmission.form_date <= end_date
        ).group_by(
            DailyFormSubmission.form_date
        ).order_by(
            DailyFormSubmission.form_date
        ).all()
        
        # Get total planned value for percentage calculation
        overall = self.get_overall_progress()
        total_planned = overall['total_planned_value'] or 1
        
        # Build trend data
        trend = []
        cumulative = 0
        
        # Convert to dict for easy lookup
        daily_dict = {d.form_date: float(d.daily_value or 0) for d in daily_data}
        
        current_date = start_date
        while current_date <= end_date:
            daily_value = daily_dict.get(current_date, 0)
            cumulative += daily_value
            
            trend.append({
                'date': current_date.isoformat(),
                'date_display': current_date.strftime('%Y-%m-%d'),
                'daily_value': daily_value,
                'cumulative_value': cumulative,
                'cumulative_progress': (cumulative / total_planned) * 100 if total_planned > 0 else 0
            })
            
            current_date += timedelta(days=1)
        
        # Aggregate if needed
        if interval == 'weekly':
            trend = self._aggregate_by_week(trend)
        elif interval == 'monthly':
            trend = self._aggregate_by_month(trend)
        
        return trend
    
    def _aggregate_by_week(self, daily_data):
        """Aggregate daily data by week."""
        if not daily_data:
            return []
        
        weekly = []
        current_week = []
        
        for day in daily_data:
            current_week.append(day)
            date = datetime.fromisoformat(day['date'])
            
            if date.weekday() == 6 or day == daily_data[-1]:  # Sunday or last day
                if current_week:
                    weekly.append({
                        'date': current_week[0]['date'],
                        'date_display': f"Week of {current_week[0]['date_display']}",
                        'daily_value': sum(d['daily_value'] for d in current_week),
                        'cumulative_value': current_week[-1]['cumulative_value'],
                        'cumulative_progress': current_week[-1]['cumulative_progress']
                    })
                    current_week = []
        
        return weekly
    
    def _aggregate_by_month(self, daily_data):
        """Aggregate daily data by month."""
        if not daily_data:
            return []
        
        monthly = defaultdict(list)
        
        for day in daily_data:
            date = datetime.fromisoformat(day['date'])
            month_key = date.strftime('%Y-%m')
            monthly[month_key].append(day)
        
        result = []
        for month_key in sorted(monthly.keys()):
            days = monthly[month_key]
            result.append({
                'date': days[0]['date'],
                'date_display': datetime.fromisoformat(days[0]['date']).strftime('%Y-%m'),
                'daily_value': sum(d['daily_value'] for d in days),
                'cumulative_value': days[-1]['cumulative_value'],
                'cumulative_progress': days[-1]['cumulative_progress']
            })
        
        return result
    
    def get_progress_velocity(self):
        """
        Calculate progress velocity (rate of work completion).
        
        Returns:
            dict: {
                'daily_average': float,
                'weekly_average': float,
                'last_7_days': float,
                'last_30_days': float,
                'trend': str ('increasing', 'decreasing', 'stable')
            }
        """
        from models.daily_form import DailyFormSubmission, ConstructionOperation
        
        # Get all approved forms with work
        forms = self.db.session.query(
            DailyFormSubmission.form_date,
            func.sum(ConstructionOperation.amount).label('total_amount')
        ).join(
            ConstructionOperation
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).group_by(
            DailyFormSubmission.form_date
        ).order_by(
            DailyFormSubmission.form_date
        ).all()
        
        if not forms:
            return {
                'daily_average': 0,
                'weekly_average': 0,
                'last_7_days': 0,
                'last_30_days': 0,
                'trend': 'stable',
                'working_days': 0
            }
        
        # Calculate averages
        total_amount = sum(float(f.total_amount or 0) for f in forms)
        working_days = len(forms)
        daily_average = total_amount / working_days if working_days > 0 else 0
        
        # Last 7 and 30 days
        now = datetime.now().date()
        last_7 = [f for f in forms if (now - f.form_date).days <= 7]
        last_30 = [f for f in forms if (now - f.form_date).days <= 30]
        
        last_7_total = sum(float(f.total_amount or 0) for f in last_7)
        last_30_total = sum(float(f.total_amount or 0) for f in last_30)
        
        last_7_avg = last_7_total / len(last_7) if last_7 else 0
        last_30_avg = last_30_total / len(last_30) if last_30 else 0
        
        # Determine trend
        trend = 'stable'
        if last_7_avg > daily_average * 1.1:
            trend = 'increasing'
        elif last_7_avg < daily_average * 0.9:
            trend = 'decreasing'
        
        return {
            'daily_average': daily_average,
            'weekly_average': daily_average * 7,
            'last_7_days': last_7_avg,
            'last_30_days': last_30_avg,
            'trend': trend,
            'working_days': working_days
        }
    
    def get_roadmap_coverage(self):
        """
        Get roadmap coverage for station-based operations.
        
        Returns:
            dict: {
                'activities': {activity_name: {
                    'segments': [{start: float, end: float, amount: float}],
                    'total_length': float,
                    'coverage_percent': float
                }},
                'global_min': float,
                'global_max': float,
                'total_coverage': float
            }
        """
        from models.daily_form import DailyFormSubmission, ConstructionOperation
        
        # Get all operations with station data
        operations = self.db.session.query(
            ConstructionOperation
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved',
            ConstructionOperation.start_station.isnot(None),
            ConstructionOperation.end_station.isnot(None)
        ).all()
        
        if not operations:
            return {
                'activities': {},
                'global_min': 0,
                'global_max': 0,
                'total_coverage': 0
            }
        
        # Group by activity
        activities = defaultdict(lambda: {'segments': [], 'total_length': 0})
        global_min = float('inf')
        global_max = 0
        
        for op in operations:
            start_m = op.start_meters
            end_m = op.end_meters
            
            if start_m is not None and end_m is not None:
                activities[op.operation_type]['segments'].append({
                    'start': start_m,
                    'end': end_m,
                    'start_station': op.start_station,
                    'end_station': op.end_station,
                    'amount': op.amount,
                    'length': end_m - start_m
                })
                activities[op.operation_type]['total_length'] += (end_m - start_m)
                
                global_min = min(global_min, start_m)
                global_max = max(global_max, end_m)
        
        # Calculate coverage percentages
        total_range = global_max - global_min if global_max > global_min else 1
        
        for activity in activities.values():
            activity['coverage_percent'] = (activity['total_length'] / total_range) * 100
        
        return {
            'activities': dict(activities),
            'global_min': global_min if global_min != float('inf') else 0,
            'global_max': global_max,
            'total_coverage': total_range
        }
    
    def get_summary(self):
        """
        Get a complete summary of physical progress.
        
        Returns:
            dict: Complete physical progress summary
        """
        return {
            'by_activity': self.get_progress_by_activity(),
            'overall': self.get_overall_progress(),
            'velocity': self.get_progress_velocity(),
            'roadmap': self.get_roadmap_coverage()
        }
