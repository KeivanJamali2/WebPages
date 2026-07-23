"""
=============================================================================
Issues & Problem Tracking Analysis Module
=============================================================================

Provides analysis of project issues including:
- Issues by category
- Issue frequency trends
- Issue locations
- Issue duration/resolution time
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from collections import defaultdict


class IssueAnalysis:
    """Analyze project issues and problems."""
    
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
        
        self.issue_categories = self.project_config.get('Project_Issues', {})
    
    def get_issues_by_category(self):
        """
        Categorize and count issues.
        
        Returns:
            dict: {
                'total_issues': int,
                'by_category': dict,
                'most_common': str,
                'category_details': dict
            }
        """
        from models.daily_form import DailyFormSubmission, ProjectIssue
        
        # Get issues grouped by category
        issues = self.db.session.query(
            ProjectIssue.issue_type,
            func.count(ProjectIssue.id).label('count'),
            func.group_concat(ProjectIssue.notes).label('descriptions')
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).group_by(
            ProjectIssue.issue_type
        ).all()
        
        by_category = {}
        category_details = {}
        total_issues = 0
        most_common = None
        max_count = 0
        
        for issue in issues:
            category = issue.issue_type or 'Uncategorized'
            count = int(issue.count or 0)
            
            by_category[category] = count
            total_issues += count
            
            # Parse descriptions
            descriptions = (issue.descriptions or '').split(',')
            category_details[category] = {
                'count': count,
                'sample_issues': descriptions[:5]  # First 5 examples
            }
            
            if count > max_count:
                max_count = count
                most_common = category
        
        # Calculate percentages
        for category in by_category:
            category_details[category]['percentage'] = (by_category[category] / total_issues * 100) if total_issues > 0 else 0
        
        return {
            'total_issues': total_issues,
            'by_category': by_category,
            'most_common': most_common,
            'category_details': category_details
        }
    
    def get_issue_frequency_trend(self):
        """
        Analyze issue frequency over time.
        
        Returns:
            dict: {
                'daily_average': float,
                'weekly_trend': list,
                'monthly_trend': list,
                'trend_direction': str
            }
        """
        from models.daily_form import DailyFormSubmission, ProjectIssue
        
        # Get issues with dates
        issues = self.db.session.query(
            DailyFormSubmission.form_date,
            func.count(ProjectIssue.id).label('count')
        ).join(
            ProjectIssue
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).group_by(
            DailyFormSubmission.form_date
        ).order_by(
            DailyFormSubmission.form_date
        ).all()
        
        if not issues:
            return {
                'daily_average': 0,
                'weekly_trend': [],
                'monthly_trend': [],
                'trend_direction': 'no_data'
            }
        
        # Daily data
        daily_data = {issue.form_date: int(issue.count or 0) for issue in issues}
        total_issues = sum(daily_data.values())
        total_days = len(daily_data)
        daily_average = total_issues / total_days if total_days > 0 else 0
        
        # Weekly aggregation
        weekly_data = defaultdict(int)
        for date, count in daily_data.items():
            week_start = date - timedelta(days=date.weekday())
            weekly_data[week_start] += count
        
        weekly_trend = [
            {'week': week.isoformat(), 'count': count}
            for week, count in sorted(weekly_data.items())
        ]
        
        # Monthly aggregation
        monthly_data = defaultdict(int)
        for date, count in daily_data.items():
            monthly_data[date.strftime('%Y-%m')] += count
        
        monthly_trend = [
            {'month': month, 'count': count}
            for month, count in sorted(monthly_data.items())
        ]
        
        # Determine trend direction
        if len(monthly_trend) >= 2:
            first_half = monthly_trend[:len(monthly_trend)//2]
            second_half = monthly_trend[len(monthly_trend)//2:]
            
            first_avg = sum(m['count'] for m in first_half) / len(first_half)
            second_avg = sum(m['count'] for m in second_half) / len(second_half)
            
            if second_avg > first_avg * 1.2:
                trend_direction = 'increasing'
            elif second_avg < first_avg * 0.8:
                trend_direction = 'decreasing'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'insufficient_data'
        
        return {
            'daily_average': daily_average,
            'weekly_trend': weekly_trend,
            'monthly_trend': monthly_trend,
            'trend_direction': trend_direction,
            'total_issues': total_issues,
            'days_with_issues': total_days
        }
    
    def get_issue_locations(self):
        """
        Analyze where issues occur (by station/location if available).
        
        Returns:
            dict: {
                'by_location': dict,
                'hotspots': list,
                'coverage': dict
            }
        """
        from models.daily_form import DailyFormSubmission, ProjectIssue
        
        # Get issues - try to extract location from description
        issues = self.db.session.query(
            ProjectIssue.issue_type,
            ProjectIssue.notes,
            ProjectIssue.effect,
            DailyFormSubmission.form_date
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).all()
        
        by_category_date = defaultdict(lambda: defaultdict(list))
        
        for issue in issues:
            category = issue.issue_type or 'Uncategorized'
            date_str = issue.form_date.strftime('%Y-%m')
            by_category_date[category][date_str].append({
                'description': issue.notes,
                'effect': issue.effect
            })
        
        # Find hotspots (categories with recurring issues)
        hotspots = []
        for category, months in by_category_date.items():
            recurring_months = len([m for m in months.values() if len(m) > 0])
            if recurring_months >= 2:  # Issues in 2+ months
                total = sum(len(m) for m in months.values())
                hotspots.append({
                    'category': category,
                    'total_issues': total,
                    'months_affected': recurring_months,
                    'recurring': True
                })
        
        # Sort hotspots by total issues
        hotspots.sort(key=lambda x: x['total_issues'], reverse=True)
        
        return {
            'by_category_time': {k: dict(v) for k, v in by_category_date.items()},
            'hotspots': hotspots[:10],  # Top 10
            'total_categories': len(by_category_date)
        }
    
    def get_issue_duration(self):
        """
        Analyze issue resolution patterns.
        Note: Since we don't track resolution dates directly,
        we estimate based on recurrence patterns.
        
        Returns:
            dict: {
                'resolved_issues': int,
                'pending_issues': int,
                'resolution_rate': float,
                'by_category': dict
            }
        """
        from models.daily_form import DailyFormSubmission, ProjectIssue
        
        # Get all issues with effect field
        issues = self.db.session.query(
            ProjectIssue.issue_type,
            ProjectIssue.notes,
            ProjectIssue.effect,
            DailyFormSubmission.form_date
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).order_by(
            DailyFormSubmission.form_date
        ).all()
        
        # Categorize by resolution status
        resolved = 0
        pending = 0
        by_category = defaultdict(lambda: {'total': 0, 'resolved': 0, 'pending': 0})
        
        # Keywords indicating resolution
        resolved_keywords = ['resolved', 'fixed', 'completed', 'done', 'حل شد', 'برطرف']
        pending_keywords = ['pending', 'ongoing', 'in progress', 'در حال']
        
        for issue in issues:
            category = issue.issue_type or 'Uncategorized'
            effect = (issue.effect or '').lower()
            
            by_category[category]['total'] += 1
            
            # Check if resolved based on effect description
            if effect and any(kw in effect for kw in resolved_keywords):
                resolved += 1
                by_category[category]['resolved'] += 1
            elif effect and any(kw in effect for kw in pending_keywords):
                pending += 1
                by_category[category]['pending'] += 1
            else:
                # Assume pending if no clear resolution
                pending += 1
                by_category[category]['pending'] += 1
        
        total = resolved + pending
        resolution_rate = (resolved / total * 100) if total > 0 else 0
        
        # Calculate per-category rates
        for category in by_category:
            cat_total = by_category[category]['total']
            cat_resolved = by_category[category]['resolved']
            by_category[category]['resolution_rate'] = (cat_resolved / cat_total * 100) if cat_total > 0 else 0
        
        return {
            'total_issues': total,
            'resolved_issues': resolved,
            'pending_issues': pending,
            'resolution_rate': resolution_rate,
            'by_category': dict(by_category)
        }
    
    def get_summary(self):
        """
        Get complete issue analysis summary.
        
        Returns:
            dict: Complete issue analysis summary
        """
        return {
            'by_category': self.get_issues_by_category(),
            'frequency_trend': self.get_issue_frequency_trend(),
            'locations': self.get_issue_locations(),
            'duration': self.get_issue_duration()
        }
