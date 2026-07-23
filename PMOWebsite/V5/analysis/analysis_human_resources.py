"""
Human Resources Analysis
=========================

Analyzes personnel data: positions, headcount, working hours, and presence rates.
"""
from typing import Dict, List, Any
from collections import defaultdict


class HumanResourcesAnalysis:
    """
    Analyzes human resources data from daily forms.
    
    Provides:
    - Summary table by position (days present, people-days, hours, presence rate)
    - Daily detail per position
    - Headcount trends over time
    - Hours distribution and trends
    - Presence analysis vs. expected days
    """
    
    def __init__(self, data_service, project_config: dict):
        """
        Initialize analysis with data service and project config.
        
        Args:
            data_service: DataService instance with get_human_resources() method
            project_config: Project configuration dict with Human_Resources_Rates
        """
        self.ds = data_service
        self.config = project_config
        self.hr_data = data_service.get_human_resources()
        
        # Get expected days from config
        self.hr_rates = project_config.get('Human_Resources_Rates', {})
    
    def get_summary_table(self, unit: str = "per_day") -> Dict[str, Any]:
        """
        Get summary statistics per position.
        
        Args:
            unit: Time unit for averages (per_day, per_week, per_month, per_hour)
        
        Returns:
            Dict with:
            - rows: List of position summaries
            - totals: Grand totals across all positions
        """
        # Group data by position
        by_position = defaultdict(lambda: {
            'dates': set(),
            'people_days': 0,
            'total_hours': 0,
            'daily_records': []
        })
        
        for record in self.hr_data:
            post = record['post']
            count = record.get('count', 0)
            hours = record.get('working_hours', 0)
            date = record['form_date']
            
            by_position[post]['dates'].add(date)
            by_position[post]['people_days'] += count
            by_position[post]['total_hours'] += count * hours
            by_position[post]['daily_records'].append({
                'date': date,
                'count': count,
                'hours': hours,
                'notes': record.get('notes', '')
            })
        
        # Build summary rows
        rows = []
        for post, data in by_position.items():
            days_present = len(data['dates'])
            people_days = data['people_days']
            total_hours = data['total_hours']
            
            # Avg hours per day
            avg_hours_per_day = total_hours / days_present if days_present > 0 else 0
            
            # Unit conversion
            multiplier = self._get_unit_multiplier(unit)
            avg_hours = avg_hours_per_day * multiplier
            
            # Expected days from config
            expected_days = self.hr_rates.get(post, {}).get('total_days', 0)
            
            # Presence rate
            presence_rate = (days_present / expected_days * 100) if expected_days > 0 else 0
            
            # First & last date
            sorted_dates = sorted(data['dates'])
            first_date = sorted_dates[0] if sorted_dates else None
            last_date = sorted_dates[-1] if sorted_dates else None
            
            rows.append({
                'post': post,
                'days_present': days_present,
                'people_days': people_days,
                'total_hours': total_hours,
                'avg_hours': round(avg_hours, 2),
                'expected_days': expected_days,
                'presence_rate': round(presence_rate, 1),
                'first_date': first_date,
                'last_date': last_date
            })
        
        # Sort by total hours descending
        rows.sort(key=lambda x: x['total_hours'], reverse=True)
        
        # Calculate totals
        totals = {
            'people_days': sum(r['people_days'] for r in rows),
            'total_hours': sum(r['total_hours'] for r in rows)
        }
        
        return {'rows': rows, 'totals': totals}
    
    def get_daily_detail(self, post: str = None) -> List[Dict[str, Any]]:
        """
        Get daily breakdown, optionally filtered by position.
        
        Args:
            post: Position name to filter by (None = all positions)
        
        Returns:
            List of daily records with date, post, count, hours, notes
        """
        details = []
        for record in self.hr_data:
            if post and record['post'] != post:
                continue
            
            count = record.get('count', 0)
            hours = record.get('working_hours', 0)
            
            details.append({
                'date': record['form_date'],
                'post': record['post'],
                'count': count,
                'working_hours': hours,
                'notes': record.get('notes', '')
            })
        
        # Sort by date descending
        details.sort(key=lambda x: x['date'], reverse=True)
        return details
    
    def get_presence_analysis(self) -> List[Dict[str, Any]]:
        """
        Get presence rate analysis for each position.
        
        Returns:
            List of dicts with post, expected_days, actual_days, presence_rate
        """
        by_position = defaultdict(set)
        for record in self.hr_data:
            by_position[record['post']].add(record['form_date'])
        
        analysis = []
        for post, dates in by_position.items():
            actual_days = len(dates)
            expected_days = self.hr_rates.get(post, {}).get('total_days', 0)
            presence_rate = (actual_days / expected_days * 100) if expected_days > 0 else 0
            
            analysis.append({
                'post': post,
                'expected_days': expected_days,
                'actual_days': actual_days,
                'presence_rate': round(presence_rate, 1),
                'status': 'good' if presence_rate >= 90 else 'warning' if presence_rate >= 70 else 'poor'
            })
        
        # Sort by presence rate descending
        analysis.sort(key=lambda x: x['presence_rate'], reverse=True)
        return analysis
    
    def get_hours_by_position(self) -> List[Dict[str, Any]]:
        """
        Get total working hours per position, sorted descending.
        
        Returns:
            List of dicts with post and total_hours
        """
        by_position = defaultdict(float)
        
        for record in self.hr_data:
            post = record['post']
            count = record.get('count', 0)
            hours = record.get('working_hours', 0)
            total = count * hours
            by_position[post] += total
        
        hours_data = [{'post': post, 'total_hours': round(hours, 2)} 
                      for post, hours in by_position.items()]
        hours_data.sort(key=lambda x: x['total_hours'], reverse=True)
        
        # Group top 15, rest as "Others"
        if len(hours_data) > 15:
            top15 = hours_data[:15]
            others_hours = sum(h['total_hours'] for h in hours_data[15:])
            top15.append({'post': 'سایر', 'total_hours': round(others_hours, 2)})
            return top15
        
        return hours_data
    
    def get_headcount_over_time(self) -> List[Dict[str, Any]]:
        """
        Get daily headcount stacked by position.
        
        Returns:
            List of dicts with date and counts per position
        """
        by_date = defaultdict(lambda: defaultdict(int))
        
        for record in self.hr_data:
            date = record['form_date']
            post = record['post']
            count = record.get('count', 0)
            by_date[date][post] += count
        
        # Convert to list format
        result = []
        for date in sorted(by_date.keys()):
            row = {'date': date}
            row.update(by_date[date])
            result.append(row)
        
        return result
    
    def get_daily_hours_trend(self) -> List[Dict[str, Any]]:
        """
        Get total working hours per day.
        
        Returns:
            List of dicts with date and total_hours
        """
        by_date = defaultdict(float)
        
        for record in self.hr_data:
            date = record['form_date']
            count = record.get('count', 0)
            hours = record.get('working_hours', 0)
            total = count * hours
            by_date[date] += total
        
        trend = [{'date': date, 'total_hours': round(hours, 2)} 
                 for date, hours in by_date.items()]
        trend.sort(key=lambda x: x['date'])
        return trend
    
    def get_all(self, unit: str = "per_day") -> Dict[str, Any]:
        """
        Get all analysis data at once.
        
        Args:
            unit: Time unit for summary table
        
        Returns:
            Dict with all analysis data
        """
        return {
            'summary': self.get_summary_table(unit),
            'presence_analysis': self.get_presence_analysis(),
            'hours_by_position': self.get_hours_by_position(),
            'headcount_over_time': self.get_headcount_over_time(),
            'daily_hours_trend': self.get_daily_hours_trend()
        }
    
    @staticmethod
    def _get_unit_multiplier(unit: str) -> float:
        """Get multiplier for unit conversion."""
        multipliers = {
            'per_day': 1.0,
            'per_hour': 1.0 / 8.0,
            'per_week': 7.0,
            'per_month': 30.0
        }
        return multipliers.get(unit, 1.0)