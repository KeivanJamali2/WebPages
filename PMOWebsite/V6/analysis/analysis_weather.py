"""
=============================================================================
ANALYSIS: Weather & Climate Impact (آب‌وهوا و تأثیر اقلیمی)
=============================================================================

GOAL:
    Visualise temperature, humidity, and weather conditions throughout the
    project, and cross-reference weather data with issues / work output to
    understand how climate affects project performance.

=============================================================================
DATA SOURCES
=============================================================================

1. ClimateCondition table (via DataService.get_climate_conditions()):
   Each row = one day's weather record.
   Fields:
       - form_date       (str, ISO date)
       - min_temperature  (float, °C)
       - max_temperature  (float, °C)
       - humidity         (float, % — 0-100)
       - weather_type     (str — "clear" / "cloudy" / "rainy" / "foggy" / "snowy")
       - wind_speed       (str — "fast" / "normal" / "slow")
       - climate_effect   (str — "no_effect" / "slow_progress" / "stopped")

2. ProjectIssue table (via DataService.get_project_issues()):
   Used for cross-referencing: do issues increase on bad-weather days?
   Fields: form_date, issue_type, effect, ...

3. ConstructionOperation table (via DataService.get_construction_operations()):
   Used for cross-referencing: does work output drop on bad-weather days?
   Fields: form_date, operation_type, amount, ...

4. Safety table (via DataService.get_safety_records()):
   Used for cross-referencing: do incidents correlate with weather?
   Fields: form_date, safety_situation, incident_occurred, ...

=============================================================================
MAIN TABLE — Daily Weather Log
=============================================================================

    | Date | Min Temp (°C) | Max Temp (°C) | Humidity (%) |
    | Weather Type | Wind Speed | Climate Effect on Project |
    | Issues That Day (count) | Work Output That Day (total amount) |

Sortable by any column.  Default sort: date ascending.
Rows where climate_effect == "stopped" highlighted in red.
Rows where climate_effect == "slow_progress" highlighted in yellow.

=============================================================================
SUMMARY TABLE — Weather Statistics
=============================================================================

    | Metric                              | Value                |
    |-------------------------------------|----------------------|
    | Total Reporting Days                | ...                  |
    | Avg Min Temperature                 | ... °C               |
    | Avg Max Temperature                 | ... °C               |
    | Min Temperature Recorded            | ... °C (on date ...) |
    | Max Temperature Recorded            | ... °C (on date ...) |
    | Avg Humidity                        | ... %                |
    | Days: Clear (صاف)                   | ...                  |
    | Days: Cloudy (ابری)                 | ...                  |
    | Days: Rainy (بارانی)                | ...                  |
    | Days: Foggy (مه‌آلود)               | ...                  |
    | Days: Snowy (برفی)                  | ...                  |
    | Days with No Effect on Work         | ...                  |
    | Days with Slow Progress             | ...                  |
    | Days with Work Stopped              | ...                  |
    | % Days Weather Impacted Work        | (slow + stopped) / total × 100 |

=============================================================================
CROSS-REFERENCE TABLE — Weather vs Performance
=============================================================================

Group days by weather_type.  For each weather type:

    | Weather Type | Avg Work Output | Avg Issue Count | Incident Rate |
    | Avg Min Temp | Avg Max Temp | Avg Humidity |

This shows, for example:
    - On "rainy" days, avg work output was 1500 m³ vs 2900 m³ on "clear" days.
    - On "foggy" days, incident rate was 20% vs 5% on "clear" days.

Similarly, group by climate_effect:

    | Climate Effect | Days | Avg Work Output | Avg Issues | Avg Temp Range |

=============================================================================
DATE RANGE FILTER
=============================================================================

Two date pickers: [From Date] — [To Date]

=============================================================================
CHARTS / PLOTS
=============================================================================

CHART 1 — Temperature Trend (Dual Line Chart)
    X-axis = Date
    Y-axis = Temperature (°C)
    Two lines:
        - Red line   = max_temperature
        - Blue line  = min_temperature
    Shaded area between them = daily temperature range.
    Optional: horizontal dashed lines at 0°C and 40°C for reference.

CHART 2 — Humidity Trend (Line Chart)
    X-axis = Date
    Y-axis = Humidity (%)
    Single line.  Background shading: light blue > 80%, light yellow < 30%.

CHART 3 — Weather Type Distribution (Pie Chart)
    Slices = weather_type values
    Colours: clear=☀️gold, cloudy=grey, rainy=blue, foggy=purple, snowy=white-blue.

CHART 4 — Climate Effect on Work (Stacked Bar)
    X-axis = Date (or week if many days)
    Y-axis = Count (always 1 per day, stacked)
    Three colours: green = no_effect, yellow = slow_progress, red = stopped.
    Shows the timeline of weather impact.

CHART 5 — Weather vs Work Output (Grouped Bar)
    X-axis = Weather type
    Y-axis = Average daily work output (sum of all operation amounts)
    One bar per weather type.
    Clear visual of how much work gets done under each condition.

CHART 6 — Weather vs Issues (Grouped Bar)
    X-axis = Weather type
    Y-axis = Average number of issues per day
    One bar per weather type.

CHART 7 — Temperature vs Work Output (Scatter Plot — optional/advanced)
    X-axis = Max temperature
    Y-axis = Total work output that day
    Each dot = one day.  Colour = weather_type.
    Helps spot if extreme heat/cold reduces output.

=============================================================================
EXPORT
=============================================================================

Two buttons: [Export Excel] [Export PDF]

Excel:
    - Sheet 1: "Weather Log" — full daily weather table with issue/work counts
    - Sheet 2: "Weather Statistics" — summary metrics table
    - Sheet 3: "Weather vs Performance" — cross-reference tables
    File name: "{project_name}_weather_{from}_{to}.xlsx"

PDF:
    - Title page
    - Summary statistics table
    - All charts
    - Cross-reference tables
    File name: "{project_name}_weather_{from}_{to}.pdf"

Export modal: date range, charts checkboxes, language.

=============================================================================
FUNCTION SIGNATURE
=============================================================================

class WeatherAnalysis:

    def __init__(self, data_service: DataService, project_config: dict):
        ...

    def get_daily_log(self) -> list[dict]:
        # Full daily table with weather + issue counts + work output
        ...

    def get_summary_stats(self) -> dict:
        # Single dict with all summary metrics
        ...

    def get_weather_vs_performance(self) -> list[dict]:
        # [{weather_type, avg_work_output, avg_issues, incident_rate, ...}, ...]
        ...

    def get_climate_effect_breakdown(self) -> list[dict]:
        # [{climate_effect, days, avg_output, avg_issues, avg_temp_range}, ...]
        ...

    def get_temperature_trend(self) -> list[dict]:
        # [{date, min_temp, max_temp}, ...]
        ...

    def get_humidity_trend(self) -> list[dict]:
        # [{date, humidity}, ...]
        ...

    def get_weather_distribution(self) -> dict:
        # {"clear": N, "cloudy": M, "rainy": K, ...}
        ...
"""