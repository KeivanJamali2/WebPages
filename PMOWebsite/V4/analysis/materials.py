"""
=============================================================================
Material Management Analysis Module
=============================================================================

Provides analysis of materials including:
- Material consumption rates
- Inventory levels
- Cost spent on materials
- Supply rate analysis
- At-risk materials identification
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_
from collections import defaultdict


class MaterialAnalysis:
    """Analyze material management."""
    
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
        
        self.material_config = self.project_config.get('Incoming_Materials', {})
        self.material_prices = self.project_config.get('Material_Prices', {})
    
    def get_material_consumption(self):
        """
        Analyze material consumption rates.
        
        Returns:
            dict: {material_type: {
                'total_received': float,
                'total_used': float,
                'consumption_rate': float,
                'daily_average': float,
                'trend': list
            }}
        """
        from models.daily_form import DailyFormSubmission, IncomingMaterial
        
        # Get material data
        material_data = self.db.session.query(
            IncomingMaterial.material_type,
            DailyFormSubmission.form_date,
            func.sum(IncomingMaterial.incoming_amount).label('received'),
            func.sum(IncomingMaterial.used_amount).label('used')
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).group_by(
            IncomingMaterial.material_type,
            DailyFormSubmission.form_date
        ).order_by(
            IncomingMaterial.material_type,
            DailyFormSubmission.form_date
        ).all()
        
        # Organize by material type
        materials = defaultdict(lambda: {
            'total_received': 0,
            'total_used': 0,
            'daily_data': [],
            'days': 0
        })
        
        for mat in material_data:
            received = float(mat.received or 0)
            used = float(mat.used or 0)
            
            materials[mat.material_type]['total_received'] += received
            materials[mat.material_type]['total_used'] += used
            materials[mat.material_type]['days'] += 1
            materials[mat.material_type]['daily_data'].append({
                'date': mat.form_date.isoformat(),
                'received': received,
                'used': used
            })
        
        result = {}
        
        # Initialize with configured materials
        for mat_type, unit in self.material_config.items():
            prices = self.material_prices.get(mat_type, {})
            result[mat_type] = {
                'total_received': 0,
                'total_used': 0,
                'consumption_rate': 0,
                'daily_average': 0,
                'days': 0,
                'trend': [],
                'unit': unit,
                'price_per_unit': prices.get('price_per_unit', 0),
                'planned_total': prices.get('planned_total', 0)
            }
        
        # Update with actual data
        for mat_type, data in materials.items():
            if mat_type not in result:
                result[mat_type] = {
                    'unit': '',
                    'price_per_unit': 0,
                    'planned_total': 0
                }
            
            total_received = data['total_received']
            total_used = data['total_used']
            days = data['days']
            
            consumption_rate = (total_used / total_received * 100) if total_received > 0 else 0
            
            result[mat_type].update({
                'total_received': total_received,
                'total_used': total_used,
                'consumption_rate': consumption_rate,
                'daily_average': total_used / days if days > 0 else 0,
                'days': days,
                'trend': data['daily_data']
            })
        
        return result
    
    def get_inventory_levels(self):
        """
        Calculate current inventory levels.
        
        Returns:
            dict: {material_type: {
                'received': float,
                'used': float,
                'in_stock': float,
                'stock_days': float,
                'status': str
            }}
        """
        consumption = self.get_material_consumption()
        
        result = {}
        
        for mat_type, data in consumption.items():
            received = data['total_received']
            used = data['total_used']
            in_stock = received - used
            daily_avg = data['daily_average']
            
            # Estimate days of stock remaining
            stock_days = in_stock / daily_avg if daily_avg > 0 else float('inf')
            
            # Determine status
            if stock_days == float('inf'):
                status = 'no_usage'
            elif stock_days <= 3:
                status = 'critical'
            elif stock_days <= 7:
                status = 'low'
            elif stock_days <= 14:
                status = 'adequate'
            else:
                status = 'good'
            
            result[mat_type] = {
                'received': received,
                'used': used,
                'in_stock': max(in_stock, 0),
                'stock_days': stock_days if stock_days != float('inf') else None,
                'daily_usage_avg': daily_avg,
                'unit': data.get('unit', ''),
                'status': status
            }
        
        return result
    
    def get_material_cost_spent(self):
        """
        Analyze cost spent on materials.
        
        Returns:
            dict: {
                'total_cost': float,
                'by_material': dict,
                'planned_budget': float,
                'budget_used_percent': float,
                'cost_trend': list
            }
        """
        from models.daily_form import DailyFormSubmission, IncomingMaterial
        
        # Get material receipts with dates
        material_data = self.db.session.query(
            IncomingMaterial.material_type,
            DailyFormSubmission.form_date,
            func.sum(IncomingMaterial.incoming_amount).label('received')
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved'
        ).group_by(
            IncomingMaterial.material_type,
            DailyFormSubmission.form_date
        ).all()
        
        by_material = {}
        daily_costs = defaultdict(float)
        total_cost = 0
        
        for mat in material_data:
            price = self.material_prices.get(mat.material_type, {}).get('price_per_unit', 0)
            cost = float(mat.received or 0) * price
            
            if mat.material_type not in by_material:
                by_material[mat.material_type] = {
                    'quantity': 0,
                    'price_per_unit': price,
                    'cost': 0,
                    'planned_total': self.material_prices.get(mat.material_type, {}).get('planned_total', 0)
                }
            
            by_material[mat.material_type]['quantity'] += float(mat.received or 0)
            by_material[mat.material_type]['cost'] += cost
            daily_costs[mat.form_date] += cost
            total_cost += cost
        
        # Calculate planned budget
        planned_budget = sum(
            info.get('price_per_unit', 0) * info.get('planned_total', 0)
            for info in self.material_prices.values()
        )
        
        # Cost trend
        cost_trend = [
            {'date': date.isoformat(), 'cost': cost, 'cumulative': 0}
            for date, cost in sorted(daily_costs.items())
        ]
        
        # Calculate cumulative
        cumulative = 0
        for item in cost_trend:
            cumulative += item['cost']
            item['cumulative'] = cumulative
        
        return {
            'total_cost': total_cost,
            'by_material': by_material,
            'planned_budget': planned_budget,
            'budget_used_percent': (total_cost / planned_budget * 100) if planned_budget > 0 else 0,
            'remaining_budget': planned_budget - total_cost,
            'cost_trend': cost_trend
        }
    
    def get_supply_rate_analysis(self):
        """
        Analyze material supply rates.
        
        Returns:
            dict: {material_type: {
                'supply_rate': float (units per day),
                'consistency': float (0-100),
                'delivery_count': int,
                'avg_delivery_size': float
            }}
        """
        from models.daily_form import DailyFormSubmission, IncomingMaterial
        
        # Get delivery data
        deliveries = self.db.session.query(
            IncomingMaterial.material_type,
            DailyFormSubmission.form_date,
            func.sum(IncomingMaterial.incoming_amount).label('quantity')
        ).join(
            DailyFormSubmission
        ).filter(
            DailyFormSubmission.project_id == self.project_id,
            DailyFormSubmission.status == 'approved',
            IncomingMaterial.incoming_amount > 0
        ).group_by(
            IncomingMaterial.material_type,
            DailyFormSubmission.form_date
        ).order_by(
            IncomingMaterial.material_type,
            DailyFormSubmission.form_date
        ).all()
        
        # Organize by material
        materials = defaultdict(list)
        for d in deliveries:
            materials[d.material_type].append({
                'date': d.form_date,
                'quantity': float(d.quantity or 0)
            })
        
        result = {}
        
        for mat_type, delivery_list in materials.items():
            if len(delivery_list) == 0:
                continue
            
            total_quantity = sum(d['quantity'] for d in delivery_list)
            delivery_count = len(delivery_list)
            
            # Calculate days span
            if delivery_count > 1:
                first_date = delivery_list[0]['date']
                last_date = delivery_list[-1]['date']
                days_span = (last_date - first_date).days + 1
            else:
                days_span = 1
            
            supply_rate = total_quantity / days_span
            avg_delivery_size = total_quantity / delivery_count
            
            # Calculate consistency (coefficient of variation)
            quantities = [d['quantity'] for d in delivery_list]
            mean_qty = sum(quantities) / len(quantities)
            if mean_qty > 0 and len(quantities) > 1:
                variance = sum((q - mean_qty) ** 2 for q in quantities) / len(quantities)
                std_dev = variance ** 0.5
                cv = std_dev / mean_qty
                consistency = max(0, 100 - (cv * 100))  # Lower CV = more consistent
            else:
                consistency = 100
            
            result[mat_type] = {
                'supply_rate': supply_rate,
                'consistency': consistency,
                'delivery_count': delivery_count,
                'avg_delivery_size': avg_delivery_size,
                'total_supplied': total_quantity,
                'days_span': days_span,
                'unit': self.material_config.get(mat_type, '')
            }
        
        return result
    
    def get_at_risk_materials(self):
        """
        Identify materials that are at risk (low stock, high usage, supply issues).
        
        Returns:
            list: [{
                'material': str,
                'risk_level': str,
                'risk_factors': list,
                'recommendation': str
            }]
        """
        inventory = self.get_inventory_levels()
        supply_rates = self.get_supply_rate_analysis()
        consumption = self.get_material_consumption()
        
        at_risk = []
        
        for mat_type, inv_data in inventory.items():
            risk_factors = []
            risk_score = 0
            
            # Check stock level
            if inv_data['status'] == 'critical':
                risk_factors.append('Critical stock level (< 3 days)')
                risk_score += 3
            elif inv_data['status'] == 'low':
                risk_factors.append('Low stock level (< 7 days)')
                risk_score += 2
            
            # Check supply consistency
            supply = supply_rates.get(mat_type, {})
            if supply.get('consistency', 100) < 50:
                risk_factors.append('Inconsistent supply')
                risk_score += 2
            
            # Check usage vs supply rate
            daily_usage = inv_data.get('daily_usage_avg', 0)
            supply_rate = supply.get('supply_rate', 0)
            
            if daily_usage > 0 and supply_rate < daily_usage * 0.8:
                risk_factors.append('Supply rate below usage rate')
                risk_score += 2
            
            # Check progress vs planned
            cons_data = consumption.get(mat_type, {})
            planned = cons_data.get('planned_total', 0)
            used = cons_data.get('total_used', 0)
            
            if planned > 0 and used > planned * 0.9:
                risk_factors.append('Nearing planned quantity limit')
                risk_score += 1
            
            if risk_factors:
                # Determine risk level
                if risk_score >= 5:
                    risk_level = 'high'
                    recommendation = 'Immediate action required: Order materials urgently'
                elif risk_score >= 3:
                    risk_level = 'medium'
                    recommendation = 'Monitor closely and consider placing order'
                else:
                    risk_level = 'low'
                    recommendation = 'Keep monitoring supply levels'
                
                at_risk.append({
                    'material': mat_type,
                    'risk_level': risk_level,
                    'risk_score': risk_score,
                    'risk_factors': risk_factors,
                    'recommendation': recommendation,
                    'current_stock': inv_data['in_stock'],
                    'stock_days': inv_data['stock_days'],
                    'unit': inv_data.get('unit', '')
                })
        
        # Sort by risk score descending
        at_risk.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return at_risk
    
    def get_summary(self):
        """
        Get complete material summary.
        
        Returns:
            dict: Complete material analysis summary
        """
        return {
            'consumption': self.get_material_consumption(),
            'inventory': self.get_inventory_levels(),
            'cost': self.get_material_cost_spent(),
            'supply_rates': self.get_supply_rate_analysis(),
            'at_risk': self.get_at_risk_materials()
        }
