"""
=============================================================================
Resource Utilization Analysis Module
=============================================================================

Provides analysis of resource utilization including:
- Equipment utilization rates
- Equipment downtime analysis
- Planned vs actual resource usage
- Man-hours tracking and analysis
- Human resource cost analysis
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_
from collections import defaultdict


class ResourceAnalysis:
    """Analyze resource utilization."""
    
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
        
        self.hr_rates = self.project_config.get('Human_Resources_Rates', {})
        self.equipment_costs = self.project_config.get('Equipment_Costs', {})
        self.hr_config = self.project_config.get('Human_Resources', {})
        self.equipment_config = self.project_config.get('Tools_And_Equipments', {})
    
    def _get_equipment_rate(self, equipment_type, equipment_model=None):
        """Get hourly rate for equipment, handling nested model structure."""
        eq_config = self.equipment_costs.get(equipment_type, {})
        if not eq_config:
            return 0
        if 'hourly_rate' in eq_config:
            return eq_config.get('hourly_rate', 0)
        model_key = equipment_model or 'default'
        model_config = eq_config.get(model_key, eq_config.get('default', {}))
        if isinstance(model_config, dict):
            return model_config.get('hourly_rate', 0)
        return 0
    
    def _get_equipment_planned_qty(self, equipment_type, equipment_model=None):
        """Get planned quantity for equipment, handling nested model structure."""
        eq_config = self.equipment_costs.get(equipment_type, {})
        if not eq_config:
            return 0
        if 'planned_quantity' in eq_config:
            return eq_config.get('planned_quantity', 0)
        model_key = equipment_model or 'default'
        model_config = eq_config.get(model_key, eq_config.get('default', {}))
        if isinstance(model_config, dict):
            return model_config.get('planned_quantity', 0)
        return 0
    
    def get_equipment_utilization(self):
        """
        Calculate equipment utilization rates.
        
        Returns:
            dict: {equipment_type: {
                'total_hours': float,
                'total_count': int,
                'avg_hours_per_unit': float,
                'utilization_rate': float,
                'planned_quantity': int,
                'days_used': int
            }}
        """
        from models.daily_form import DailyFormSubmission, ToolEquipment
        
        # Get equipment usage data
        equipment_data = self.db.session.query(
            ToolEquipment.equipment_type,
            func.sum(ToolEquipment.working_hours * ToolEquipment.count_active).label('total_hours'),
            func.sum(ToolEquipment.count_active).label('total_count'),
            func.count(func.distinct(DailyFormSubmission.form_date)).label('days_used')
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).group_by(
            ToolEquipment.equipment_type
        ).all()
        
        # Get total working days
        total_days = self.db.session.query(
            func.count(func.distinct(DailyFormSubmission.form_date))
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).scalar() or 1
        
        result = {}
        
        # Initialize with configured equipment
        for eq_type, models_or_count in self.equipment_config.items():
            planned_qty = self._get_equipment_planned_qty(eq_type)
            result[eq_type] = {
                'total_hours': 0,
                'total_count': 0,
                'avg_hours_per_unit': 0,
                'utilization_rate': 0,
                'planned_quantity': planned_qty,
                'days_used': 0,
                'potential_hours': planned_qty * 8 * total_days if planned_qty else 0
            }
        
        # Update with actual data
        for eq in equipment_data:
            eq_type = eq.equipment_type
            total_hours = float(eq.total_hours or 0)
            total_count = int(eq.total_count or 0)
            days_used = int(eq.days_used or 0)
            
            if eq_type not in result:
                result[eq_type] = {
                    'planned_quantity': 0,
                    'potential_hours': 0
                }
            
            avg_hours = total_hours / total_count if total_count > 0 else 0
            
            # Calculate utilization rate
            # Potential = planned_quantity * 8 hours * working_days
            potential_hours = result[eq_type]['potential_hours']
            utilization = (total_hours / potential_hours * 100) if potential_hours > 0 else 0
            
            result[eq_type].update({
                'total_hours': total_hours,
                'total_count': total_count,
                'avg_hours_per_unit': avg_hours,
                'utilization_rate': min(utilization, 100),
                'days_used': days_used
            })
        
        return result
    
    def get_equipment_downtime(self):
        """
        Analyze equipment downtime patterns.
        
        Returns:
            dict: {equipment_type: {
                'total_downtime_days': int,
                'downtime_reasons': dict,
                'average_downtime': float,
                'availability_rate': float
            }}
        """
        from models.daily_form import DailyFormSubmission, ToolEquipment
        
        utilization = self.get_equipment_utilization()
        
        # Get all working days
        total_days = self.db.session.query(
            func.count(func.distinct(DailyFormSubmission.form_date))
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).scalar() or 1
        
        result = {}
        
        for eq_type, data in utilization.items():
            days_used = data['days_used']
            downtime_days = total_days - days_used
            
            result[eq_type] = {
                'total_days': total_days,
                'days_used': days_used,
                'downtime_days': downtime_days,
                'availability_rate': (days_used / total_days * 100) if total_days > 0 else 0,
                'utilization_rate': data['utilization_rate']
            }
        
        return result
    
    def get_planned_vs_actual_resources(self):
        """
        Compare planned vs actual resource usage.
        
        Returns:
            dict: {
                'equipment': {type: {planned, actual, variance}},
                'human_resources': {role: {planned, actual, variance}}
            }
        """
        from models.daily_form import DailyFormSubmission, ToolEquipment, HumanResource
        
        # Equipment comparison
        equipment_actual = self.db.session.query(
            ToolEquipment.equipment_type,
            func.sum(ToolEquipment.working_hours * ToolEquipment.count_active).label('total_hours')
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).group_by(
            ToolEquipment.equipment_type
        ).all()
        
        equipment_result = {}
        for eq_type, eq_models in self.equipment_costs.items():
            # Sum planned quantities across models
            planned_hours = 0
            if isinstance(eq_models, dict):
                if 'planned_quantity' in eq_models:
                    planned_hours = eq_models.get('planned_quantity', 0)
                else:
                    for model_key, model_config in eq_models.items():
                        if isinstance(model_config, dict):
                            planned_hours += model_config.get('planned_quantity', 0)
            
            actual_hours = 0
            
            # Find actual
            for eq in equipment_actual:
                if eq.equipment_type == eq_type:
                    actual_hours = float(eq.total_hours or 0)
                    break
            
            variance = actual_hours - planned_hours
            
            equipment_result[eq_type] = {
                'planned_hours': planned_hours,
                'actual_hours': actual_hours,
                'variance': variance,
                'variance_percent': (variance / planned_hours * 100) if planned_hours > 0 else 0,
                'status': 'over' if variance > 0 else ('under' if variance < 0 else 'on target')
            }
        
        # Human resources comparison
        hr_actual = self.db.session.query(
            HumanResource.post,
            func.sum(HumanResource.working_hours * HumanResource.count).label('total_hours'),
            func.sum(HumanResource.count).label('total_count')
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).group_by(
            HumanResource.post
        ).all()
        
        hr_result = {}
        # Handle both list and dict HR config
        hr_config_items = []
        if isinstance(self.hr_config, list):
            hr_config_items = [(role, 1) for role in self.hr_config]
        elif isinstance(self.hr_config, dict):
            hr_config_items = list(self.hr_config.items())
        
        for role, count in hr_config_items:
            actual_hours = 0
            actual_count = 0
            
            for hr in hr_actual:
                if hr.post == role:
                    actual_hours = float(hr.total_hours or 0)
                    actual_count = int(hr.total_count or 0)
                    break
            
            hr_result[role] = {
                'planned_count': count,
                'actual_total': actual_count,
                'actual_hours': actual_hours,
                'avg_hours_per_person': actual_hours / actual_count if actual_count > 0 else 0
            }
        
        return {
            'equipment': equipment_result,
            'human_resources': hr_result
        }
    
    def get_manhours_analysis(self):
        """
        Analyze man-hours tracking.
        
        Returns:
            dict: {
                'total_manhours': float,
                'by_role': dict,
                'daily_average': float,
                'trend': list,
                'productivity_index': float
            }
        """
        from models.daily_form import DailyFormSubmission, HumanResource, ConstructionOperation
        
        # Get man-hours by role
        manhours_by_role = self.db.session.query(
            HumanResource.post,
            func.sum(HumanResource.working_hours * HumanResource.count).label('total_hours'),
            func.sum(HumanResource.count).label('total_count'),
            func.count(func.distinct(DailyFormSubmission.form_date)).label('days_worked')
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).group_by(
            HumanResource.post
        ).all()
        
        by_role = {}
        total_manhours = 0
        
        for hr in manhours_by_role:
            hours = float(hr.total_hours or 0)
            count = int(hr.total_count or 0)
            days = int(hr.days_worked or 0)
            
            by_role[hr.post] = {
                'total_hours': hours,
                'total_headcount': count,
                'days_worked': days,
                'avg_daily_hours': hours / days if days > 0 else 0,
                'hourly_rate': self.hr_rates.get(hr.post, {}).get('hourly_rate', 0)
            }
            total_manhours += hours
        
        # Get daily trend
        daily_trend = self.db.session.query(
            DailyFormSubmission.form_date,
            func.sum(HumanResource.working_hours * HumanResource.count).label('manhours')
        ).join(
            HumanResource
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).group_by(
            DailyFormSubmission.form_date
        ).order_by(
            DailyFormSubmission.form_date
        ).all()
        
        trend = [
            {
                'date': d.form_date.isoformat(),
                'manhours': float(d.manhours or 0)
            }
            for d in daily_trend
        ]
        
        # Calculate productivity (work output per man-hour)
        total_work = self.db.session.query(
            func.sum(ConstructionOperation.amount)
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).scalar() or 0
        
        productivity_index = total_work / total_manhours if total_manhours > 0 else 0
        
        working_days = len(trend)
        daily_average = total_manhours / working_days if working_days > 0 else 0
        
        return {
            'total_manhours': total_manhours,
            'by_role': by_role,
            'daily_average': daily_average,
            'working_days': working_days,
            'trend': trend,
            'productivity_index': productivity_index
        }
    
    def get_hr_cost_analysis(self):
        """
        Analyze human resource costs.
        
        Returns:
            dict: {
                'total_cost': float,
                'by_role': dict,
                'daily_average': float,
                'cost_trend': list,
                'cost_per_work_unit': float
            }
        """
        from models.daily_form import DailyFormSubmission, HumanResource, ConstructionOperation
        
        # Get cost by role
        hr_data = self.db.session.query(
            HumanResource.post,
            DailyFormSubmission.form_date,
            func.sum(HumanResource.working_hours * HumanResource.count).label('hours')
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).group_by(
            HumanResource.post,
            DailyFormSubmission.form_date
        ).all()
        
        by_role = defaultdict(lambda: {'hours': 0, 'cost': 0, 'days': 0})
        daily_costs = defaultdict(float)
        
        for hr in hr_data:
            hours = float(hr.hours or 0)
            rate = self.hr_rates.get(hr.post, {}).get('hourly_rate', 0)
            cost = hours * rate
            
            by_role[hr.post]['hours'] += hours
            by_role[hr.post]['cost'] += cost
            by_role[hr.post]['days'] += 1
            by_role[hr.post]['hourly_rate'] = rate
            
            daily_costs[hr.form_date] += cost
        
        # Calculate totals
        total_cost = sum(r['cost'] for r in by_role.values())
        working_days = len(daily_costs)
        daily_average = total_cost / working_days if working_days > 0 else 0
        
        # Cost trend
        cost_trend = [
            {'date': date.isoformat(), 'cost': cost}
            for date, cost in sorted(daily_costs.items())
        ]
        
        # Cost per work unit
        total_work = self.db.session.query(
            func.sum(ConstructionOperation.amount)
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).scalar() or 0
        
        cost_per_work = total_cost / total_work if total_work > 0 else 0
        
        return {
            'total_cost': total_cost,
            'by_role': dict(by_role),
            'daily_average': daily_average,
            'working_days': working_days,
            'cost_trend': cost_trend,
            'cost_per_work_unit': cost_per_work
        }
    
    def get_summary(self):
        """
        Get complete resource summary.
        
        Returns:
            dict: Complete resource analysis summary
        """
        return {
            'equipment_utilization': self.get_equipment_utilization(),
            'equipment_downtime': self.get_equipment_downtime(),
            'planned_vs_actual': self.get_planned_vs_actual_resources(),
            'manhours': self.get_manhours_analysis(),
            'hr_cost': self.get_hr_cost_analysis()
        }
