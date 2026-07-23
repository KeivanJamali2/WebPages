"""
=============================================================================
ANALYSIS: Tools & Equipment (ماشین‌آلات و تجهیزات)
=============================================================================

GOAL:
    Full table of every tool/equipment — usage hours, active/inactive/repair
    status breakdown, costs — plus charts to quickly spot equipment with the
    most downtime, highest cost, or lowest utilisation.

=============================================================================
DATA SOURCES
=============================================================================

1. ToolEquipment table (via DataService.get_tools_equipment()):
   Each row = one equipment entry for one day.
   Fields:
       - form_date           (str, ISO date)
       - equipment_type      (str — e.g. "بیل مکانیکی", "لودر")
       - equipment_model     (str | None — e.g. "ده چرخ", "GPS")
       - equipment_name      (str — "type - model" combined, for display)
       - count_active        (int — how many units were active that day)
       - working_hours       (float — hours worked per unit that day)
       - situation           (str — "Active" / "Inactive" / "Under Repair")
       - inactivity_reason   (str | None — reason if not active)

2. Project config (via DataService.get_project_config()):
   - config["Tools_And_Equipments"]  →  { type: [models] }
   - config["Equipment_Costs"]       →  { type: { model: {"planned_quantity": Y, "hourly_rate": X (optional)} } }
   The hourly_rate is in Rial per hour per machine (may be 0 or absent if not available).

=============================================================================
MAIN TABLE — Equipment Summary
=============================================================================

Group rows by equipment_type (with sub-rows for each equipment_model if exists).
Columns:

    | Equipment Type | Model | Total Days Reported |
    | Days Active | Days Inactive | Days Under Repair |
    | Active % | Inactive % | Repair % |
    | Total Units·Days (Σ count_active) | Total Hours Worked (Σ count_active × working_hours) |
    | Hourly Rate | Total Cost (hours × hourly_rate) |
    | Planned Qty | Avg Active/Day vs Planned % |

Definitions:
    - Days Active       = count of form_dates where situation == "Active"
    - Days Inactive     = count of form_dates where situation == "Inactive"
    - Days Under Repair = count of form_dates where situation == "Under Repair"
    - Active %          = Days Active / Total Days Reported × 100
    - Total Cost        = Σ (count_active × working_hours × hourly_rate) across all dates
    - Avg Active/Day    = Total Units·Days / Total Days Reported
    - Planned %         = (Avg Active/Day / planned_quantity) × 100

Sorting: default by Total Cost descending.

=============================================================================
DETAIL TABLE — Daily Breakdown
=============================================================================

Collapsible per equipment_type+model:

    | Date | Count Active | Working Hours | Situation | Inactivity Reason | Daily Cost |

=============================================================================
INACTIVITY LOG TABLE
=============================================================================

A separate filtered table showing ONLY rows where situation ≠ "Active":

    | Date | Equipment | Model | Situation | Reason | Duration (if consecutive days) |

"Duration" = count of consecutive dates where this same equipment stayed
in the same non-active situation.  This helps spot chronic repair issues.

=============================================================================
UNIT CONVERSION FILTER
=============================================================================

Dropdown: [ Per Day | Per Week | Per Month | Per Hour ]
Affects: average hours, average cost, chart Y-axes.
    Per Day   → daily average
    Per Hour  → daily_avg / 8
    Per Week  → daily_avg × 7
    Per Month → daily_avg × 30

=============================================================================
DATE RANGE FILTER
=============================================================================

Two date pickers: [From Date] — [To Date]

=============================================================================
CHARTS / PLOTS
=============================================================================

CHART 1 — Equipment Status Distribution (Stacked Horizontal Bar)
    Y-axis = Equipment name (type + model)
    X-axis = Number of days
    Stacked bars: green = Active, orange = Inactive, red = Under Repair
    Sorted by "repair %" descending (worst at top).

CHART 2 — Top Equipment by Cost (Horizontal Bar)
    Y-axis = Equipment name
    X-axis = Total cost (Rial)
    Sorted descending.

CHART 3 — Utilisation Rate vs Planned (Grouped Bar)
    Y-axis = Equipment type
    Two bars per type: "Avg Active/Day" (actual) and "Planned Qty" (target)
    Colours: blue = actual, grey dashed = planned.

CHART 4 — Daily Active Equipment Count (Stacked Area)
    X-axis = Date
    Y-axis = count_active
    Stacked by equipment_type.

CHART 5 — Cost Trend Over Time (Line Chart)
    X-axis = Date
    Y-axis = total daily equipment cost
    Single line.

CHART 6 — Repair Frequency (Bar Chart)
    X-axis = Equipment name
    Y-axis = Number of "Under Repair" days
    Only showing equipment that had at least 1 repair day.

=============================================================================
EXPORT
=============================================================================

Two buttons: [Export Excel] [Export PDF]

Excel:
    - Sheet 1: "Equipment Summary" — main table
    - Sheet 2: "Daily Detail" — flat: (date, type, model, count, hours, situation, reason, cost)
    - Sheet 3: "Inactivity Log" — filtered non-active rows with duration
    File name: "{project_name}_equipment_{from}_{to}.xlsx"

PDF:
    - Title page
    - Summary table
    - All charts
    - Inactivity log table
    File name: "{project_name}_equipment_{from}_{to}.pdf"

Export modal: date range, unit, charts checkboxes, language.

=============================================================================
FUNCTION SIGNATURE
=============================================================================

class ToolsEquipmentAnalysis:

    def __init__(self, data_service: DataService, project_config: dict):
        ...

    def get_summary_table(self, unit: str = "per_day") -> list[dict]:
        # One dict per equipment_type+model with all summary columns
        ...

    def get_daily_detail(self, equipment_type: str | None = None) -> list[dict]:
        # Daily rows, optionally filtered by type
        ...

    def get_inactivity_log(self) -> list[dict]:
        # Non-active rows with consecutive-day duration
        ...

    def get_status_distribution(self) -> list[dict]:
        # [{equipment, days_active, days_inactive, days_repair}, ...]
        ...

    def get_cost_by_equipment(self) -> list[dict]:
        # [{equipment, total_cost}, ...]
        ...

    def get_utilisation_vs_planned(self) -> list[dict]:
        # [{equipment, avg_active_per_day, planned_qty, utilisation_pct}, ...]
        ...

    def get_daily_cost_trend(self) -> list[dict]:
        # [{date, total_cost}, ...]
        ...

    def get_repair_frequency(self) -> list[dict]:
        # [{equipment, repair_days}, ...]
        ...
"""