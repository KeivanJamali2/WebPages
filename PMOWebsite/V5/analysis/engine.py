"""
=============================================================================
Analysis Engine — Stub
=============================================================================

This is a minimal stub so that routes/boss.py can import AnalysisEngine
without crashing.  The only method it implements is `check_data_availability()`
which is used by the boss dashboard to decide whether to show "no data yet".

YOU should add your own analysis methods here.
"""

from models.daily_form import DailyFormSubmission


class AnalysisEngine:
    """
    Stub analysis engine.

    Replace / extend this class with your own engineering analyses.
    The boss route currently only calls:
        - engine.check_data_availability()
    """

    def __init__(self, db, project_id, project_config=None, lang='en'):
        self.db = db
        self.project_id = project_id
        self.project_config = project_config or {}
        self.lang = lang

    # ------------------------------------------------------------------
    # Data availability (used by the boss route)
    # ------------------------------------------------------------------
    def check_data_availability(self):
        """
        Check how many approved daily‑form submissions exist for this project.

        Returns:
            dict: {
                'has_data': bool,
                'form_count': int,
                'message': str,
            }
        """
        form_count = (
            self.db.session.query(DailyFormSubmission)
            .filter(
                DailyFormSubmission.project_id == self.project_id,
                DailyFormSubmission.status == 'approved',
            )
            .count()
        )

        return {
            'has_data': form_count > 0,
            'form_count': form_count,
            'message': (
                'Ready for analysis'
                if form_count > 0
                else 'No approved daily forms yet. Submit and approve data first.'
            ),
        }
