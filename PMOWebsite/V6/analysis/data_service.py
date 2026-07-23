"""
=============================================================================
Data Service — Database Helper for Analysis
=============================================================================

Provides clean, ready-to-use functions that pull data from the database
so you can focus purely on the engineering / analysis logic.

MODELS AVAILABLE (for reference):
    DailyFormSubmission   — main form (date, project_id, status, …)
    HumanResource         — post, count, working_hours, notes
    ToolEquipment         — equipment_type, equipment_model, count_active,
                            working_hours, situation, inactivity_reason
    ConstructionOperation — operation_type, start_station, end_station,
                            unit, amount
    IncomingMaterial      — material_type, material_unit, incoming_amount,
                            cumulative_incoming, used_amount,
                            cumulative_used, storage_place, waybill_number
    ClimateCondition      — min_temperature, max_temperature, humidity,
                            weather_type, wind_speed, climate_effect
    ProjectIssue          — issue_type, effect, location_station,
                            start_time, end_time, notes
    Safety                — safety_situation, safety_inspection,
                            incident_occurred, incident_explanation
    Event                 — event_type, event_name, explanation,
                            document_filename
    Project               — project_code, name, location, budget,
                            start_date, end_date, …

USAGE:
    from analysis.data_service import DataService
    from models import db

    ds = DataService(db, project_id=1)

    # Get all approved forms as dicts
    forms = ds.get_forms()

    # Get human‑resource rows joined with form date
    hr = ds.get_human_resources()

    # Get everything in one call
    bundle = ds.get_all_data()
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, and_

from models.daily_form import (
    DailyFormSubmission,
    HumanResource,
    ToolEquipment,
    ConstructionOperation,
    IncomingMaterial,
    ClimateCondition,
    ProjectIssue,
    Safety,
    Event,
)
from models.project import Project


class DataService:
    """
    Helper class that reads daily‑form data and project info from the DB.

    Every public method returns plain Python objects (lists of dicts)
    so you can use them in analysis code, Pandas, or anything else
    without depending on SQLAlchemy outside this class.
    """

    def __init__(self, db, project_id: int,
                 status: str = 'approved',
                 from_date: Optional[date] = None,
                 to_date: Optional[date] = None):
        """
        Args:
            db          : The SQLAlchemy ``db`` object (``from models import db``).
            project_id  : Which project to query.
            status      : Only include forms with this status (default ``'approved'``).
                          Pass ``None`` to include all statuses.
            from_date   : Optional start‑date filter (inclusive).
            to_date     : Optional end‑date filter (inclusive).
        """
        self.db = db
        self.project_id = project_id
        self.status = status
        self.from_date = from_date
        self.to_date = to_date

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _base_form_query(self):
        """Return a query on DailyFormSubmission already filtered by project / status / dates."""
        q = DailyFormSubmission.query.filter(
            DailyFormSubmission.project_id == self.project_id,
        )
        if self.status is not None:
            q = q.filter(DailyFormSubmission.status == self.status)
        if self.from_date is not None:
            q = q.filter(DailyFormSubmission.form_date >= self.from_date)
        if self.to_date is not None:
            q = q.filter(DailyFormSubmission.form_date <= self.to_date)
        return q

    def _form_ids(self) -> list[int]:
        """Get IDs of matching forms (used to join child tables)."""
        rows = self._base_form_query().with_entities(DailyFormSubmission.id).all()
        return [r.id for r in rows]

    def _child_query(self, model):
        """Return a query on a child model filtered by the matching form IDs."""
        form_ids = self._form_ids()
        if not form_ids:
            return model.query.filter(False)  # empty result
        return model.query.filter(model.daily_form_id.in_(form_ids))

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert a SQLAlchemy model instance to a plain dict via its ``to_dict()``."""
        if hasattr(row, 'to_dict'):
            return row.to_dict()
        # Fallback: use column inspection
        return {c.name: getattr(row, c.name) for c in row.__table__.columns}

    # ------------------------------------------------------------------
    # Project information
    # ------------------------------------------------------------------
    def get_project(self) -> Optional[Dict[str, Any]]:
        """
        Get project information as a dict.

        Returns:
            dict with keys: id, project_code, name, location, contract_number,
            start_date, end_date, is_ongoing, budget, owner, manager,
            description, status, …
            or None if project not found.
        """
        project = Project.query.get(self.project_id)
        if project is None:
            return None
        return project.to_dict()

    def get_project_config(self) -> Dict[str, Any]:
        """
        Load the project's configuration file (from Projects/project_configurations/).

        Returns:
            Configuration dict (HUMAN_RESOURCES, TOOLS_EQUIPMENT, OPERATIONS, …).
            Empty dict if not found.
        """
        project = Project.query.get(self.project_id)
        if project is None:
            return {}
        from Projects.project_configurations import load_project_config
        try:
            return load_project_config(project.project_code)
        except FileNotFoundError:
            return {}

    # ------------------------------------------------------------------
    # Daily form submissions
    # ------------------------------------------------------------------
    def get_forms(self, include_sections: bool = False) -> List[Dict[str, Any]]:
        """
        Get all matching daily‑form submissions.

        Args:
            include_sections: If True, each dict also contains nested lists
                              for human_resources, tools_equipments, etc.
        Returns:
            List of dicts sorted by form_date ascending.
        """
        forms = (
            self._base_form_query()
            .order_by(DailyFormSubmission.form_date.asc())
            .all()
        )
        return [f.to_dict(include_sections=include_sections) for f in forms]

    def get_form_dates(self) -> List[date]:
        """
        Get sorted list of unique form dates.

        Returns:
            List of ``datetime.date`` objects.
        """
        rows = (
            self._base_form_query()
            .with_entities(DailyFormSubmission.form_date)
            .distinct()
            .order_by(DailyFormSubmission.form_date.asc())
            .all()
        )
        return [r.form_date for r in rows]

    def get_form_count(self) -> int:
        """Return total number of matching forms."""
        return self._base_form_query().count()

    # ------------------------------------------------------------------
    # Human Resources
    # ------------------------------------------------------------------
    def get_human_resources(self) -> List[Dict[str, Any]]:
        """
        Get all human‑resource records linked to matching forms.

        Each dict has: id, daily_form_id, post, count, working_hours, notes,
        plus **form_date** (joined from the parent form).

        Returns:
            List of dicts sorted by form_date ascending.
        """
        rows = (
            self.db.session.query(HumanResource, DailyFormSubmission.form_date)
            .join(DailyFormSubmission)
            .filter(
                DailyFormSubmission.project_id == self.project_id,
                *self._date_status_filters(),
            )
            .order_by(DailyFormSubmission.form_date.asc())
            .all()
        )
        result = []
        for hr, form_date in rows:
            d = hr.to_dict()
            d['form_date'] = form_date.isoformat()
            result.append(d)
        return result

    # ------------------------------------------------------------------
    # Tools & Equipment
    # ------------------------------------------------------------------
    def get_tools_equipment(self) -> List[Dict[str, Any]]:
        """
        Get all tool / equipment records linked to matching forms.

        Each dict has: id, equipment_type, equipment_model, count_active,
        working_hours, situation, inactivity_reason, plus **form_date**.

        Returns:
            List of dicts sorted by form_date ascending.
        """
        rows = (
            self.db.session.query(ToolEquipment, DailyFormSubmission.form_date)
            .join(DailyFormSubmission)
            .filter(
                DailyFormSubmission.project_id == self.project_id,
                *self._date_status_filters(),
            )
            .order_by(DailyFormSubmission.form_date.asc())
            .all()
        )
        result = []
        for te, form_date in rows:
            d = te.to_dict()
            d['form_date'] = form_date.isoformat()
            result.append(d)
        return result

    # ------------------------------------------------------------------
    # Construction Operations
    # ------------------------------------------------------------------
    def get_construction_operations(self) -> List[Dict[str, Any]]:
        """
        Get all construction‑operation records linked to matching forms.

        Each dict has: id, operation_type, start_station, end_station,
        start_meters, end_meters, length_meters, unit, amount,
        plus **form_date**.

        Returns:
            List of dicts sorted by form_date ascending.
        """
        rows = (
            self.db.session.query(ConstructionOperation, DailyFormSubmission.form_date)
            .join(DailyFormSubmission)
            .filter(
                DailyFormSubmission.project_id == self.project_id,
                *self._date_status_filters(),
            )
            .order_by(DailyFormSubmission.form_date.asc())
            .all()
        )
        result = []
        for co, form_date in rows:
            d = co.to_dict()
            d['form_date'] = form_date.isoformat()
            result.append(d)
        return result

    # ------------------------------------------------------------------
    # Incoming Materials
    # ------------------------------------------------------------------
    def get_incoming_materials(self) -> List[Dict[str, Any]]:
        """
        Get all incoming‑material records linked to matching forms.

        Each dict has: id, material_type, material_unit, incoming_amount,
        cumulative_incoming, used_amount, cumulative_used, storage_place,
        waybill_number, plus **form_date**.

        Returns:
            List of dicts sorted by form_date ascending.
        """
        rows = (
            self.db.session.query(IncomingMaterial, DailyFormSubmission.form_date)
            .join(DailyFormSubmission)
            .filter(
                DailyFormSubmission.project_id == self.project_id,
                *self._date_status_filters(),
            )
            .order_by(DailyFormSubmission.form_date.asc())
            .all()
        )
        result = []
        for im, form_date in rows:
            d = im.to_dict()
            d['form_date'] = form_date.isoformat()
            result.append(d)
        return result

    # ------------------------------------------------------------------
    # Climate Conditions
    # ------------------------------------------------------------------
    def get_climate_conditions(self) -> List[Dict[str, Any]]:
        """
        Get all climate‑condition records linked to matching forms.

        Each dict has: id, min_temperature, max_temperature, humidity,
        weather_type, wind_speed, climate_effect, plus **form_date**.

        Returns:
            List of dicts sorted by form_date ascending.
        """
        rows = (
            self.db.session.query(ClimateCondition, DailyFormSubmission.form_date)
            .join(DailyFormSubmission)
            .filter(
                DailyFormSubmission.project_id == self.project_id,
                *self._date_status_filters(),
            )
            .order_by(DailyFormSubmission.form_date.asc())
            .all()
        )
        result = []
        for cc, form_date in rows:
            d = cc.to_dict()
            d['form_date'] = form_date.isoformat()
            result.append(d)
        return result

    # ------------------------------------------------------------------
    # Project Issues
    # ------------------------------------------------------------------
    def get_project_issues(self) -> List[Dict[str, Any]]:
        """
        Get all project‑issue records linked to matching forms.

        Each dict has: id, issue_type, effect, location_station,
        start_time, end_time, notes, plus **form_date**.

        Returns:
            List of dicts sorted by form_date ascending.
        """
        rows = (
            self.db.session.query(ProjectIssue, DailyFormSubmission.form_date)
            .join(DailyFormSubmission)
            .filter(
                DailyFormSubmission.project_id == self.project_id,
                *self._date_status_filters(),
            )
            .order_by(DailyFormSubmission.form_date.asc())
            .all()
        )
        result = []
        for pi, form_date in rows:
            d = pi.to_dict()
            d['form_date'] = form_date.isoformat()
            result.append(d)
        return result

    # ------------------------------------------------------------------
    # Safety Records
    # ------------------------------------------------------------------
    def get_safety_records(self) -> List[Dict[str, Any]]:
        """
        Get all safety records linked to matching forms.

        Each dict has: id, safety_situation, safety_inspection,
        incident_occurred, incident_explanation, plus **form_date**.

        Returns:
            List of dicts sorted by form_date ascending.
        """
        rows = (
            self.db.session.query(Safety, DailyFormSubmission.form_date)
            .join(DailyFormSubmission)
            .filter(
                DailyFormSubmission.project_id == self.project_id,
                *self._date_status_filters(),
            )
            .order_by(DailyFormSubmission.form_date.asc())
            .all()
        )
        result = []
        for sr, form_date in rows:
            d = sr.to_dict()
            d['form_date'] = form_date.isoformat()
            result.append(d)
        return result

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def get_events(self) -> List[Dict[str, Any]]:
        """
        Get all event records linked to matching forms.

        Each dict has: id, event_type, event_name, explanation,
        document_filename, plus **form_date**.

        Returns:
            List of dicts sorted by form_date ascending.
        """
        rows = (
            self.db.session.query(Event, DailyFormSubmission.form_date)
            .join(DailyFormSubmission)
            .filter(
                DailyFormSubmission.project_id == self.project_id,
                *self._date_status_filters(),
            )
            .order_by(DailyFormSubmission.form_date.asc())
            .all()
        )
        result = []
        for ev, form_date in rows:
            d = ev.to_dict()
            d['form_date'] = form_date.isoformat()
            result.append(d)
        return result

    # ------------------------------------------------------------------
    # Aggregation helpers
    # ------------------------------------------------------------------
    def get_all_data(self) -> Dict[str, Any]:
        """
        Fetch **everything** in one call.

        Returns:
            {
                'project':                 dict | None,
                'forms':                   [dict, …],
                'human_resources':         [dict, …],
                'tools_equipment':         [dict, …],
                'construction_operations': [dict, …],
                'incoming_materials':      [dict, …],
                'climate_conditions':      [dict, …],
                'project_issues':          [dict, …],
                'safety_records':          [dict, …],
                'events':                  [dict, …],
            }
        """
        return {
            'project': self.get_project(),
            'forms': self.get_forms(),
            'human_resources': self.get_human_resources(),
            'tools_equipment': self.get_tools_equipment(),
            'construction_operations': self.get_construction_operations(),
            'incoming_materials': self.get_incoming_materials(),
            'climate_conditions': self.get_climate_conditions(),
            'project_issues': self.get_project_issues(),
            'safety_records': self.get_safety_records(),
            'events': self.get_events(),
        }

    def get_summary_counts(self) -> Dict[str, int]:
        """
        Quick count of records per section.

        Returns:
            {
                'forms': 5,
                'human_resources': 42,
                'tools_equipment': 18,
                ...
            }
        """
        form_ids = self._form_ids()
        if not form_ids:
            return {k: 0 for k in [
                'forms', 'human_resources', 'tools_equipment',
                'construction_operations', 'incoming_materials',
                'climate_conditions', 'project_issues',
                'safety_records', 'events',
            ]}

        def _count(model):
            return model.query.filter(model.daily_form_id.in_(form_ids)).count()

        return {
            'forms': len(form_ids),
            'human_resources': _count(HumanResource),
            'tools_equipment': _count(ToolEquipment),
            'construction_operations': _count(ConstructionOperation),
            'incoming_materials': _count(IncomingMaterial),
            'climate_conditions': _count(ClimateCondition),
            'project_issues': _count(ProjectIssue),
            'safety_records': _count(Safety),
            'events': _count(Event),
        }

    # ------------------------------------------------------------------
    # Per-date data (useful for time‑series)
    # ------------------------------------------------------------------
    def get_data_for_date(self, target_date: date) -> Dict[str, Any]:
        """
        Get all section data for a single date.

        Args:
            target_date: The date to query.

        Returns:
            Same structure as ``get_all_data()`` but filtered to one day.
        """
        # Temporarily override date filters
        old_from, old_to = self.from_date, self.to_date
        self.from_date = target_date
        self.to_date = target_date
        try:
            data = self.get_all_data()
        finally:
            self.from_date, self.to_date = old_from, old_to
        return data

    # ------------------------------------------------------------------
    # Private filter helper
    # ------------------------------------------------------------------
    def _date_status_filters(self):
        """Build a list of SQLAlchemy filter clauses for status + date range."""
        filters = []
        if self.status is not None:
            filters.append(DailyFormSubmission.status == self.status)
        if self.from_date is not None:
            filters.append(DailyFormSubmission.form_date >= self.from_date)
        if self.to_date is not None:
            filters.append(DailyFormSubmission.form_date <= self.to_date)
        return filters
