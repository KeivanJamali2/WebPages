"""
Weather & Climate Impact Analysis
====================================

Analyzes temperature, humidity, weather conditions and their impact on work.
"""
from typing import Dict, List, Any
from collections import defaultdict


class WeatherAnalysis:
    """
    Analyzes weather / climate data from daily forms.

    Provides:
    - Summary statistics (avg temp, humidity, weather type distribution)
    - Climate effect breakdown
    """

    def __init__(self, data_service, project_config: dict):
        self.ds = data_service
        self.config = project_config
        self.weather_data = data_service.get_climate_conditions()

    # ------------------------------------------------------------------
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Summary metrics table.
        """
        if not self.weather_data:
            return {'rows': [], 'total_days': 0}

        total_days = len(set(r['form_date'] for r in self.weather_data))

        min_temps = []
        max_temps = []
        humidities = []
        weather_types = defaultdict(int)
        climate_effects = defaultdict(int)

        record_min_temp = None
        record_min_date = None
        record_max_temp = None
        record_max_date = None

        for rec in self.weather_data:
            mt = rec.get('min_temperature')
            xt = rec.get('max_temperature')
            hum = rec.get('humidity')
            wt = rec.get('weather_type') or 'unknown'
            ce = rec.get('climate_effect') or 'unknown'

            if mt is not None:
                min_temps.append(mt)
                if record_min_temp is None or mt < record_min_temp:
                    record_min_temp = mt
                    record_min_date = rec['form_date']

            if xt is not None:
                max_temps.append(xt)
                if record_max_temp is None or xt > record_max_temp:
                    record_max_temp = xt
                    record_max_date = rec['form_date']

            if hum is not None:
                humidities.append(hum)

            weather_types[wt] += 1
            climate_effects[ce] += 1

        avg_min = round(sum(min_temps) / len(min_temps), 1) if min_temps else None
        avg_max = round(sum(max_temps) / len(max_temps), 1) if max_temps else None
        avg_hum = round(sum(humidities) / len(humidities), 1) if humidities else None

        slow = climate_effects.get('slow_progress', 0)
        stopped = climate_effects.get('stopped', 0)
        impact_pct = round((slow + stopped) / total_days * 100, 1) if total_days else 0

        return {
            'total_days': total_days,
            'avg_min_temp': avg_min,
            'avg_max_temp': avg_max,
            'min_temp_recorded': record_min_temp,
            'min_temp_date': record_min_date,
            'max_temp_recorded': record_max_temp,
            'max_temp_date': record_max_date,
            'avg_humidity': avg_hum,
            'weather_types': dict(weather_types),
            'climate_effects': dict(climate_effects),
            'impact_pct': impact_pct,
        }

    # ------------------------------------------------------------------
    def get_weather_table(self) -> Dict[str, Any]:
        """
        One row per weather_type showing counts and effect breakdown.
        """
        by_type = defaultdict(lambda: {
            'count': 0,
            'no_effect': 0,
            'slow_progress': 0,
            'stopped': 0,
            'min_temps': [],
            'max_temps': [],
            'humidities': [],
        })

        for rec in self.weather_data:
            wt = rec.get('weather_type') or 'unknown'
            ce = rec.get('climate_effect') or 'unknown'

            by_type[wt]['count'] += 1
            if ce == 'no_effect':
                by_type[wt]['no_effect'] += 1
            elif ce == 'slow_progress':
                by_type[wt]['slow_progress'] += 1
            elif ce == 'stopped':
                by_type[wt]['stopped'] += 1

            mt = rec.get('min_temperature')
            xt = rec.get('max_temperature')
            hum = rec.get('humidity')
            if mt is not None:
                by_type[wt]['min_temps'].append(mt)
            if xt is not None:
                by_type[wt]['max_temps'].append(xt)
            if hum is not None:
                by_type[wt]['humidities'].append(hum)

        total_days = len(set(r['form_date'] for r in self.weather_data)) if self.weather_data else 0

        rows = []
        for wt, d in by_type.items():
            pct = round(d['count'] / total_days * 100, 1) if total_days else 0
            avg_min = round(sum(d['min_temps']) / len(d['min_temps']), 1) if d['min_temps'] else None
            avg_max = round(sum(d['max_temps']) / len(d['max_temps']), 1) if d['max_temps'] else None
            avg_hum = round(sum(d['humidities']) / len(d['humidities']), 1) if d['humidities'] else None

            rows.append({
                'weather_type': wt,
                'days': d['count'],
                'pct_of_total': pct,
                'no_effect': d['no_effect'],
                'slow_progress': d['slow_progress'],
                'stopped': d['stopped'],
                'avg_min_temp': avg_min,
                'avg_max_temp': avg_max,
                'avg_humidity': avg_hum,
            })

        rows.sort(key=lambda x: x['days'], reverse=True)

        return {'rows': rows, 'total_days': total_days}

    # ------------------------------------------------------------------
    def get_all(self, unit: str = "per_day") -> Dict[str, Any]:
        return {
            'summary_stats': self.get_summary_stats(),
            'weather_table': self.get_weather_table(),
        }
