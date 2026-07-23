"""
=============================================================================
ANALYSIS: Materials & Resources (مصالح و منابع)
=============================================================================

GOAL:
    Show incoming materials, how much has been used vs stored, storage
    duration per material type, costs, and consumption trends — so the
    manager can spot shortages, over-stocking, and cost issues.

=============================================================================
DATA SOURCES
=============================================================================

1. IncomingMaterial table (via DataService.get_incoming_materials()):
   Each row = one material's record for one day.
   Fields:
       - form_date            (str, ISO date)
       - material_type        (str — e.g. "شن و ماسه", "آب عملیات خاکی")
       - material_unit        (str — e.g. "تن (ton)", "متر مکعب (m³)")
       - incoming_amount      (float — quantity received that day)
       - cumulative_incoming  (float — running total received up to that day)
       - used_amount          (float — quantity consumed that day)
       - cumulative_used      (float — running total consumed up to that day)
       - storage_place        (str — where it's stored)
       - waybill_number       (str — delivery document number)

2. Project config (via DataService.get_project_config()):
   - config["Incoming_Materials"]  →  { material_name: unit }
   - config["Material_Prices"]     →  { material_name: {"price_per_unit": X, "planned_total": Y} }

=============================================================================
MAIN TABLE — Materials Summary
=============================================================================

One row per material_type.  Columns:

    | # | Material | Unit | Total Incoming | Total Used |
    | Current Stock (incoming − used) | Planned Total |
    | Incoming % of Plan (incoming / planned × 100) |
    | Usage % of Incoming (used / incoming × 100) |
    | Price/Unit | Total Incoming Cost | Total Used Cost |
    | Avg Storage Days (see below) |

Definitions:
    - Total Incoming     = Σ incoming_amount  OR  max(cumulative_incoming)
    - Total Used         = Σ used_amount      OR  max(cumulative_used)
    - Current Stock      = Total Incoming − Total Used
    - Avg Storage Days:
        For each delivery batch (each form_date with incoming_amount > 0),
        calculate how many days until that amount was consumed.
        Simplification: (Current Stock × total_days) / Total Incoming
        gives average age of inventory in days.
    - Total Incoming Cost = Total Incoming × price_per_unit
    - Total Used Cost     = Total Used × price_per_unit

Sorting: default by Total Incoming Cost descending (most expensive first).

=============================================================================
STOCK DETAIL TABLE
=============================================================================

Collapsible per material_type:

    | Date | Incoming | Used | Cumulative In | Cumulative Used |
    | Stock Balance (cum_in − cum_used) | Waybill | Storage Place |

=============================================================================
STORAGE ALERT TABLE
=============================================================================

A separate table showing materials with concerning stock levels:

    | Material | Current Stock | Stock/Incoming Ratio | Avg Storage Days | Alert Level |

Alert Level:
    - 🔴 Critical:  stock == 0 and incoming < planned_total
    - 🟡 Low:       stock < 10% of total incoming
    - 🟢 High:      stock > 50% of total incoming (possible over-stocking)
    - ⚪ Normal:     everything else

=============================================================================
UNIT CONVERSION FILTER
=============================================================================

Dropdown: [ Per Day | Per Week | Per Month | Per Hour ]
Affects: "Avg incoming/period", "Avg usage/period", chart Y-axes.
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

CHART 1 — Incoming vs Used by Material (Grouped Bar)
    Y-axis = Material name
    X-axis = Amount
    Two bars per material: blue = Total Incoming, red = Total Used
    Gap between them = current stock.

CHART 2 — Current Stock Levels (Horizontal Bar)
    Y-axis = Material name
    X-axis = Current Stock amount
    Bars coloured by alert level (red / yellow / green).
    Sorted by stock amount ascending (lowest first → most at risk).

CHART 3 — Cumulative Incoming vs Used Over Time (Line Chart, per material)
    A dropdown to select which material to view.
    X-axis = Date
    Y-axis = Cumulative amount
    Two lines: solid = cumulative incoming, dashed = cumulative used
    The gap between lines = stock at any point in time.

CHART 4 — Cost Breakdown by Material (Pie / Donut)
    Slices = material types
    Value  = Total Incoming Cost
    Show top 10, group rest as "Others".

CHART 5 — Materials with Most Storage Days (Horizontal Bar)
    Y-axis = Material name
    X-axis = Average storage days
    Sorted descending — materials sitting in storage longest at top.

CHART 6 — Daily Incoming vs Usage Trend (Stacked Bar)
    X-axis = Date
    Y-axis = Total amount (all materials summed)
    Two stacked groups: incoming (positive) vs used (negative or separate colour)

=============================================================================
EXPORT
=============================================================================

Two buttons: [Export Excel] [Export PDF]

Excel:
    - Sheet 1: "Materials Summary" — the main summary table
    - Sheet 2: "Daily Detail" — flat: (date, material, incoming, used, cum_in, cum_used, stock, waybill, storage_place)
    - Sheet 3: "Stock Alerts" — the alert table
    - Sheet 4: "Cost Analysis" — material, price/unit, total_in_cost, total_used_cost
    File name: "{project_name}_materials_{from}_{to}.xlsx"

PDF:
    - Title page
    - Summary table
    - All charts
    - Stock alerts table
    File name: "{project_name}_materials_{from}_{to}.pdf"

Export modal: date range, unit, charts checkboxes, language.

=============================================================================
FUNCTION SIGNATURE
=============================================================================

class MaterialsAnalysis:

    def __init__(self, data_service: DataService, project_config: dict):
        ...

    def get_summary_table(self, unit: str = "per_day") -> list[dict]:
        # One dict per material_type
        ...

    def get_daily_detail(self, material_type: str | None = None) -> list[dict]:
        # Daily rows, optionally filtered
        ...

    def get_stock_alerts(self) -> list[dict]:
        # [{material, current_stock, ratio, avg_storage_days, alert_level}, ...]
        ...

    def get_incoming_vs_used(self) -> list[dict]:
        # [{material, total_incoming, total_used, current_stock}, ...]
        ...

    def get_cumulative_trend(self, material_type: str) -> list[dict]:
        # [{date, cumulative_incoming, cumulative_used, stock}, ...]
        ...

    def get_cost_breakdown(self) -> list[dict]:
        # [{material, total_incoming_cost, total_used_cost}, ...]
        ...

    def get_storage_days(self) -> list[dict]:
        # [{material, avg_storage_days}, ...]
        ...
"""