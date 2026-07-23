"""
=============================================================================
ANALYSIS: Activities & Roadmap Progress (پیشرفت فعالیت‌ها و نقشه مسیر)
=============================================================================
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class ActivitiesRoadmapAnalysis:
    """
    Analyses construction operations data and produces summaries,
    charts data, and projections for the Activities & Roadmap page.
    """

    def __init__(self, data_service, project_config: dict):
        self.ds = data_service
        self.config = project_config
        self._ops: Optional[List[dict]] = None  # lazy cache

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @property
    def ops(self) -> List[dict]:
        if self._ops is None:
            self._ops = self.ds.get_construction_operations()
        return self._ops

    def _budget(self) -> dict:
        """Return Activity_Budget from config (or empty dict)."""
        return self.config.get("Activity_Budget", {})

    def _planned(self, activity: str) -> dict:
        """Get {planned_amount, price_per_unit} for one activity."""
        return self._budget().get(activity, {"planned_amount": 0, "price_per_unit": 0})

    @staticmethod
    def _distinct_dates(rows: List[dict]) -> List[str]:
        """Sorted unique form_date strings from a list of row-dicts."""
        return sorted({r["form_date"] for r in rows})

    @staticmethod
    def _unit_multiplier(unit: str, num_days: int, work_hours: int = 8) -> float:
        """
        Convert a *total* value into a rate based on the chosen unit.
        Returns a divisor: result = total / divisor.
        """
        if num_days <= 0:
            num_days = 1
        if unit == "per_hour":
            return num_days * work_hours
        if unit == "per_week":
            return num_days / 7
        if unit == "per_month":
            return num_days / 30
        # default per_day
        return num_days

    # ------------------------------------------------------------------
    # 1. Activities summary table
    # ------------------------------------------------------------------
    def get_activities_summary(self, unit: str = "per_day") -> List[dict]:
        """
        One dict per activity type with totals, planned, progress, costs.
        """
        budget = self._budget()
        by_activity: Dict[str, List[dict]] = defaultdict(list)
        for row in self.ops:
            by_activity[row["operation_type"]].append(row)

        # date span for rate conversion
        all_dates = self._distinct_dates(self.ops)
        if len(all_dates) >= 2:
            d0 = datetime.fromisoformat(all_dates[0])
            d1 = datetime.fromisoformat(all_dates[-1])
            num_days = max((d1 - d0).days, 1)
        else:
            num_days = 1

        result = []
        total_cost_done = 0
        total_planned_cost = 0

        for activity, rows in sorted(by_activity.items()):
            planned = self._planned(activity)
            planned_amount = planned["planned_amount"]
            price = planned["price_per_unit"]
            total_amount = sum(r["amount"] for r in rows)
            dates = self._distinct_dates(rows)
            days_active = len(dates)
            first_date = dates[0] if dates else None
            last_date = dates[-1] if dates else None
            cost_done = total_amount * price
            planned_cost = planned_amount * price
            progress = (total_amount / planned_amount * 100) if planned_amount > 0 else None

            divisor = self._unit_multiplier(unit, num_days)
            avg_amount = total_amount / divisor if divisor else 0

            total_cost_done += cost_done
            total_planned_cost += planned_cost

            # unit label from config or from first row
            unit_label = ""
            act_units = self.config.get("Daily_Activity_Report", {})
            if activity in act_units:
                unit_label = act_units[activity]
            elif rows:
                unit_label = rows[0].get("unit", "")

            result.append({
                "activity": activity,
                "unit_label": unit_label,
                "total_amount": round(total_amount, 2),
                "planned_amount": planned_amount,
                "progress": round(progress, 1) if progress is not None else None,
                "cost_done": round(cost_done, 2),
                "planned_cost": round(planned_cost, 2),
                "first_date": first_date,
                "last_date": last_date,
                "days_active": days_active,
                "avg_amount": round(avg_amount, 2),
            })

        return {
            "rows": result,
            "total_cost_done": round(total_cost_done, 2),
            "total_planned_cost": round(total_planned_cost, 2),
            "unit": unit,
            "num_days": num_days,
        }

    # ------------------------------------------------------------------
    # 2. Roadmap coverage segments
    # ------------------------------------------------------------------
    def get_roadmap_coverage(self) -> List[dict]:
        """
        Each segment: {operation_type, start_m, end_m, date, amount, cost}.
        Suitable for a horizontal Gantt-style chart.
        """
        budget = self._budget()
        segments = []
        for r in self.ops:
            price = self._planned(r["operation_type"])["price_per_unit"]
            segments.append({
                "operation_type": r["operation_type"],
                "start_m": r.get("start_meters", 0),
                "end_m": r.get("end_meters", 0),
                "start_station": r.get("start_station", ""),
                "end_station": r.get("end_station", ""),
                "date": r["form_date"],
                "amount": r["amount"],
                "cost": round(r["amount"] * price, 2),
            })
        return segments

    # ------------------------------------------------------------------
    # 3. Cumulative progress per activity
    # ------------------------------------------------------------------
    def get_cumulative_progress(self) -> dict:
        """
        { activity_name: [{date, cumulative, planned_amount}, ...], ... }
        """
        budget = self._budget()
        by_activity: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

        for r in self.ops:
            by_activity[r["operation_type"]][r["form_date"]] += r["amount"]

        result = {}
        for activity, date_amounts in sorted(by_activity.items()):
            planned = self._planned(activity)["planned_amount"]
            cumulative = 0
            series = []
            for d in sorted(date_amounts):
                cumulative += date_amounts[d]
                series.append({
                    "date": d,
                    "cumulative": round(cumulative, 2),
                    "planned_amount": planned,
                })
            result[activity] = series
        return result

    # ------------------------------------------------------------------
    # 4. Work output (stacked bar data, grouped by unit)
    # ------------------------------------------------------------------
    @staticmethod
    def _date_to_period_key(date_str: str, unit: str) -> str:
        """
        Map an ISO date to a period key based on the unit.
        per_day  → YYYY-MM-DD
        per_week → ISO week start (Monday) as YYYY-MM-DD
        per_month → YYYY-MM-01
        per_hour → same as per_day (amounts will be divided by work_hours)
        """
        dt = datetime.fromisoformat(date_str)
        if unit == 'per_week':
            monday = dt - timedelta(days=dt.weekday())
            return monday.date().isoformat()
        elif unit == 'per_month':
            return dt.strftime('%Y-%m-01')
        else:
            return date_str  # per_day and per_hour

    def get_daily_output(self, unit: str = "per_day") -> List[dict]:
        """
        [{date, activities: {activity_name: amount, ...}}, ...]

        When unit is per_week or per_month, amounts are summed into
        their respective period.  When unit is per_hour, daily amounts
        are divided by work_hours (8).
        """
        work_hours = 8
        by_period: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for r in self.ops:
            key = self._date_to_period_key(r["form_date"], unit)
            by_period[key][r["operation_type"]] += r["amount"]

        # For per_hour, divide totals by the number of days in each period * work_hours
        if unit == 'per_hour':
            # Count how many actual days fall in each period key
            days_per_period: Dict[str, set] = defaultdict(set)
            for r in self.ops:
                key = self._date_to_period_key(r["form_date"], unit)
                days_per_period[key].add(r["form_date"])
            for key in by_period:
                n = len(days_per_period.get(key, {1}))
                div = max(n * work_hours, 1)
                for act in by_period[key]:
                    by_period[key][act] = round(by_period[key][act] / div, 2)

        result = []
        for d in sorted(by_period):
            result.append({"date": d, "activities": dict(by_period[d])})
        return result

    # ------------------------------------------------------------------
    # 5. Cost breakdown (pie chart data)
    # ------------------------------------------------------------------
    def get_cost_breakdown(self) -> List[dict]:
        """[{activity, total_cost}, ...]"""
        by_activity: Dict[str, float] = defaultdict(float)
        for r in self.ops:
            price = self._planned(r["operation_type"])["price_per_unit"]
            by_activity[r["operation_type"]] += r["amount"] * price

        return [
            {"activity": a, "total_cost": round(c, 2)}
            for a, c in sorted(by_activity.items())
        ]

    # ------------------------------------------------------------------
    # 6. Projection / forecast
    # ------------------------------------------------------------------
    def get_projection(self) -> List[dict]:
        """
        [{activity, current_rate, remaining, days_to_finish,
          projected_end, total_done, planned_amount}, ...]
        """
        by_activity: Dict[str, List[dict]] = defaultdict(list)
        for r in self.ops:
            by_activity[r["operation_type"]].append(r)

        result = []
        for activity, rows in sorted(by_activity.items()):
            planned = self._planned(activity)
            planned_amount = planned["planned_amount"]
            total_done = sum(r["amount"] for r in rows)
            dates = self._distinct_dates(rows)
            days_active = len(dates)
            last_date = dates[-1] if dates else None

            if days_active > 0:
                current_rate = total_done / days_active
            else:
                current_rate = 0

            remaining = max(planned_amount - total_done, 0)

            if current_rate > 0 and remaining > 0:
                days_to_finish = remaining / current_rate
                if last_date:
                    projected_end = (
                        datetime.fromisoformat(last_date) + timedelta(days=int(days_to_finish))
                    ).date().isoformat()
                else:
                    projected_end = None
            else:
                days_to_finish = 0 if remaining == 0 else None
                projected_end = last_date if remaining == 0 else None

            result.append({
                "activity": activity,
                "total_done": round(total_done, 2),
                "planned_amount": planned_amount,
                "current_rate": round(current_rate, 2),
                "remaining": round(remaining, 2),
                "days_to_finish": round(days_to_finish, 1) if days_to_finish is not None else None,
                "projected_end": projected_end,
                "last_date": last_date,
            })
        return result

    # ------------------------------------------------------------------
    # Combined — all data for the page in one call
    # ------------------------------------------------------------------
    def get_all(self, unit: str = "per_day") -> dict:
        """Return everything the template / API needs."""
        return {
            "summary": self.get_activities_summary(unit),
            "roadmap": self.get_roadmap_coverage(),
            "cumulative": self.get_cumulative_progress(),
            "daily_output": self.get_daily_output(unit),
            "cost_breakdown": self.get_cost_breakdown(),
            "projection": self.get_projection(),
        }