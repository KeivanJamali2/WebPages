"""
Materials & Resources Analysis
================================

Analyzes incoming materials: amounts received, used, stock levels, consumption.
"""
from typing import Dict, List, Any
from collections import defaultdict


class MaterialsAnalysis:
    """
    Analyzes incoming materials data from daily forms.

    Provides:
    - Summary table per material (incoming, used, stock)
    - Stock alerts
    """

    def __init__(self, data_service, project_config: dict):
        self.ds = data_service
        self.config = project_config
        self.mat_data = data_service.get_incoming_materials()
        self.materials = project_config.get('Incoming_Materials_And_Goods', {})

    # ------------------------------------------------------------------
    def get_summary_table(self, unit: str = "per_day") -> Dict[str, Any]:
        """
        One row per material_type.

        Columns: material, unit, total_incoming, total_used, current_stock,
        usage_pct_incoming, avg_incoming (unit-adjusted), avg_used (unit-adjusted).
        """
        by_mat = defaultdict(lambda: {
            'dates': set(),
            'total_incoming': 0.0,
            'total_used': 0.0,
            'max_cum_in': 0.0,
            'max_cum_used': 0.0,
            'unit': '',
        })

        for rec in self.mat_data:
            mt = rec['material_type']
            date = rec['form_date']

            by_mat[mt]['dates'].add(date)
            by_mat[mt]['total_incoming'] += rec.get('incoming_amount', 0)
            by_mat[mt]['total_used'] += rec.get('used_amount', 0)
            by_mat[mt]['unit'] = rec.get('material_unit', '')

            cum_in = rec.get('cumulative_incoming', 0)
            cum_used = rec.get('cumulative_used', 0)
            if cum_in > by_mat[mt]['max_cum_in']:
                by_mat[mt]['max_cum_in'] = cum_in
            if cum_used > by_mat[mt]['max_cum_used']:
                by_mat[mt]['max_cum_used'] = cum_used

        multiplier = self._get_unit_multiplier(unit)
        rows = []
        for mt, d in by_mat.items():
            total_days = len(d['dates'])
            # Prefer cumulative max if available, else sum
            total_incoming = d['max_cum_in'] if d['max_cum_in'] > 0 else d['total_incoming']
            total_used = d['max_cum_used'] if d['max_cum_used'] > 0 else d['total_used']
            current_stock = total_incoming - total_used

            usage_pct_incoming = round(total_used / total_incoming * 100, 1) if total_incoming else 0

            avg_incoming_day = d['total_incoming'] / total_days if total_days else 0
            avg_used_day = d['total_used'] / total_days if total_days else 0

            rows.append({
                'material': mt,
                'unit': d['unit'],
                'total_incoming': round(total_incoming, 2),
                'total_used': round(total_used, 2),
                'current_stock': round(current_stock, 2),
                'usage_pct_incoming': usage_pct_incoming,
                'avg_incoming': round(avg_incoming_day * multiplier, 2),
                'avg_used': round(avg_used_day * multiplier, 2),
                'total_days': total_days,
            })

        rows.sort(key=lambda x: x['total_incoming'], reverse=True)

        totals = {
            'total_incoming': round(sum(r['total_incoming'] for r in rows), 2),
            'total_used': round(sum(r['total_used'] for r in rows), 2),
            'current_stock': round(sum(r['current_stock'] for r in rows), 2),
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
