"""
=============================================================================
KPI (Key Performance Indicators) Analysis Module
=============================================================================

Provides executive-level KPIs including:
- Project health score
- CPI and SPI metrics
- Budget burn rate
- Days to completion
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_
from collections import defaultdict


# Bilingual recommendations
KPI_TRANSLATIONS = {
    'en': {
        'progress_declining': 'Progress velocity is declining - investigate causes',
        'cost_below_target': 'Cost performance is below target - review spending',
        'schedule_behind': 'Schedule performance is behind - consider acceleration',
        'safety_attention': 'Safety compliance needs attention',
    },
    'fa': {
        'progress_declining': 'سرعت پیشرفت در حال کاهش است - علل را بررسی کنید',
        'cost_below_target': 'عملکرد هزینه زیر هدف است - هزینه‌ها را بررسی کنید',
        'schedule_behind': 'عملکرد زمان‌بندی عقب است - شتاب‌دهی را در نظر بگیرید',
        'safety_attention': 'انطباق ایمنی نیاز به توجه دارد',
    }
}


class KPIAnalysis:
    """Calculate executive-level KPIs."""
    
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
        
        self.project_info = self.project_config.get('Project_Info', {})
    
    def get_project_health_score(self):
        """
        Calculate overall project health score (0-100).
        
        Returns:
            dict: {
                'overall_score': int,
                'grade': str,
                'components': dict,
                'recommendations': list
            }
        """
        from analysis.physical_progress import PhysicalProgressAnalysis
        from analysis.financial import FinancialAnalysis
        from analysis.schedule import ScheduleAnalysis
        from analysis.safety import SafetyAnalysis
        
        # Get component scores
        scores = {}
        recommendations = []
        trans = KPI_TRANSLATIONS.get(self.lang, KPI_TRANSLATIONS['en'])
        
        # Progress Score (25%)
        try:
            progress = PhysicalProgressAnalysis(self.db, self.project_id, self.project_config)
            overall = progress.get_overall_progress()
            velocity = progress.get_progress_velocity()
            
            progress_score = min(overall['weighted_progress'], 100)
            if velocity['trend'] == 'increasing':
                progress_score = min(progress_score + 10, 100)
            elif velocity['trend'] == 'decreasing':
                progress_score = max(progress_score - 10, 0)
                recommendations.append(trans['progress_declining'])
            
            scores['progress'] = {'score': progress_score, 'weight': 0.25}
        except Exception as e:
            scores['progress'] = {'score': 50, 'weight': 0.25}  # Default
        
        # Financial Score (25%)
        try:
            financial = FinancialAnalysis(self.db, self.project_id, self.project_config)
            evm = financial.get_evm_analysis()
            
            cpi = evm.get('CPI', 1)
            if cpi >= 1:
                financial_score = min(100, 80 + (cpi - 1) * 100)
            else:
                financial_score = max(0, cpi * 80)
            
            if cpi < 0.9:
                recommendations.append(trans['cost_below_target'])
            
            scores['financial'] = {'score': financial_score, 'weight': 0.25}
        except Exception as e:
            scores['financial'] = {'score': 50, 'weight': 0.25}
        
        # Schedule Score (25%)
        try:
            schedule = ScheduleAnalysis(self.db, self.project_id, self.project_config)
            variance = schedule.get_schedule_variance()
            
            spi = variance.get('spi', 1)
            if spi >= 1:
                schedule_score = min(100, 80 + (spi - 1) * 100)
            else:
                schedule_score = max(0, spi * 80)
            
            if spi < 0.9:
                recommendations.append(trans['schedule_behind'])
            
            scores['schedule'] = {'score': schedule_score, 'weight': 0.25}
        except Exception as e:
            scores['schedule'] = {'score': 50, 'weight': 0.25}
        
        # Safety Score (25%)
        try:
            safety = SafetyAnalysis(self.db, self.project_id, self.project_config)
            compliance = safety.get_inspection_compliance()
            days_safe = safety.get_days_without_incident()
            
            safety_score = compliance.get('compliance_rate', 100)
            
            # Bonus for continuous safe days
            current_streak = days_safe.get('current_streak', 0)
            if current_streak >= 30:
                safety_score = min(100, safety_score + 10)
            
            if safety_score < 90:
                recommendations.append(trans['safety_attention'])
            
            scores['safety'] = {'score': safety_score, 'weight': 0.25}
        except Exception as e:
            scores['safety'] = {'score': 100, 'weight': 0.25}
        
        # Calculate weighted overall score
        overall_score = sum(
            component['score'] * component['weight']
            for component in scores.values()
        )
        
        # Determine grade
        if overall_score >= 90:
            grade = 'A'
        elif overall_score >= 80:
            grade = 'B'
        elif overall_score >= 70:
            grade = 'C'
        elif overall_score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'overall_score': round(overall_score, 1),
            'grade': grade,
            'components': scores,
            'recommendations': recommendations[:5]  # Top 5
        }
    
    def get_cpi_spi_metrics(self):
        """
        Get detailed CPI and SPI metrics with trends.
        
        Returns:
            dict: {
                'current': {cpi, spi, interpretation},
                'trend': list,
                'forecast': dict
            }
        """
        from analysis.financial import FinancialAnalysis
        from analysis.schedule import ScheduleAnalysis
        
        # Get current metrics
        financial = FinancialAnalysis(self.db, self.project_id, self.project_config)
        schedule = ScheduleAnalysis(self.db, self.project_id, self.project_config)
        
        evm = financial.get_evm_analysis()
        variance = schedule.get_schedule_variance()
        
        cpi = evm.get('CPI', 1)
        spi = variance.get('spi', 1)
        
        # Interpretation
        if cpi >= 1 and spi >= 1:
            interpretation = 'excellent'
            status_message = 'Project is under budget and ahead of schedule'
        elif cpi >= 1 and spi < 1:
            interpretation = 'good_cost_bad_schedule'
            status_message = 'Under budget but behind schedule'
        elif cpi < 1 and spi >= 1:
            interpretation = 'bad_cost_good_schedule'
            status_message = 'Over budget but ahead of schedule'
        else:
            interpretation = 'needs_attention'
            status_message = 'Both cost and schedule need attention'
        
        # Combined efficiency index
        composite = (cpi * spi) ** 0.5  # Geometric mean
        
        return {
            'current': {
                'cpi': round(cpi, 3),
                'spi': round(spi, 3),
                'composite': round(composite, 3),
                'interpretation': interpretation,
                'status_message': status_message
            },
            'evm_details': {
                'BAC': evm.get('BAC', 0),
                'EV': evm.get('EV', 0),
                'AC': evm.get('AC', 0),
                'PV': evm.get('PV', 0),
                'SV': evm.get('SV', 0),
                'CV': evm.get('CV', 0)
            },
            'forecast': {
                'EAC': evm.get('EAC', 0),
                'ETC': evm.get('ETC', 0),
                'VAC': evm.get('VAC', 0)
            }
        }
    
    def get_burn_rate(self):
        """
        Calculate budget burn rate and projections.
        
        Returns:
            dict: {
                'daily_burn': float,
                'weekly_burn': float,
                'monthly_burn': float,
                'percent_burned': float,
                'days_until_empty': int,
                'projected_overrun': float
            }
        """
        from analysis.financial import FinancialAnalysis
        from models.daily_form import DailyFormSubmission
        
        # Get budget info
        financial = FinancialAnalysis(self.db, self.project_id, self.project_config)
        budget_actual = financial.get_budget_vs_actual()
        
        total_budget = budget_actual['budget']['total'] or 1
        total_spent = budget_actual['actual']['total']
        
        # Get working days
        working_days = self.db.session.query(
            func.count(func.distinct(DailyFormSubmission.form_date))
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).scalar() or 1
        
        # Calculate burn rates
        daily_burn = total_spent / working_days
        weekly_burn = daily_burn * 7
        monthly_burn = daily_burn * 30
        
        percent_burned = (total_spent / total_budget * 100)
        remaining = total_budget - total_spent
        
        # Days until budget empty (at current rate)
        days_until_empty = remaining / daily_burn if daily_burn > 0 else float('inf')
        
        # Get progress to estimate overrun
        from analysis.physical_progress import PhysicalProgressAnalysis
        progress = PhysicalProgressAnalysis(self.db, self.project_id, self.project_config)
        overall = progress.get_overall_progress()
        
        progress_percent = overall['weighted_progress'] or 1
        
        # Project total cost at completion
        if progress_percent > 0:
            projected_total = (total_spent / progress_percent) * 100
            projected_overrun = projected_total - total_budget
        else:
            projected_total = total_budget
            projected_overrun = 0
        
        return {
            'total_budget': total_budget,
            'total_spent': total_spent,
            'remaining': remaining,
            'daily_burn': daily_burn,
            'weekly_burn': weekly_burn,
            'monthly_burn': monthly_burn,
            'percent_burned': round(percent_burned, 2),
            'days_until_empty': int(days_until_empty) if days_until_empty != float('inf') else None,
            'projected_total': projected_total,
            'projected_overrun': projected_overrun,
            'status': 'on_budget' if projected_overrun <= 0 else ('at_risk' if projected_overrun <= total_budget * 0.1 else 'over_budget')
        }
    
    def get_days_to_completion(self):
        """
        Calculate estimated days to project completion.
        
        Returns:
            dict: {
                'estimated_days': int,
                'estimated_date': str,
                'confidence': str,
                'scenarios': dict
            }
        """
        from analysis.physical_progress import PhysicalProgressAnalysis
        from analysis.schedule import ScheduleAnalysis
        
        progress = PhysicalProgressAnalysis(self.db, self.project_id, self.project_config)
        schedule = ScheduleAnalysis(self.db, self.project_id, self.project_config)
        
        overall = progress.get_overall_progress()
        velocity = progress.get_progress_velocity()
        working_days = schedule.get_working_days_analysis()
        
        # Current progress
        current_progress = overall['weighted_progress']
        remaining_percent = 100 - current_progress
        
        # Velocity metrics
        daily_avg = velocity.get('daily_average', 0)
        last_7_avg = velocity.get('last_7_days', 0)
        last_30_avg = velocity.get('last_30_days', 0)
        
        # Working day efficiency
        efficiency = working_days.get('efficiency_rate', 70) / 100
        
        # Calculate scenarios
        scenarios = {}
        
        # Optimistic (using best recent velocity)
        best_velocity = max(daily_avg, last_7_avg, last_30_avg, 0.001)
        if overall['total_planned_value'] > 0:
            remaining_value = overall['total_planned_value'] - overall['total_actual_value']
            optimistic_days = remaining_value / (best_velocity / efficiency) if best_velocity > 0 else 0
        else:
            optimistic_days = remaining_percent / (best_velocity * 100) if best_velocity > 0 else 0
        
        scenarios['optimistic'] = {
            'days': int(optimistic_days),
            'date': (datetime.now().date() + timedelta(days=int(optimistic_days))).isoformat()
        }
        
        # Most likely (using average velocity)
        likely_days = optimistic_days * 1.2  # 20% buffer
        scenarios['likely'] = {
            'days': int(likely_days),
            'date': (datetime.now().date() + timedelta(days=int(likely_days))).isoformat()
        }
        
        # Pessimistic (using slowest velocity with buffer)
        slowest_velocity = min(v for v in [daily_avg, last_7_avg, last_30_avg] if v > 0) if any(v > 0 for v in [daily_avg, last_7_avg, last_30_avg]) else 0.001
        if overall['total_planned_value'] > 0:
            pessimistic_days = remaining_value / (slowest_velocity * efficiency) if slowest_velocity > 0 else likely_days * 1.5
        else:
            pessimistic_days = likely_days * 1.5
        
        scenarios['pessimistic'] = {
            'days': int(pessimistic_days),
            'date': (datetime.now().date() + timedelta(days=int(pessimistic_days))).isoformat()
        }
        
        # Determine confidence
        spread = pessimistic_days - optimistic_days
        if velocity['trend'] == 'stable' and spread < likely_days * 0.3:
            confidence = 'high'
        elif velocity['trend'] == 'increasing':
            confidence = 'medium_high'
        elif velocity['trend'] == 'decreasing':
            confidence = 'low'
        else:
            confidence = 'medium'
        
        return {
            'estimated_days': int(likely_days),
            'estimated_date': scenarios['likely']['date'],
            'confidence': confidence,
            'current_progress': current_progress,
            'scenarios': scenarios,
            'velocity_info': {
                'daily_average': daily_avg,
                'recent_7_day': last_7_avg,
                'trend': velocity['trend']
            }
        }
    
    def get_summary(self):
        """
        Get complete KPI summary.
        
        Returns:
            dict: Complete KPI summary for executive dashboard
        """
        return {
            'health_score': self.get_project_health_score(),
            'performance_indices': self.get_cpi_spi_metrics(),
            'burn_rate': self.get_burn_rate(),
            'completion': self.get_days_to_completion()
        }
