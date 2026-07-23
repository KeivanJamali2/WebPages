"""
=============================================================================
Safety & HSE Analysis Module
=============================================================================

Provides safety and HSE analysis including:
- Incident rate tracking
- Inspection compliance
- Near-miss tracking
- Safety trend analysis
- Days without incident
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from collections import defaultdict


class SafetyAnalysis:
    """Analyze safety and HSE metrics."""
    
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
    
    def get_incident_rate(self):
        """
        Calculate incident rates.
        
        Returns:
            dict: {
                'total_incidents': int,
                'incident_rate': float,
                'by_severity': dict,
                'by_type': dict,
                'trir': float (Total Recordable Incident Rate)
            }
        """
        from models.daily_form import DailyFormSubmission, Safety
        
        # Get safety records
        safety_records = self.db.session.query(
            Safety
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).all()
        
        # Categorize incidents
        by_type = defaultdict(int)
        incidents = []
        total_incidents = 0
        
        for record in safety_records:
            # Check for incidents - exact match for "Incident" value or incident_occurred flag
            status_lower = (record.safety_situation or '').lower()
            is_incident = (
                status_lower == 'incident' or
                record.incident_occurred or
                'incident' in status_lower
            )
            
            if is_incident:
                total_incidents += 1
                incidents.append({
                    'status': record.safety_situation,
                    'description': record.incident_explanation
                })
            
            if record.safety_situation:
                by_type[record.safety_situation] += 1
        
        # Get total man-hours for TRIR calculation
        from analysis.resources import ResourceAnalysis
        resource_analysis = ResourceAnalysis(self.db, self.project_id, self.project_config)
        manhours_data = resource_analysis.get_manhours_analysis()
        total_manhours = manhours_data['total_manhours'] or 1
        
        # Calculate TRIR (incidents per 200,000 man-hours)
        trir = (total_incidents * 200000) / total_manhours
        
        # Calculate incident rate (per 1000 working days)
        working_days = manhours_data['working_days'] or 1
        incident_rate = (total_incidents / working_days) * 1000
        
        return {
            'total_incidents': total_incidents,
            'incident_rate': incident_rate,
            'by_type': dict(by_type),
            'trir': round(trir, 4),
            'total_manhours': total_manhours,
            'working_days': working_days,
            'recent_incidents': incidents[:10]  # Last 10
        }
    
    def get_inspection_compliance(self):
        """
        Analyze safety inspection compliance.
        
        Returns:
            dict: {
                'total_inspections': int,
                'passed': int,
                'failed': int,
                'compliance_rate': float,
                'by_status': dict
            }
        """
        from models.daily_form import DailyFormSubmission, Safety
        
        # Get safety inspection data - count days where inspection was done
        safety_data = self.db.session.query(
            Safety.safety_inspection,
            Safety.safety_situation,
            Safety.incident_occurred
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).all()
        
        by_status = defaultdict(int)
        total = len(safety_data)
        inspections_done = 0
        no_incidents = 0
        
        for record in safety_data:
            # Count inspections done
            if record.safety_inspection:
                inspections_done += 1
            
            # Count by safety situation
            status = record.safety_situation or 'Unknown'
            by_status[status] += 1
            
            # Count safe days (NoIncident)
            status_lower = status.lower()
            if status_lower == 'noincident' and not record.incident_occurred:
                no_incidents += 1
        
        # Compliance = days with no incidents / total days
        compliance_rate = (no_incidents / total * 100) if total > 0 else 100
        
        # Inspection rate = days with inspections / total days
        inspection_rate = (inspections_done / total * 100) if total > 0 else 0
        
        return {
            'total_days': total,
            'total_inspections': inspections_done,
            'inspection_rate': inspection_rate,
            'no_incidents': no_incidents,
            'incidents': total - no_incidents,
            'compliance_rate': compliance_rate,
            'by_status': dict(by_status)
        }
    
    def get_near_miss_tracking(self):
        """
        Track near-miss incidents.
        
        Returns:
            dict: {
                'total_near_misses': int,
                'by_category': dict,
                'trend': list,
                'rate_per_day': float
            }
        """
        from models.daily_form import DailyFormSubmission, Safety
        
        # Near-miss keywords - including the exact form values
        near_miss_keywords = ['nearmiss', 'near miss', 'near-miss', 'close call', 'تقریبی', 'نزدیک']
        
        # Get safety records with descriptions
        safety_records = self.db.session.query(
            Safety,
            DailyFormSubmission.form_date
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).order_by(
            DailyFormSubmission.form_date
        ).all()
        
        near_misses = []
        by_month = defaultdict(int)
        
        for record, form_date in safety_records:
            description = (record.incident_explanation or '').lower()
            status = (record.safety_situation or '').lower()
            
            # Check for exact "NearMiss" value or keyword matches
            if status == 'nearmiss' or any(kw in description or kw in status for kw in near_miss_keywords):
                near_misses.append({
                    'date': form_date.isoformat(),
                    'description': record.incident_explanation
                })
                by_month[form_date.strftime('%Y-%m')] += 1
        
        total_near_misses = len(near_misses)
        
        # Get total working days
        working_days = self.db.session.query(
            func.count(func.distinct(DailyFormSubmission.form_date))
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).scalar() or 1
        
        rate_per_day = total_near_misses / working_days
        
        # Build trend
        trend = [
            {'month': month, 'count': count}
            for month, count in sorted(by_month.items())
        ]
        
        return {
            'total_near_misses': total_near_misses,
            'by_month': dict(by_month),
            'trend': trend,
            'rate_per_day': rate_per_day,
            'recent': near_misses[-10:] if near_misses else []  # Last 10
        }
    
    def get_safety_trend(self):
        """
        Analyze safety trends over time.
        
        Returns:
            dict: {
                'monthly_data': list,
                'trend_direction': str,
                'improvement_rate': float
            }
        """
        from models.daily_form import DailyFormSubmission, Safety
        
        # Get monthly safety data
        monthly_data = self.db.session.query(
            func.strftime('%Y-%m', DailyFormSubmission.form_date).label('month'),
            func.count(Safety.id).label('records'),
            Safety.safety_situation
        ).join(
            Safety
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).group_by(
            func.strftime('%Y-%m', DailyFormSubmission.form_date),
            Safety.safety_situation
        ).all()
        
        # Aggregate by month
        months = defaultdict(lambda: {'total': 0, 'issues': 0})
        issue_keywords = ['incident', 'unsafe', 'violation', 'danger', 'خطر', 'حادثه']
        
        for data in monthly_data:
            months[data.month]['total'] += data.records
            status = (data.safety_situation or '').lower()
            if any(kw in status for kw in issue_keywords):
                months[data.month]['issues'] += data.records
        
        # Build trend data
        trend_data = []
        for month in sorted(months.keys()):
            data = months[month]
            safe_rate = ((data['total'] - data['issues']) / data['total'] * 100) if data['total'] > 0 else 100
            trend_data.append({
                'month': month,
                'total_records': data['total'],
                'issues': data['issues'],
                'safe_rate': safe_rate
            })
        
        # Determine trend direction
        if len(trend_data) >= 2:
            first_half = trend_data[:len(trend_data)//2]
            second_half = trend_data[len(trend_data)//2:]
            
            first_avg = sum(d['safe_rate'] for d in first_half) / len(first_half)
            second_avg = sum(d['safe_rate'] for d in second_half) / len(second_half)
            
            improvement_rate = second_avg - first_avg
            
            if improvement_rate > 5:
                trend_direction = 'improving'
            elif improvement_rate < -5:
                trend_direction = 'declining'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'insufficient_data'
            improvement_rate = 0
        
        return {
            'monthly_data': trend_data,
            'trend_direction': trend_direction,
            'improvement_rate': improvement_rate
        }
    
    def get_days_without_incident(self):
        """
        Calculate days without safety incidents.
        
        Returns:
            dict: {
                'current_streak': int,
                'longest_streak': int,
                'last_incident_date': str,
                'total_safe_days': int
            }
        """
        from models.daily_form import DailyFormSubmission, Safety
        
        # Get all form dates with safety status
        forms = self.db.session.query(
            DailyFormSubmission.form_date,
            Safety.safety_situation
        ).join(
            Safety
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).order_by(
            DailyFormSubmission.form_date
        ).all()
        
        if not forms:
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'last_incident_date': None,
                'total_safe_days': 0
            }
        
        # Keywords for incidents
        incident_keywords = ['incident', 'accident', 'injury', 'unsafe', 'حادثه', 'آسیب']
        
        # Process each day
        incident_dates = set()
        all_dates = set()
        
        for form_date, status in forms:
            all_dates.add(form_date)
            status_lower = (status or '').lower()
            if any(kw in status_lower for kw in incident_keywords):
                incident_dates.add(form_date)
        
        # Sort dates
        sorted_dates = sorted(all_dates)
        safe_days = [d for d in sorted_dates if d not in incident_dates]
        
        total_safe_days = len(safe_days)
        
        # Calculate current streak (from most recent)
        current_streak = 0
        for d in reversed(sorted_dates):
            if d not in incident_dates:
                current_streak += 1
            else:
                break
        
        # Calculate longest streak
        longest_streak = 0
        current = 0
        
        for d in sorted_dates:
            if d not in incident_dates:
                current += 1
                longest_streak = max(longest_streak, current)
            else:
                current = 0
        
        # Last incident date
        incident_dates_list = sorted(incident_dates)
        last_incident = incident_dates_list[-1].isoformat() if incident_dates_list else None
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'last_incident_date': last_incident,
            'total_safe_days': total_safe_days,
            'total_working_days': len(sorted_dates),
            'safe_day_percentage': (total_safe_days / len(sorted_dates) * 100) if sorted_dates else 100
        }
    
    def get_summary(self):
        """
        Get complete safety summary.
        
        Returns:
            dict: Complete safety analysis summary
        """
        return {
            'incident_rate': self.get_incident_rate(),
            'inspection_compliance': self.get_inspection_compliance(),
            'near_misses': self.get_near_miss_tracking(),
            'trend': self.get_safety_trend(),
            'days_without_incident': self.get_days_without_incident()
        }
