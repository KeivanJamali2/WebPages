"""
Problems & Safety Analysis
============================

Section A — Project Issues: types, occurrences, durations.
Section B — Safety: incident / near-miss / no-incident breakdown.
"""
from typing import Dict, List, Any
from collections import defaultdict
from datetime import datetime, date


class ProblemsAnalysis:
    """
    Analyzes project issues and safety data from daily forms.

    Provides:
    - Issues summary table by issue type
    - Safety summary metrics
    """

    def __init__(self, data_service, project_config: dict):
        self.ds = data_service
        self.config = project_config
        self.issues_data = data_service.get_project_issues()
        self.safety_data = data_service.get_safety_records()
        self.form_dates = [d.isoformat() if isinstance(d, date) else d
                          for d in data_service.get_form_dates()]

    # ==================================================================
    # SECTION A — PROJECT ISSUES
    # ==================================================================

    def get_issues_summary(self) -> Dict[str, Any]:
        """
        One row per issue_type.

        Columns: issue_type, occurrences, days_with_issue,
        pct_of_all_days, avg_duration, last_occurrence.
        """
        total_form_days = len(set(self.form_dates))

        by_type = defaultdict(lambda: {
            'dates': set(),
            'count': 0,
            'durations': [],
        })

        for rec in self.issues_data:
            it = rec['issue_type']
            by_type[it]['dates'].add(rec['form_date'])
            by_type[it]['count'] += 1

            # Calculate duration if both times exist
            st = rec.get('start_time')
            et = rec.get('end_time')
            if st and et:
                try:
                    t1 = datetime.fromisoformat(st) if isinstance(st, str) else datetime.combine(date.min, st)
                    t2 = datetime.fromisoformat(et) if isinstance(et, str) else datetime.combine(date.min, et)
                    dur_minutes = (t2 - t1).total_seconds() / 60
                    if dur_minutes > 0:
                        by_type[it]['durations'].append(dur_minutes)
                except (ValueError, TypeError):
                    pass

        rows = []
        for it, d in by_type.items():
            days_with = len(d['dates'])
            pct = round(days_with / total_form_days * 100, 1) if total_form_days else 0

            # Average duration
            if d['durations']:
                avg_min = sum(d['durations']) / len(d['durations'])
                avg_dur = f"{int(avg_min // 60):02d}:{int(avg_min % 60):02d}"
            else:
                avg_dur = None

            sorted_dates = sorted(d['dates'])
            last_occ = sorted_dates[-1] if sorted_dates else None

            rows.append({
                'issue_type': it,
                'occurrences': d['count'],
                'days_with_issue': days_with,
                'pct_of_all_days': pct,
                'avg_duration': avg_dur,
                'last_occurrence': last_occ,
            })

        rows.sort(key=lambda x: x['occurrences'], reverse=True)

        return {
            'rows': rows,
            'total_form_days': total_form_days,
            'total_issues': sum(r['occurrences'] for r in rows),
        }

    # ==================================================================
    # SECTION B — SAFETY
    # ==================================================================

    def get_safety_summary(self) -> Dict[str, Any]:
        """
        Single dict with all safety metrics.
        """
        total_days = len(set(self.form_dates))

        incident_days = set()
        near_miss_days = set()
        no_incident_days = set()
        inspection_count = 0

        for rec in self.safety_data:
            sit = (rec.get('safety_situation') or '').strip()
            d = rec['form_date']

            if sit == 'Incident' or rec.get('incident_occurred'):
                incident_days.add(d)
            elif sit == 'NearMiss':
                near_miss_days.add(d)
            else:
                no_incident_days.add(d)

            if rec.get('safety_inspection'):
                inspection_count += 1

        n_incident = len(incident_days)
        n_near_miss = len(near_miss_days)
        n_no_incident = len(no_incident_days)

        incident_rate = round(n_incident / total_days * 100, 1) if total_days else 0
        near_miss_rate = round(n_near_miss / total_days * 100, 1) if total_days else 0
        safe_rate = round(n_no_incident / total_days * 100, 1) if total_days else 0
        inspection_rate = round(inspection_count / total_days * 100, 1) if total_days else 0

        # Days since last incident
        today_str = date.today().isoformat()
        if incident_days:
            last_incident = max(incident_days)
            try:
                d1 = date.fromisoformat(last_incident)
                days_since = (date.today() - d1).days
            except (ValueError, TypeError):
                days_since = None
        else:
            days_since = None

        return {
            'total_days': total_days,
            'incident_days': n_incident,
            'near_miss_days': n_near_miss,
            'no_incident_days': n_no_incident,
            'incident_rate': incident_rate,
            'near_miss_rate': near_miss_rate,
            'safe_rate': safe_rate,
            'days_since_last_incident': days_since,
            'inspection_count': inspection_count,
            'inspection_rate': inspection_rate,
        }

    # ==================================================================
    # Combined
    # ==================================================================

    def get_all(self, unit: str = "per_day") -> Dict[str, Any]:
        return {
            'issues_summary': self.get_issues_summary(),
            'safety_summary': self.get_safety_summary(),
        }
