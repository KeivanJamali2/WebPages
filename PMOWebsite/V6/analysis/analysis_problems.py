"""
=============================================================================
ANALYSIS: Problems & Safety (مشکلات و ایمنی)
=============================================================================

GOAL:
    Two sections on one page:
    SECTION A — Project Issues (مشکلات پروژه): types, locations, durations.
    SECTION B — Safety (ایمنی): incident / near-miss / no-incident breakdown.
    Both with tables + charts + export.

=============================================================================
DATA SOURCES
=============================================================================

1. ProjectIssue table (via DataService.get_project_issues()):
   Each row = one issue logged on one day.
   Fields:
       - form_date          (str, ISO date)
       - issue_type         (str — e.g. "مشکلات تجهیزاتی", "مسائل مالی")
       - effect             (str — description of the effect)
       - location_station   (str — station format "00+000", or None)
       - start_time         (str, ISO time or None — when the issue started)
       - end_time           (str, ISO time or None — when it ended)
       - notes              (str — additional remarks)

2. Safety table (via DataService.get_safety_records()):
   Each row = one safety record per day.
   Fields:
       - form_date              (str, ISO date)
       - safety_situation       (str — "Incident" / "NearMiss" / "NoIncident")
       - safety_inspection      (bool — was an inspection done?)
       - incident_occurred      (bool)
       - incident_explanation   (str — details if incident occurred)

3. DailyFormSubmission dates (via DataService.get_form_dates()):
   Used to know total reporting days (for "days with/without problems" calc).

4. Project config:
   - config["Project_Issues"]  →  list of issue type names

=============================================================================
SECTION A — PROJECT ISSUES
=============================================================================

TABLE A1 — Issues Summary (one row per issue_type):

    | # | Issue Type | Occurrences | Days with this Issue | % of All Days |
    | Locations Affected (list of unique stations) |
    | Avg Duration (end_time − start_time, if both exist) |
    | Last Occurrence Date |

    - Occurrences       = total rows matching this issue_type
    - Days with Issue   = distinct form_dates for this type
    - % of All Days     = Days with Issue / total form_dates × 100
    - Avg Duration      = mean of (end_time − start_time) for rows where
                          both times are non-null.  Display as HH:MM.
                          Show "N/A" if no time data.

TABLE A2 — Full Issues Log (flat table, scrollable):

    | Date | Issue Type | Effect | Location (Station) | Start Time | End Time | Duration | Notes |

    Sortable by any column.  Default sort: date descending (newest first).

---

CHART A1 — Issues by Category (Horizontal Bar)
    Y-axis = issue_type
    X-axis = number of occurrences
    Sorted descending.

CHART A2 — Days With Problems vs Without (Donut Chart)
    Two slices:
        - "Days with at least 1 issue" = count of distinct form_dates that have any ProjectIssue row
        - "Days without issues" = total form_dates − above
    Show counts and percentages.

CHART A3 — Issues Timeline (Scatter / Dot Chart)
    X-axis = Date
    Y-axis = Issue type (categorical)
    One dot per occurrence.  Dot colour = issue_type.  Tooltip = effect + location.
    Shows clustering of problems over time.

CHART A4 — Issues by Location (Horizontal Bar, if location data exists)
    Y-axis = Station (grouped into segments, e.g. 00+000–01+000, 01+000–02+000)
    X-axis = Number of issues in that segment
    Only shown if ≥ 3 issues have location_station filled.

=============================================================================
SECTION B — SAFETY
=============================================================================

TABLE B1 — Safety Summary:

    | Metric                     | Value  |
    |----------------------------|--------|
    | Total Reporting Days       | ...    |
    | Days: حادثه (Incident)     | ...    |
    | Days: شبه حادثه (NearMiss) | ...    |
    | Days: بدون حادثه (NoIncident) | ... |
    | Incident Rate (%)          | incidents / total × 100 |
    | Near-Miss Rate (%)         | near-misses / total × 100 |
    | Safe Days Rate (%)         | no-incidents / total × 100 |
    | Days Since Last Incident   | calendar days from last incident to today |
    | Total Inspections Done     | count where safety_inspection == True |
    | Inspection Rate (%)        | inspections / total × 100 |

TABLE B2 — Safety Detail Log:

    | Date | Situation (حادثه/شبه حادثه/بدون حادثه) | Inspection Done? | Incident? | Explanation |

    Sorted by date descending.
    Rows with incidents highlighted in red background.
    Rows with near-misses highlighted in yellow background.

---

CHART B1 — Safety Breakdown (Pie Chart)
    Three slices: حادثه (red), شبه حادثه (yellow), بدون حادثه (green)
    Values = number of days for each.

CHART B2 — Safety Trend Over Time (Stacked Bar)
    X-axis = Date (or week/month if many days)
    Y-axis = Count
    Stacked: green = NoIncident, yellow = NearMiss, red = Incident
    Shows how safety status evolved.

CHART B3 — Cumulative Incident Count (Line Chart)
    X-axis = Date
    Y-axis = Running total of incidents
    A rising line; the steeper it rises, the worse the safety trend.

CHART B4 — Inspection Compliance (Gauge or Single Number)
    Show inspection_rate % as a big number or gauge.
    Green ≥ 90%, yellow 70-89%, red < 70%.

=============================================================================
DATE RANGE FILTER
=============================================================================

Two date pickers at the top, shared by both sections.

=============================================================================
EXPORT
=============================================================================

Two buttons: [Export Excel] [Export PDF]

Excel:
    - Sheet 1: "Issues Summary" — table A1
    - Sheet 2: "Issues Log" — table A2
    - Sheet 3: "Safety Summary" — table B1
    - Sheet 4: "Safety Log" — table B2
    File name: "{project_name}_problems_safety_{from}_{to}.xlsx"

PDF:
    - Title page
    - Section A: issues summary table + charts A1-A4
    - Section B: safety summary table + charts B1-B4
    File name: "{project_name}_problems_safety_{from}_{to}.pdf"

Export modal: date range, which sections (Issues / Safety / Both),
             charts checkboxes, language.

=============================================================================
FUNCTION SIGNATURE
=============================================================================

class ProblemsAnalysis:

    def __init__(self, data_service: DataService, project_config: dict):
        ...

    # --- Issues ---
    def get_issues_summary(self) -> list[dict]:
        # One dict per issue_type with counts and percentages
        ...

    def get_issues_log(self) -> list[dict]:
        # Full flat table of all issues
        ...

    def get_days_with_vs_without_issues(self) -> dict:
        # {"with_issues": N, "without_issues": M, "total_days": T}
        ...

    def get_issues_by_location(self) -> list[dict]:
        # [{station_range, count}, ...]
        ...

    # --- Safety ---
    def get_safety_summary(self) -> dict:
        # Single dict with all metrics from table B1
        ...

    def get_safety_log(self) -> list[dict]:
        # Full flat table of all safety records
        ...

    def get_safety_breakdown(self) -> dict:
        # {"Incident": N, "NearMiss": M, "NoIncident": K}
        ...

    def get_safety_trend(self) -> list[dict]:
        # [{date, incident_count, near_miss_count, no_incident_count}, ...]
        ...

    def get_cumulative_incidents(self) -> list[dict]:
        # [{date, cumulative_incidents}, ...]
        ...
"""