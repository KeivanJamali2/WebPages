"""
Tools & Equipment Analysis
===========================

Analyzes equipment data: status breakdown, working hours, utilisation rates.
"""
from typing import Dict, List, Any
from collections import defaultdict


class ToolsEquipmentAnalysis:
    """
    Analyzes tools & equipment data from daily forms.

    Provides:
    - Summary table by equipment type+model (days active/inactive/repair, hours, utilisation)
    - Status distribution for charts
    - Daily active equipment trend
    """

    def __init__(self, data_service, project_config: dict):
        self.ds = data_service
        self.config = project_config
        self.equip_data = data_service.get_tools_equipment()
        self.equip_costs = project_config.get('Equipment_Costs', {})

    # ------------------------------------------------------------------
    def get_summary_table(self, unit: str = "per_day") -> Dict[str, Any]:
        """
        One row per equipment_type + model.

        Columns: equipment_name, total_days, days_active, days_inactive,
        days_repair, active_pct, total_units_days, total_hours,
        avg_hours (unit-adjusted), planned_qty, utilisation_pct.
        """
        key_fn = lambda r: (r['equipment_type'], r.get('equipment_model') or '')

        by_equip = defaultdict(lambda: {
            'dates_active': set(),
            'dates_inactive': set(),
            'dates_repair': set(),
            'all_dates': set(),
            'total_units_days': 0,
            'total_hours': 0.0,
        })

        for rec in self.equip_data:
            k = key_fn(rec)
            date = rec['form_date']
            sit = (rec.get('situation') or '').strip()
            count = rec.get('count_active', 0)
            hours = rec.get('working_hours', 0)

            by_equip[k]['all_dates'].add(date)
            if sit == 'Active':
                by_equip[k]['dates_active'].add(date)
            elif sit == 'Under Repair':
                by_equip[k]['dates_repair'].add(date)
            else:
                by_equip[k]['dates_inactive'].add(date)

            by_equip[k]['total_units_days'] += count
            by_equip[k]['total_hours'] += count * hours

        multiplier = self._get_unit_multiplier(unit)
        rows = []
        for (etype, emodel), d in by_equip.items():
            total_days = len(d['all_dates'])
            days_active = len(d['dates_active'])
            days_inactive = len(d['dates_inactive'])
            days_repair = len(d['dates_repair'])

            active_pct = round(days_active / total_days * 100, 1) if total_days else 0
            inactive_pct = round(days_inactive / total_days * 100, 1) if total_days else 0
            repair_pct = round(days_repair / total_days * 100, 1) if total_days else 0

            avg_hours_day = d['total_hours'] / total_days if total_days else 0
            avg_hours = round(avg_hours_day * multiplier, 2)

            # Planned qty from config
            models_dict = self.equip_costs.get(etype, {})
            model_info = models_dict.get(emodel, models_dict.get('default', {}))
            planned_qty = model_info.get('planned_quantity', 0)
            hourly_rate = model_info.get('hourly_rate', 0)

            avg_active_day = d['total_units_days'] / total_days if total_days else 0
            utilisation_pct = round(avg_active_day / planned_qty * 100, 1) if planned_qty else 0

            name = f"{etype} - {emodel}" if emodel else etype

            rows.append({
                'equipment_name': name,
                'equipment_type': etype,
                'equipment_model': emodel,
                'total_days': total_days,
                'days_active': days_active,
                'days_inactive': days_inactive,
                'days_repair': days_repair,
                'active_pct': active_pct,
                'inactive_pct': inactive_pct,
                'repair_pct': repair_pct,
                'total_units_days': d['total_units_days'],
                'total_hours': round(d['total_hours'], 2),
                'avg_hours': avg_hours,
                'hourly_rate': hourly_rate,
                'planned_qty': planned_qty,
                'utilisation_pct': utilisation_pct,
            })

        rows.sort(key=lambda x: x['total_hours'], reverse=True)

        totals = {
            'total_units_days': sum(r['total_units_days'] for r in rows),
            'total_hours': round(sum(r['total_hours'] for r in rows), 2),
        }

        return {'rows': rows, 'totals': totals}

    # ------------------------------------------------------------------
    def get_all(self, unit: str = "per_day") -> Dict[str, Any]:
        return {
            'summary': self.get_summary_table(unit),
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _get_unit_multiplier(unit: str) -> float:
        return {'per_day': 1.0, 'per_hour': 1.0 / 8.0,
                'per_week': 7.0, 'per_month': 30.0}.get(unit, 1.0)
