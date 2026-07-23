"""
=============================================================================
Financial Analysis Module
=============================================================================

Provides financial analysis including:
- Daily cost breakdown
- Monthly financial breakdown
- Budget vs actual comparison
- Cost per activity
- Earned Value Management (EVM)
- Cost forecasting
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_
from collections import defaultdict
import calendar


class FinancialAnalysis:
    """Analyze financial aspects of the project."""
    
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
        
        # Get rates from config
        self.hr_rates = self.project_config.get('Human_Resources_Rates', {})
        self.equipment_costs = self.project_config.get('Equipment_Costs', {})
        self.material_prices = self.project_config.get('Material_Prices', {})
        self.activity_budget = self.project_config.get('Activity_Budget', {})
        self.project_info = self.project_config.get('Project_Info', {})
    
    def get_daily_cost_breakdown(self, date=None):
        """
        Get cost breakdown for a specific date.
        
        Args:
            date: Date to analyze (defaults to most recent form)
            
        Returns:
            dict: {
                'date': str,
                'labor_cost': float,
                'equipment_cost': float,
                'material_cost': float,
                'activity_cost': float,
                'total_cost': float,
                'details': {}
            }
        """
        from models.daily_form import DailyFormSubmission, HumanResource, ToolEquipment, IncomingMaterial, ConstructionOperation
        
        # Get the form
        query = self.db.session.query(DailyFormSubmission).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        )
        
        if date:
            form = query.filter(DailyFormSubmission.form_date == date).first()
        else:
            form = query.order_by(DailyFormSubmission.form_date.desc()).first()
        
        if not form:
            return {
                'date': date.isoformat() if date else 'N/A',
                'labor_cost': 0,
                'equipment_cost': 0,
                'material_cost': 0,
                'activity_cost': 0,
                'total_cost': 0,
                'details': {'labor': [], 'equipment': [], 'materials': [], 'activities': []}
            }
        
        # Calculate labor cost
        labor_details = []
        labor_cost = 0
        for hr in form.human_resources:
            hours = hr.working_hours or 8
            rate = self.hr_rates.get(hr.post, {}).get('hourly_rate', 0)
            cost = hours * rate * hr.count
            labor_cost += cost
            labor_details.append({
                'role': hr.post,
                'count': hr.count,
                'hours': hours,
                'rate': rate,
                'cost': cost
            })
        
        # Calculate equipment cost
        equipment_details = []
        equipment_cost = 0
        for eq in form.tools_equipments:
            hours = eq.working_hours or 8
            rate = self.equipment_costs.get(eq.equipment_type, {}).get('hourly_rate', 0)
            cost = hours * rate * eq.count_active
            equipment_cost += cost
            equipment_details.append({
                'type': eq.equipment_type,
                'count': eq.count_active,
                'hours': hours,
                'rate': rate,
                'cost': cost
            })
        
        # Calculate material cost
        material_details = []
        material_cost = 0
        for mat in form.incoming_materials:
            price = self.material_prices.get(mat.material_type, {}).get('price_per_unit', 0)
            cost = (mat.incoming_amount or 0) * price
            material_cost += cost
            material_details.append({
                'type': mat.material_type,
                'quantity': mat.incoming_amount,
                'price': price,
                'cost': cost
            })
        
        # Calculate activity cost
        activity_details = []
        activity_cost = 0
        for op in form.construction_operations:
            budget_info = self.activity_budget.get(op.operation_type, {})
            price = budget_info.get('price_per_unit', 0)
            cost = (op.amount or 0) * price
            activity_cost += cost
            activity_details.append({
                'type': op.operation_type,
                'amount': op.amount,
                'unit': op.unit,
                'price': price,
                'cost': cost
            })
        
        return {
            'date': form.form_date.isoformat(),
            'labor_cost': labor_cost,
            'equipment_cost': equipment_cost,
            'material_cost': material_cost,
            'activity_cost': activity_cost,
            'total_cost': labor_cost + equipment_cost + material_cost + activity_cost,
            'details': {
                'labor': labor_details,
                'equipment': equipment_details,
                'materials': material_details,
                'activities': activity_details
            }
        }
    
    def get_monthly_breakdown(self, year=None, month=None):
        """
        Get monthly financial breakdown.
        
        Args:
            year: Year to analyze (defaults to current)
            month: Month to analyze (defaults to current)
            
        Returns:
            dict: Monthly breakdown with daily totals
        """
        from models.daily_form import DailyFormSubmission
        
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        # Get date range
        first_day = datetime(year, month, 1).date()
        last_day = datetime(year, month, calendar.monthrange(year, month)[1]).date()
        
        # Get all forms for the month
        forms = self.db.session.query(DailyFormSubmission).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved',
            DailyFormSubmission.form_date >= first_day,
            DailyFormSubmission.form_date <= last_day
        ).order_by(DailyFormSubmission.form_date).all()
        
        daily_costs = []
        total_labor = 0
        total_equipment = 0
        total_material = 0
        total_activity = 0
        
        # Process each form
        for form in forms:
            cost = self.get_daily_cost_breakdown(form.form_date)
            daily_costs.append({
                'date': cost['date'],
                'labor': cost['labor_cost'],
                'equipment': cost['equipment_cost'],
                'material': cost['material_cost'],
                'activity': cost['activity_cost'],
                'total': cost['total_cost']
            })
            total_labor += cost['labor_cost']
            total_equipment += cost['equipment_cost']
            total_material += cost['material_cost']
            total_activity += cost['activity_cost']
        
        return {
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'working_days': len(forms),
            'daily_costs': daily_costs,
            'totals': {
                'labor': total_labor,
                'equipment': total_equipment,
                'material': total_material,
                'activity': total_activity,
                'total': total_labor + total_equipment + total_material + total_activity
            },
            'averages': {
                'daily_cost': (total_labor + total_equipment + total_material + total_activity) / len(forms) if forms else 0
            }
        }
    
    def get_budget_vs_actual(self):
        """
        Compare budget vs actual spending.
        
        Returns:
            dict: Budget vs actual comparison
        """
        from models.daily_form import DailyFormSubmission, ConstructionOperation, HumanResource, ToolEquipment, IncomingMaterial
        
        # Get total budget from config
        total_budget = self.project_info.get('budget', 0)
        
        # Calculate actual spending by category
        forms = self.db.session.query(DailyFormSubmission).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).all()
        
        actual_labor = 0
        actual_equipment = 0
        actual_material = 0
        actual_activity = 0
        
        for form in forms:
            cost = self.get_daily_cost_breakdown(form.form_date)
            actual_labor += cost['labor_cost']
            actual_equipment += cost['equipment_cost']
            actual_material += cost['material_cost']
            actual_activity += cost['activity_cost']
        
        total_actual = actual_labor + actual_equipment + actual_material + actual_activity
        
        # Calculate planned values
        planned_activity = sum(
            info.get('planned_amount', 0) * info.get('price_per_unit', 0)
            for info in self.activity_budget.values()
        )
        
        planned_equipment = sum(
            info.get('hourly_rate', 0) * info.get('planned_quantity', 0)
            for info in self.equipment_costs.values()
        )
        
        planned_material = sum(
            info.get('price_per_unit', 0) * info.get('planned_total', 0)
            for info in self.material_prices.values()
        )
        
        return {
            'budget': {
                'total': total_budget,
                'activity': planned_activity,
                'equipment': planned_equipment,
                'material': planned_material
            },
            'actual': {
                'total': total_actual,
                'labor': actual_labor,
                'equipment': actual_equipment,
                'material': actual_material,
                'activity': actual_activity
            },
            'variance': {
                'total': total_budget - total_actual,
                'percent': ((total_budget - total_actual) / total_budget * 100) if total_budget > 0 else 0
            },
            'burn_rate': {
                'percent': (total_actual / total_budget * 100) if total_budget > 0 else 0,
                'remaining': total_budget - total_actual
            }
        }
    
    def get_cost_per_activity(self):
        """
        Get cost analysis per activity type.
        
        Returns:
            dict: {activity: {actual, planned, variance, efficiency}}
        """
        from models.daily_form import DailyFormSubmission, ConstructionOperation
        
        # Get all operations
        operations = self.db.session.query(
            ConstructionOperation.operation_type,
            func.sum(ConstructionOperation.amount).label('total_amount')
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).group_by(
            ConstructionOperation.operation_type
        ).all()
        
        result = {}
        
        # Initialize with planned activities
        for activity, budget_info in self.activity_budget.items():
            planned_amount = budget_info.get('planned_amount', 0)
            price_per_unit = budget_info.get('price_per_unit', 0)
            planned_cost = planned_amount * price_per_unit
            
            result[activity] = {
                'planned_amount': planned_amount,
                'actual_amount': 0,
                'price_per_unit': price_per_unit,
                'planned_cost': planned_cost,
                'actual_cost': 0,
                'variance': planned_cost,
                'variance_percent': 0,
                'cost_efficiency': 0
            }
        
        # Update with actual data
        for op in operations:
            activity = op.operation_type
            actual_amount = float(op.total_amount or 0)
            
            if activity in result:
                price = result[activity]['price_per_unit']
                actual_cost = actual_amount * price
                planned_cost = result[activity]['planned_cost']
                
                result[activity]['actual_amount'] = actual_amount
                result[activity]['actual_cost'] = actual_cost
                result[activity]['variance'] = planned_cost - actual_cost
                
                if planned_cost > 0:
                    result[activity]['variance_percent'] = ((planned_cost - actual_cost) / planned_cost) * 100
                    result[activity]['cost_efficiency'] = (actual_cost / planned_cost) * 100
        
        return result
    
    def get_evm_analysis(self):
        """
        Calculate Earned Value Management metrics.
        
        Returns:
            dict: {
                'PV': Planned Value,
                'EV': Earned Value,
                'AC': Actual Cost,
                'SV': Schedule Variance,
                'CV': Cost Variance,
                'SPI': Schedule Performance Index,
                'CPI': Cost Performance Index,
                'EAC': Estimate At Completion,
                'ETC': Estimate To Complete,
                'VAC': Variance At Completion,
                'TCPI': To Complete Performance Index
            }
        """
        budget_actual = self.get_budget_vs_actual()
        cost_per_activity = self.get_cost_per_activity()
        
        # Budget At Completion (BAC)
        BAC = budget_actual['budget']['total'] or 1
        
        # Actual Cost (AC)
        AC = budget_actual['actual']['total']
        
        # Planned Value (PV) - What we planned to spend by now
        # This requires schedule data; estimate as percentage of time passed
        project_start = self.project_info.get('start_date')
        project_end = self.project_info.get('end_date')
        
        if project_start and project_end:
            try:
                start = datetime.strptime(project_start, '%Y-%m-%d').date()
                end = datetime.strptime(project_end, '%Y-%m-%d').date()
                today = datetime.now().date()
                
                total_days = (end - start).days or 1
                elapsed_days = (today - start).days
                time_percent = min(max(elapsed_days / total_days, 0), 1)
                
                PV = BAC * time_percent
            except:
                PV = BAC * 0.5  # Default to 50%
        else:
            PV = BAC * 0.5  # Default to 50%
        
        # Earned Value (EV) - Value of work actually completed
        EV = 0
        for activity_data in cost_per_activity.values():
            if activity_data['planned_amount'] > 0:
                completion = activity_data['actual_amount'] / activity_data['planned_amount']
                EV += activity_data['planned_cost'] * min(completion, 1)
        
        # Calculate variances
        SV = EV - PV  # Schedule Variance
        CV = EV - AC  # Cost Variance
        
        # Calculate indices
        SPI = EV / PV if PV > 0 else 0  # Schedule Performance Index
        CPI = EV / AC if AC > 0 else 0  # Cost Performance Index
        
        # Forecasting
        EAC = BAC / CPI if CPI > 0 else BAC  # Estimate At Completion
        ETC = EAC - AC  # Estimate To Complete
        VAC = BAC - EAC  # Variance At Completion
        
        # To Complete Performance Index
        TCPI = (BAC - EV) / (BAC - AC) if (BAC - AC) > 0 else 0
        
        return {
            'BAC': BAC,
            'PV': PV,
            'EV': EV,
            'AC': AC,
            'SV': SV,
            'CV': CV,
            'SPI': round(SPI, 3),
            'CPI': round(CPI, 3),
            'EAC': EAC,
            'ETC': ETC,
            'VAC': VAC,
            'TCPI': round(TCPI, 3),
            'interpretation': {
                'schedule': 'ahead' if SPI > 1 else ('behind' if SPI < 1 else 'on track'),
                'cost': 'under budget' if CPI > 1 else ('over budget' if CPI < 1 else 'on budget'),
                'health': 'good' if SPI >= 0.9 and CPI >= 0.9 else ('warning' if SPI >= 0.8 and CPI >= 0.8 else 'critical')
            }
        }
    
    def get_cost_forecast(self, months_ahead=6):
        """
        Forecast costs for upcoming months.
        
        Args:
            months_ahead: Number of months to forecast
            
        Returns:
            list: [{month, forecasted_cost, cumulative}]
        """
        from models.daily_form import DailyFormSubmission
        
        # Get historical monthly data
        forms = self.db.session.query(
            func.strftime('%Y-%m', DailyFormSubmission.form_date).label('month'),
            func.count(DailyFormSubmission.id).label('form_count')
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).group_by(
            func.strftime('%Y-%m', DailyFormSubmission.form_date)
        ).all()
        
        # Calculate average monthly cost
        monthly_costs = []
        for form_month in forms:
            year, month = map(int, form_month.month.split('-'))
            breakdown = self.get_monthly_breakdown(year, month)
            monthly_costs.append(breakdown['totals']['total'])
        
        avg_monthly_cost = sum(monthly_costs) / len(monthly_costs) if monthly_costs else 0
        
        # Get EVM for better forecasting
        evm = self.get_evm_analysis()
        cpi = evm['CPI'] or 1
        
        # Adjusted forecast based on CPI
        adjusted_monthly = avg_monthly_cost / cpi if cpi > 0 else avg_monthly_cost
        
        # Generate forecast
        budget_actual = self.get_budget_vs_actual()
        current_spent = budget_actual['actual']['total']
        remaining = budget_actual['budget']['total'] - current_spent
        
        forecast = []
        cumulative = current_spent
        current_date = datetime.now()
        
        for i in range(1, months_ahead + 1):
            next_month = current_date + timedelta(days=30 * i)
            forecasted = min(adjusted_monthly, remaining)
            cumulative += forecasted
            remaining -= forecasted
            
            forecast.append({
                'month': next_month.strftime('%Y-%m'),
                'month_name': next_month.strftime('%B %Y'),
                'forecasted_cost': forecasted,
                'cumulative': cumulative,
                'remaining_budget': max(remaining, 0)
            })
        
        return forecast
    
    def get_summary(self):
        """
        Get complete financial summary.
        
        Returns:
            dict: Complete financial summary
        """
        return {
            'budget_vs_actual': self.get_budget_vs_actual(),
            'cost_per_activity': self.get_cost_per_activity(),
            'evm': self.get_evm_analysis(),
            'forecast': self.get_cost_forecast(3)
        }
