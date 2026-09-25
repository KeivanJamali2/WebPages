import re
import os
import jdatetime
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from pathlib import Path
from collections import Counter
from collections import defaultdict
from matplotlib.gridspec import GridSpec
from Plot_Config import configure_matplotlib_for_persian, reshape_text

# Import database module if available
try:
    from database import HamiDatabase, get_database
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

configure_matplotlib_for_persian(font_size=14, font_family="sans-serif")

# Shared color palette so every plot in the app looks visually consistent.
# 4-panel charts cycle through all 4 colors.
PLOT_PALETTE = ['orange', 'skyblue', 'lightgreen', 'salmon']
# Charts with a single data series use this color.
PLOT_SINGLE_COLOR = PLOT_PALETTE[1]  # skyblue

# Bands for the absolute 0-100 performance score: (low, high, color).
SCORE_BANDS = [(0, 40, '#d9534f'), (40, 60, '#f0ad4e'),
               (60, 80, '#9fd39f'), (80, 100, '#5cb85c')]


def band_color(score: float) -> str:
    """Color for a 0-100 score, so a bar's height and its color say the same thing."""
    for low, high, color in SCORE_BANDS:
        if score < high:
            return color
    return SCORE_BANDS[-1][2]


def zscore(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    """Standardise a metric against its own cohort, negated when a lower raw value is better."""
    sd = series.std(ddof=1)
    if not sd or np.isnan(sd):
        # One person, or everyone identical: no spread left to standardise.
        z = pd.Series(0.0, index=series.index)
    else:
        z = (series - series.mean()) / sd
    return z if higher_is_better else -z


def volume_score(rate, target: float, shape: float, credit_at_target: float):
    """
    Workload credited on a saturating curve: hitting `target` scores `credit_at_target`.

    More work always scores higher, with diminishing returns and an unreachable ceiling of
    100, so carrying a heavy caseload is rewarded without letting it buy past bad service.
    """
    beta = (100.0 - credit_at_target) / credit_at_target
    r = (np.asarray(rate, dtype=float) / float(target)) ** shape
    return 100.0 * r / (r + beta)


def normalise_weights(weights: dict, keys) -> dict:
    """Rescale the weights of the metrics actually available so they still sum to 1."""
    used = {key: weights[key] for key in keys}
    total = sum(used.values())
    if not total:
        return {key: 1 / len(used) for key in used}
    return {key: value / total for key, value in used.items()}


def legend_with_headroom(ax, headroom: float = 0.22, **legend_kwargs):
    """
    Add a legend in the upper-right corner without covering the bars.

    Every bar chart here prints a value label just above each bar, so a plain
    'upper right' legend lands on top of them. Expanding the y-limit first keeps
    that corner clear no matter what the data looks like.
    """
    ax.set_ylim(top=ax.get_ylim()[1] * (1 + headroom))
    legend_kwargs.setdefault('loc', 'upper right')
    legend_kwargs.setdefault('framealpha', 0.95)
    return ax.legend(**legend_kwargs)


class SQLiteAnalyzer:
    """
    Optimized analyzer that queries SQLite database directly.
    Much faster than loading all data into memory.
    """
    
    # Define major categories for field grouping
    # Order matters! First match wins. Put keshavarzi before pezeshki 
    # so "گیاه پزشکی" matches keshavarzi (via "گیاه") before pezeshki (via "پزشکی")
    RAVAN_SHENASI = ["روانشناسی", "روان_شناسی", "روان شناسی"]
    SANAIE_GAZAII = ["غذا"]
    MODIRIAT_SANATI = ["مهندسی صنایع", "محیط زیست", "محیط_زیست", "صنایع"]
    ZABAN = ["زبان"]
    MODIRIAT_AMOZESHI = ["مدیریت آموزشی", "مدیریت_آموزشی", "ابتدایی", "آموزش"]
    TARBIAT_BADANI = ["تربیت بدنی", "تربیت_بدنی", "ورزشی", "ورزش"]
    GORAN = ["قرآن", "قران"]
    BARG = ["برق"]
    SHIMI = ["شیمی"]
    HOGOG = ["حقوق"]
    MECHANIC = ["مکانیک", "مکاترونیک"]
    GOGRAFIA = ["جغرافیا"]
    KESHAVARZI = ["کشاورزی", "گیاه"]
    MOHANDESI_PEZESHKI = ["مهندسی پزشکی"]
    PEZESHKI = ["پزشکی"]
    COMPUTER = ["کامپیوتر"]
    EGTESAD = ["اقتصاد"]
    NASAJI = ["نساجی"]
    ADABIAT = ["ادبیات"]
    MOSHAVERE = ["مشاوره"]
    OMRAN = ["عمران", "ساخت"]
    HONAR = ["هنر", "مرمت", "نقاشی", "گرافیک", "طراحی", "پارچه", "تصویری", "معماری", "شهری"]
    MICROBIOLOGY = ["میکروبیولوژی", "بیوتکنولوژی", "زیست فناوری"]
    MAVAD = ["مواد", "متالورژی"]
    PARASTARI = ["پرستاری"]
    OTAG_AMAL = ["اتاق عمل"]
    HOSHBARI = ["هوشبری"]
    MODIRIAT = ["مدیریت", "مدیریتی"]
    OLOM_ERTEBATAT = ["علوم ارتباطات", "ارتباطات", "رسانه"]
    HESABDARI = ["حسابداری", "مالی"]
    OLOM_TARBIATI = ["علوم تربیتی", "تربیتی"]
    MAHARAT = ["مهارت"]
    
    # List of all majors in priority order (first match wins)
    RESHTE_HA = [
        RAVAN_SHENASI, SANAIE_GAZAII, MODIRIAT_SANATI, ZABAN, MODIRIAT_AMOZESHI, 
        TARBIAT_BADANI, GORAN, BARG, SHIMI, HOGOG, MECHANIC, GOGRAFIA, KESHAVARZI, 
        MOHANDESI_PEZESHKI, PEZESHKI, COMPUTER, EGTESAD, NASAJI, ADABIAT, MOSHAVERE, 
        OMRAN, HONAR, MICROBIOLOGY, MAVAD, OLOM_ERTEBATAT, PARASTARI, OTAG_AMAL, 
        HOSHBARI, MODIRIAT, OLOM_TARBIATI, HESABDARI, MAHARAT
    ]
    
    # Faculty groupings (uses first element of each major as the key name)
    FACULTY = {"تعلیم و تربیت": RAVAN_SHENASI+MODIRIAT_AMOZESHI+MOSHAVERE+ZABAN+OLOM_TARBIATI,
                "علوم انسانی": MODIRIAT_SANATI+GORAN+HOGOG+HESABDARI+EGTESAD+ADABIAT+OLOM_ERTEBATAT+MODIRIAT,
                "پزشکی": PEZESHKI+PARASTARI+OTAG_AMAL+HOSHBARI,
                "فنی و مهندسی": SHIMI+MECHANIC+NASAJI+OMRAN+KESHAVARZI+SANAIE_GAZAII+MICROBIOLOGY+MAVAD,
                "مهارت و فناوری": MAHARAT,
                "هنر و معماری": TARBIAT_BADANI+GOGRAFIA+HONAR,
                "هوش مصنوعی": BARG+MOHANDESI_PEZESHKI+COMPUTER
                }   
    
    def __init__(self, db: 'HamiDatabase', plot_folder: Path, csv_folder: Path,
                 start_date: jdatetime.datetime = None, end_date: jdatetime.datetime = None,
                 cities: list = None, faculty_totals: dict = None):
        self.db = db
        self.plot_path = plot_folder
        self.csv_path = csv_folder
        self.start_date = start_date
        self.end_date = end_date
        self.cities = cities or None  # None/empty list = no filter, all cities
        # {faculty name: total students} entered by the user on the analysis page,
        # used to show each faculty's request count as a percentage of its students.
        self.faculty_totals = faculty_totals or {}

        if not self.plot_path.exists():
            self.plot_path.mkdir(parents=True, exist_ok=True)
        if not self.csv_path.exists():
            self.csv_path.mkdir(parents=True, exist_ok=True)
        
        # Cache for computed values
        self._places = None
        self._employees = None
        self._students = None
        self._people_index = None
    
    @property
    def start_date_str(self) -> str:
        """Convert start_date to string format for database queries."""
        if self.start_date:
            return self.start_date.strftime('%Y-%m-%d')
        return None
    
    @property
    def end_date_str(self) -> str:
        """Convert end_date to string format for database queries."""
        if self.end_date:
            return self.end_date.strftime('%Y-%m-%d')
        return None
    
    @property
    def people_index(self) -> dict:
        """Load hami_id -> full_name mapping from the database (editable from the website)."""
        if self._people_index is None:
            self._people_index = self.db.get_hami_names()
        return self._people_index

    def _period_days(self) -> int:
        """
        Length of the analysis window in days.

        The volume and confidence figures are rates per 30 days, so a window with no
        dates set still needs a length: fall back to the span the messages actually cover
        rather than silently scoring a multi-year database as if it were one month.
        """
        if self.start_date and self.end_date:
            return max((self.end_date - self.start_date).days, 1)
        days = self.db.get_message_count_by_date(group_by='day', start_date=self.start_date_str,
                                                 end_date=self.end_date_str, cities=self.cities)
        if not days:
            return 30
        first = jdatetime.datetime.strptime(min(days), '%Y-%m-%d')
        last = jdatetime.datetime.strptime(max(days), '%Y-%m-%d')
        return max((last - first).days, 1)

    @property
    def places(self) -> list:
        if self._places is None:
            self._places = self.db.get_all_places()
        return self._places
    
    @property
    def employees(self) -> list:
        if self._employees is None:
            self._employees = self.db.get_all_employees()
        return self._employees
    
    @property
    def students(self) -> list:
        if self._students is None:
            self._students = self.db.get_all_students()
        return self._students
    
    def total_requests_per_hami(self, plot: bool = False, show_reference: bool = True) -> pd.Series:
        """Get total requests per hami - direct SQL query."""
        counts = self.db.get_requests_count_per_hami(start_date=self.start_date_str, end_date=self.end_date_str,
                                                       cities=self.cities)
        result = pd.Series(counts).sort_values(ascending=False)

        result.to_csv(self.csv_path / 'total_requests_per_hami.csv', index=True, encoding="utf-8-sig")

        # Requests whose hami could not be identified are not a real hami: keep them
        # in the CSV export but leave them out of the chart and its reference table.
        result = result.drop('unknown', errors='ignore')

        if plot:
            fig = plt.figure(figsize=(14, 8))
            gs = GridSpec(1, 2, width_ratios=[3, 1], figure=fig)

            ax = fig.add_subplot(gs[0])
            bars = ax.bar(range(len(result)), result.values,
                         color=PLOT_SINGLE_COLOR, edgecolor='navy', alpha=0.7)

            for i, v in enumerate(result.values):
                ax.text(i, v, str(v), ha='center', fontsize=12, fontweight='bold')

            ax.set_title('Total Requests per Hami', fontsize=12, pad=20)
            ax.set_xlabel("Hami ID", fontsize=10)
            ax.set_ylabel('Requests', fontsize=10)
            ax.set_xticks(range(len(result)))
            ax.set_xticklabels(result.index, rotation=45, ha='right')
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)

            if show_reference:
                ref_ax = fig.add_subplot(gs[1])
                self._add_reference_table(ref_ax, max_rows=25, ids=result.index.tolist())

            plt.tight_layout()
            plt.savefig(self.plot_path / 'total_requests_per_hami.png', dpi=300, bbox_inches='tight')
            plt.close()

        return result

    def total_requests_per_city(self, plot: bool = False) -> pd.Series:
        """Get total requests per city - direct SQL query."""
        counts = self.db.get_requests_count_per_city(start_date=self.start_date_str, end_date=self.end_date_str)
        result = pd.Series(counts).sort_values(ascending=False)

        result.to_csv(self.csv_path / 'total_requests_per_city.csv', index=True, encoding="utf-8-sig")

        if plot:
            fig, ax = plt.subplots(figsize=(14, 8))

            ax.bar(range(len(result)), result.values,
                   color=PLOT_SINGLE_COLOR, edgecolor='navy', alpha=0.7)

            for i, v in enumerate(result.values):
                ax.text(i, v, str(v), ha='center', fontsize=12, fontweight='bold')

            ax.set_title(reshape_text('Total Requests per City'), fontsize=12, pad=20)
            ax.set_xlabel(reshape_text('City'), fontsize=10)
            ax.set_ylabel('Requests', fontsize=10)
            ax.set_xticks(range(len(result)))
            ax.set_xticklabels([reshape_text(str(c)) for c in result.index], rotation=45, ha='right')
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)

            plt.tight_layout()
            plt.savefig(self.plot_path / 'total_requests_per_city.png', dpi=300, bbox_inches='tight')
            plt.close()

        return result
    
    def message_date_distribution(self, plot: bool = False, per: str = 'month') -> pd.Series:
        """Get message/request date distribution - direct SQL aggregation."""
        
        if per == 'month_request':
            # Request count per month
            counts = self.db.get_request_count_by_month(start_date=self.start_date_str, end_date=self.end_date_str,
                                                          cities=self.cities)
        else:
            # Message count per day or month
            counts = self.db.get_message_count_by_date(group_by=per, start_date=self.start_date_str, end_date=self.end_date_str,
                                                         cities=self.cities)
        
        result = pd.Series(counts).sort_index()
        
        # Save CSVs
        if per == 'day':
            result.to_csv(self.csv_path / 'message_count_per_day.csv', index=True, encoding="utf-8-sig")
        elif per == 'month':
            result.to_csv(self.csv_path / 'message_count_per_month.csv', index=True, encoding="utf-8-sig")
        else:
            result.to_csv(self.csv_path / 'request_count_per_month.csv', index=True, encoding="utf-8-sig")
        
        t = "Request" if per == "month_request" else "Message"
        
        if plot:
            fig = plt.figure(figsize=(14, 8))
            ax = fig.add_subplot(111)
            
            unit = 'Days' if per == 'day' else 'Months'
            bars = ax.bar(range(len(result)), result.values,
                         color=PLOT_SINGLE_COLOR, edgecolor='navy', alpha=0.7,
                         label=f'Total {t}s: {int(result.sum()):,}\n{unit}: {len(result)}')

            for i, v in enumerate(result.values):
                ax.text(i, v, str(v), ha='center', fontsize=12, fontweight='bold')

            ax.set_title(f'{t} Count per Jalali {per.capitalize()}', fontsize=12, pad=20)
            ax.set_xlabel(f'Jalali {per.capitalize()}', fontsize=10)
            ax.set_ylabel(f'Number of {t}s', fontsize=10)
            ax.set_xticks(range(len(result)))
            ax.set_xticklabels(result.index, rotation=45, ha='right')
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)
            legend_with_headroom(ax, fontsize=11)
            
            plt.tight_layout()
            # Use correct filename based on type
            if per == 'month_request':
                plot_filename = 'request_count_per_jalali_month.png'
            else:
                plot_filename = f'message_count_per_jalali_{per}.png'
            plt.savefig(self.plot_path / plot_filename, dpi=300, bbox_inches='tight')
            plt.close()
        
        return result
    
    def top_communicators_for_employee(self, if_plot: bool = False, n: int = 10):
        """
        Get top employee communicators based on REQUEST CONTEXT.
        
        An EMPLOYEE message is when someone sends on ANOTHER person's request.
        This handles the edge case where "حسن نظری" could be both a student 
        (when sending on their own request) and an employee (when sending on 
        other people's requests).
        
        - Employee SENDERS: People who send messages on other people's requests
        - Employee RECEIVERS: People who receive at non-student emails
        """
        
        # Get by messages using proper context-based stats
        senders_m, receivers_m = self.db.get_employee_stats_proper(by_messages=True, start_date=self.start_date_str, end_date=self.end_date_str, cities=self.cities)

        senders_employee_m = pd.Series(senders_m).sort_values(ascending=False)
        receivers_employee_m = pd.Series(receivers_m).sort_values(ascending=False)

        self.senders_employee_m = senders_employee_m
        self.receivers_employee_m = receivers_employee_m

        senders_employee_m.to_csv(self.csv_path / 'top_employee_senders_by_messages.csv', index=True, encoding="utf-8-sig")
        receivers_employee_m.to_csv(self.csv_path / 'top_employee_receivers_by_messages.csv', index=True, encoding="utf-8-sig")

        # Get by requests using proper context-based stats
        senders_r, receivers_r = self.db.get_employee_stats_proper(by_messages=False, start_date=self.start_date_str, end_date=self.end_date_str, cities=self.cities)
        
        senders_employee_r = pd.Series(senders_r).sort_values(ascending=False)
        receivers_employee_r = pd.Series(receivers_r).sort_values(ascending=False)
        
        self.senders_employee_r = senders_employee_r
        self.receivers_employee_r = receivers_employee_r
        
        senders_employee_r.to_csv(self.csv_path / 'top_employee_senders_by_requests.csv', index=True, encoding="utf-8-sig")
        receivers_employee_r.to_csv(self.csv_path / 'top_employee_receivers_by_requests.csv', index=True, encoding="utf-8-sig")
        
        if if_plot:
            self._plot_communicators(
                receivers_employee_m.head(n), receivers_employee_r.head(n),
                senders_employee_m.head(n), senders_employee_r.head(n),
                'Employee', n, 'top_employees.png'
            )
            self._plot_requests_received_vs_answered(
                receivers_employee_r, senders_employee_r, n,
                'employee_requests_received_vs_answered.png'
            )
    
    def top_communicators_for_student(self, if_plot: bool = False, n: int = 10):
        """
        Get top student communicators - direct SQL query.
        
        Students are defined as people who made requests (names in requests table).
        - Student SENDERS: Students who sent messages
        - Student RECEIVERS: Students who received messages (at student email addresses)
        """
        
        # Get by messages using proper student stats
        senders_m, receivers_m = self.db.get_student_stats_proper(by_messages=True, start_date=self.start_date_str, end_date=self.end_date_str, cities=self.cities)

        senders_student_m = pd.Series(senders_m).sort_values(ascending=False)
        receivers_student_m = pd.Series(receivers_m).sort_values(ascending=False)

        self.senders_student_m = senders_student_m
        self.receivers_student_m = receivers_student_m

        senders_student_m.to_csv(self.csv_path / 'top_student_senders_by_messages.csv', index=True, encoding="utf-8-sig")
        receivers_student_m.to_csv(self.csv_path / 'top_student_receivers_by_messages.csv', index=True, encoding="utf-8-sig")

        # Get by requests using proper student stats
        senders_r, receivers_r = self.db.get_student_stats_proper(by_messages=False, start_date=self.start_date_str, end_date=self.end_date_str, cities=self.cities)
        
        senders_student_r = pd.Series(senders_r).sort_values(ascending=False)
        receivers_student_r = pd.Series(receivers_r).sort_values(ascending=False)
        
        self.senders_student_r = senders_student_r
        self.receivers_student_r = receivers_student_r
        
        senders_student_r.to_csv(self.csv_path / 'top_student_senders_by_requests.csv', index=True, encoding="utf-8-sig")
        receivers_student_r.to_csv(self.csv_path / 'top_student_receivers_by_requests.csv', index=True, encoding="utf-8-sig")
        
        if if_plot:
            self._plot_communicators(
                receivers_student_m.head(n), receivers_student_r.head(n),
                senders_student_m.head(n), senders_student_r.head(n),
                'Student', n, 'top_students.png'
            )
    
    def top_communicators_for_place(self, if_plot: bool = False, n: int = 10):
        """Get top place communicators - direct SQL query."""
        
        # Get by messages
        senders_m, receivers_m = self.db.get_place_stats(by_messages=True, start_date=self.start_date_str, end_date=self.end_date_str, cities=self.cities)

        senders_place_m = pd.Series(senders_m).sort_values(ascending=False)
        receivers_place_m = pd.Series(receivers_m).sort_values(ascending=False)

        self.senders_place_m = senders_place_m
        self.receivers_place_m = receivers_place_m

        senders_place_m.to_csv(self.csv_path / 'top_place_senders_by_messages.csv', index=True, encoding="utf-8-sig")
        receivers_place_m.to_csv(self.csv_path / 'top_place_receivers_by_messages.csv', index=True, encoding="utf-8-sig")

        # Get by requests
        senders_r, receivers_r = self.db.get_place_stats(by_messages=False, start_date=self.start_date_str, end_date=self.end_date_str, cities=self.cities)
        
        senders_place_r = pd.Series(senders_r).sort_values(ascending=False)
        receivers_place_r = pd.Series(receivers_r).sort_values(ascending=False)
        
        self.senders_place_r = senders_place_r
        self.receivers_place_r = receivers_place_r
        
        senders_place_r.to_csv(self.csv_path / 'top_place_senders_by_requests.csv', index=True, encoding="utf-8-sig")
        receivers_place_r.to_csv(self.csv_path / 'top_place_receivers_by_requests.csv', index=True, encoding="utf-8-sig")
        
        if if_plot:
            self._plot_communicators(
                receivers_place_m.head(n), receivers_place_r.head(n),
                senders_place_m.head(n), senders_place_r.head(n),
                'Place', n, 'top_places.png'
            )
    
    def _plot_requests_received_vs_answered(self, receivers_r, senders_r, n: int, filename: str):
        """
        Side-by-side bars comparing, per employee, how many requests they received
        against how many they answered.

        Employees are the top `n` by requests received; the answered series is
        aligned to those same people so both bars in a pair describe one employee.
        """
        received = receivers_r.head(n)
        if received.empty:
            return
        answered = senders_r.reindex(received.index).fillna(0)

        x = np.arange(len(received))
        width = 0.4

        fig, ax = plt.subplots(figsize=(16, 9))
        ax.bar(x - width / 2, received.values, width, color=PLOT_PALETTE[1],
               edgecolor='black', alpha=0.8, label='Requests received by employee')
        ax.bar(x + width / 2, answered.values, width, color=PLOT_PALETTE[0],
               edgecolor='black', alpha=0.8, label='Requests answered by employee')

        for i, v in enumerate(received.values):
            ax.text(i - width / 2, v, str(int(v)), ha='center', va='bottom',
                    fontsize=12, fontweight='bold', color='black')
        for i, v in enumerate(answered.values):
            ax.text(i + width / 2, v, str(int(v)), ha='center', va='bottom',
                    fontsize=12, fontweight='bold', color='darkred')

        ax.set_title(f'Top {len(received)} Employees — Requests Received vs Answered',
                     fontsize=14, pad=45)
        ax.set_xlabel('Employee', fontsize=10)
        ax.set_ylabel('Requests', fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels([reshape_text(str(lbl)) for lbl in received.index], rotation=45, ha='right')
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)

        # Headroom for the value labels, and the legend above the axes so it can
        # never sit on top of a bar.
        ax.set_ylim(top=ax.get_ylim()[1] * 1.1)
        ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False, fontsize=11)

        plt.tight_layout()
        plt.savefig(self.plot_path / filename, dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_communicators(self, receivers_m, receivers_r, senders_m, senders_r,
                           entity_type: str, n: int, filename: str):
        """Helper to plot communicator charts."""
        fig, axes = plt.subplots(2, 2, figsize=(18, 12))
        
        data_sets = [
            (axes[0][0], receivers_m, f'Top {n} {entity_type} Receivers by Message Count', 'Messages Received'),
            (axes[0][1], receivers_r, f'Top {n} {entity_type} Receivers by Request Count', 'Requests Received'),
            (axes[1][0], senders_m, f'Top {n} {entity_type} Senders by Message Count', 'Messages Sent'),
            (axes[1][1], senders_r, f'Top {n} {entity_type} Senders by Request Count', 'Requests Sent'),
        ]
        
        for idx, (ax, data, title, ylabel) in enumerate(data_sets):
            if len(data) > 0:
                ax.bar(range(len(data)), data.values, color=PLOT_PALETTE[idx % len(PLOT_PALETTE)], edgecolor='black', alpha=0.8)
                for i, v in enumerate(data.values):
                    ax.text(i, v + 0.5, str(v), ha='center', fontsize=12, fontweight='bold')
            ax.set_title(title, fontsize=12, pad=20)
            ax.set_xlabel(f'{entity_type} Name', fontsize=10)
            ax.set_ylabel(f'Number of {ylabel}', fontsize=10)
            ax.set_xticks(range(len(data)))
            ax.set_xticklabels([reshape_text(str(lbl)) for lbl in data.index], rotation=45, ha='right')
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(self.plot_path / filename, dpi=300, bbox_inches='tight')
        plt.close()
    
    def communication_network(self, plot: bool = False, min_count: int = 5, top_n: int = 20):
        """Get communication network - direct SQL query."""
        
        edges = self.db.get_communication_network(min_count=1, start_date=self.start_date_str, end_date=self.end_date_str)
        
        # Build edge dictionary
        edge_counts = {}
        for edge in edges:
            key = (edge['from_name'], edge['to_name'])
            edge_counts[key] = edge['count']
        
        # Save to CSV
        df_edges = pd.DataFrame(edges)
        df_edges.to_csv(self.csv_path / 'communication_network.csv', index=False, encoding="utf-8-sig")
        
        print(f"\nCommunication Network Summary:")
        print(f"Total unique edges: {len(edge_counts)}")
        print(f"Total messages in network: {sum(edge_counts.values())}")
        
        # Filter for minimum count
        filtered_edges = {k: v for k, v in edge_counts.items() if v >= min_count}
        print(f"Edges with count >= {min_count}: {len(filtered_edges)}")
        
        if plot and len(filtered_edges) > 0:
            # Get top communicators
            all_names = set()
            for (f, t), c in filtered_edges.items():
                all_names.add(f)
                all_names.add(t)
            
            # Count total messages per person
            person_counts = Counter()
            for (f, t), c in filtered_edges.items():
                person_counts[f] += c
                person_counts[t] += c
            
            top_names = [name for name, _ in person_counts.most_common(top_n)]
            print(f"Top {top_n} communicators included in heatmap")
            
            # Create matrix
            n_people = len(top_names)
            matrix = np.zeros((n_people, n_people))
            
            for i, sender in enumerate(top_names):
                for j, receiver in enumerate(top_names):
                    matrix[i, j] = filtered_edges.get((sender, receiver), 0)
            
            # Plot heatmap
            fig, ax = plt.subplots(figsize=(14, 12))
            
            im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')
            
            ax.set_xticks(range(n_people))
            ax.set_yticks(range(n_people))
            ax.set_xticklabels([reshape_text(str(n)[:20]) for n in top_names], rotation=45, ha='right')
            ax.set_yticklabels([reshape_text(str(n)[:20]) for n in top_names])
            
            ax.set_xlabel('Receiver', fontsize=12)
            ax.set_ylabel('Sender', fontsize=12)
            ax.set_title(f'Communication Network (min {min_count} messages)', fontsize=14)
            
            plt.colorbar(im, ax=ax, label='Message Count')
            plt.tight_layout()
            plt.savefig(self.plot_path / 'communication_network.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        return edge_counts
    
    def total_messages_per_student(self, plot: bool = False):
        """Get message counts per student - direct SQL query."""
        
        counts = self.db.get_student_message_counts(start_date=self.start_date_str, end_date=self.end_date_str, cities=self.cities)
        
        sent = pd.Series(counts['sent']).sort_values(ascending=False)
        received = pd.Series(counts['received']).sort_values(ascending=False)
        
        # Compute histograms
        sent_hist = sent.value_counts().sort_index()
        received_hist = received.value_counts().sort_index()
        
        stats = {
            'sent_message_hist': sent_hist,
            'received_message_hist': received_hist
        }
        
        if plot:
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            
            for ax, hist, title, color in [
                (axes[0], sent_hist, 'Messages Sent per Student', PLOT_PALETTE[1]),
                (axes[1], received_hist, 'Messages Received per Student', PLOT_PALETTE[3])
            ]:
                ax.bar(hist.index, hist.values, color=color)
                for i, v in enumerate(hist.values):
                    ax.text(hist.index[i], v + 0.5, str(v), ha='center', fontsize=12, fontweight='bold')
                ax.set_title(title)
                ax.set_xlabel('Number of Messages')
                ax.set_ylabel('Number of Students')
                ax.grid(True, axis='y', linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            plt.savefig(self.plot_path / 'total_messages_per_student.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        return stats
    
    def response_time_per_person(self, plot: bool = False):
        """
        Calculate response times per Hami - uses database for data retrieval.
        
        This analysis calculates two meaningful metrics:
        1. Hami First Response Time: Time from first message (student request) to 
           second message (hami's first response). This measures how quickly 
           the hami responds to a new student request.
        2. Request Duration: Time from first message to last message in the request.
           This measures the total lifetime/duration of handling the request.
        
        Both metrics are grouped by hami_id and averaged.
        """
        
        data = self.db.get_response_times_data(start_date=self.start_date_str, end_date=self.end_date_str, cities=self.cities)
        
        # Group by request_id
        request_dates = defaultdict(list)
        request_hami = {}
        for row in data:
            request_dates[row['request_id']].append(row['date'])
            request_hami[row['request_id']] = row['hami_id']
        
        # Metrics to calculate
        hami_first_response_times = defaultdict(list)  # Time from 1st to 2nd message
        request_durations = defaultdict(list)  # Time from 1st to last message
        
        for request_id, dates in request_dates.items():
            hami_id = request_hami[request_id]
            
            # Parse dates
            times = []
            for date_str in dates:
                try:
                    jalali_dt = jdatetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    times.append(jalali_dt)
                except:
                    pass
            
            # Remove duplicates and sort chronologically
            times = sorted(set(times))
            
            if len(times) >= 2:
                # Hami First Response Time: time from 1st message (student) to 2nd message (hami response)
                first_response = (times[1] - times[0]).total_seconds() / 3600  # in hours
                if first_response > 0:
                    hami_first_response_times[hami_id].append(first_response)
                
                # Request Duration: time from first to last message
                duration = (times[-1] - times[0]).total_seconds() / 3600  # in hours
                if duration > 0:
                    request_durations[hami_id].append(duration)
        
        # Compute averages per hami
        avg_first_response = {pid: np.mean(times) for pid, times in hami_first_response_times.items() if times}
        avg_duration = {pid: np.mean(times) for pid, times in request_durations.items() if times}
        
        # Create series sorted by value (descending)
        avg_first_response_series = pd.Series(avg_first_response).sort_values(ascending=False)
        avg_duration_series = pd.Series(avg_duration).sort_values(ascending=False)
        
        # Save to CSV
        avg_first_response_series.to_csv(self.csv_path / 'hami_first_response_time.csv', index=True, encoding="utf-8-sig")
        avg_duration_series.to_csv(self.csv_path / 'request_duration_per_hami.csv', index=True, encoding="utf-8-sig")
        
        # Also save detailed data (number of samples per hami)
        first_response_detail = pd.DataFrame({
            'hami_id': list(avg_first_response.keys()),
            'avg_first_response_hours': [avg_first_response[h] for h in avg_first_response.keys()],
            'avg_first_response_days': [avg_first_response[h]/24 for h in avg_first_response.keys()],
            'num_requests': [len(hami_first_response_times[h]) for h in avg_first_response.keys()]
        }).sort_values('avg_first_response_hours', ascending=False)
        first_response_detail.to_csv(self.csv_path / 'hami_first_response_time_detail.csv', index=False, encoding="utf-8-sig")
        
        duration_detail = pd.DataFrame({
            'hami_id': list(avg_duration.keys()),
            'avg_duration_hours': [avg_duration[h] for h in avg_duration.keys()],
            'avg_duration_days': [avg_duration[h]/24 for h in avg_duration.keys()],
            'num_requests': [len(request_durations[h]) for h in avg_duration.keys()]
        }).sort_values('avg_duration_hours', ascending=False)
        duration_detail.to_csv(self.csv_path / 'request_duration_per_hami_detail.csv', index=False, encoding="utf-8-sig")
        
        if plot:
            fig, axes = plt.subplots(2, 1, figsize=(14, 10))
            
            # Plot 1: Hami First Response Time (student -> hami response)
            ax1 = axes[0]
            colors1 = plt.cm.Reds(np.linspace(0.3, 0.9, len(avg_first_response_series)))
            bars1 = ax1.bar(range(len(avg_first_response_series)), avg_first_response_series.values, 
                           color=colors1, edgecolor='darkred', alpha=0.8)
            ax1.set_title('Average Hami First Response Time per Hami\n(Time from student request to first hami response)', 
                         fontsize=12, fontweight='bold')
            ax1.set_ylabel('Average Response Time (hours)', fontsize=12)
            ax1.set_xticks(range(len(avg_first_response_series)))
            ax1.set_xticklabels(avg_first_response_series.index, rotation=45, ha='right', fontsize=11)
            ax1.grid(True, axis='y', linestyle='--', alpha=0.5)

            # Add value labels on bars
            for i, (idx, v) in enumerate(avg_first_response_series.items()):
                days = v / 24
                ax1.annotate(f'{days:.1f}d',
                           xy=(i, v), ha='center', va='bottom', fontsize=12,
                           color='darkred')
            
            # Add a horizontal line for overall average
            overall_avg1 = avg_first_response_series.mean()
            ax1.axhline(y=overall_avg1, color='blue', linestyle='--', linewidth=2, 
                       label=f'Overall Avg: {overall_avg1:.1f}h ({overall_avg1/24:.1f}d)')
            legend_with_headroom(ax1)
            
            # Plot 2: Request Duration
            ax2 = axes[1]
            colors2 = plt.cm.Blues(np.linspace(0.3, 0.9, len(avg_duration_series)))
            bars2 = ax2.bar(range(len(avg_duration_series)), avg_duration_series.values, 
                           color=colors2, edgecolor='navy', alpha=0.8)
            ax2.set_title('Average Request Duration per Hami\n(Time from first message to last message)', 
                         fontsize=12, fontweight='bold')
            ax2.set_ylabel('Average Duration (hours)', fontsize=12)
            ax2.set_xlabel('Hami ID', fontsize=12)
            ax2.set_xticks(range(len(avg_duration_series)))
            ax2.set_xticklabels(avg_duration_series.index, rotation=45, ha='right', fontsize=11)
            ax2.grid(True, axis='y', linestyle='--', alpha=0.5)

            # Add value labels on bars
            for i, (idx, v) in enumerate(avg_duration_series.items()):
                days = v / 24
                ax2.annotate(f'{days:.1f}d',
                           xy=(i, v), ha='center', va='bottom', fontsize=12,
                           color='navy')
            
            # Add a horizontal line for overall average
            overall_avg2 = avg_duration_series.mean()
            ax2.axhline(y=overall_avg2, color='red', linestyle='--', linewidth=2, 
                       label=f'Overall Avg: {overall_avg2:.1f}h ({overall_avg2/24:.1f}d)')
            legend_with_headroom(ax2)
            
            plt.tight_layout()
            plt.savefig(self.plot_path / 'response_time_per_person.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        return {
            'avg_first_response': avg_first_response_series, 
            'avg_duration': avg_duration_series,
            'first_response_detail': first_response_detail,
            'duration_detail': duration_detail
        }

    def hami_performance_score(self, plot: bool = False, weights: dict = None,
                               targets: dict = None, show_reference: bool = True) -> pd.DataFrame:
        """
        Composite performance score per hami, produced two ways from the same inputs.

        The inputs are how many requests a hami was given, how quickly they first
        replied, how long their requests stayed open, and the Quality of Response score
        typed in on the Evaluations page for the same period.

        The **z-score** version standardises each metric against the cohort, so it ranks
        hamis against each other but is blind to the whole group improving: its mean is 0
        by construction. The **absolute** version, in `_hami_absolute_score`, maps the same
        metrics through fixed targets onto 0-100, so a better period reads as a higher
        number for everybody.

        Volume is anchored on when a request opened while timing is anchored on when it
        closed. The asymmetry is deliberate: volume answers "how much work arrived this
        period", timing answers "how well was the work that finished this period handled".
        """
        # Imported here rather than at module scope because config.py creates directories
        # as a side effect of being imported, and analyzer.py is importable on its own.
        import config

        weights = {**config.HAMI_SCORE_WEIGHTS, **(weights or {})}
        targets = {**config.HAMI_SCORE_TARGETS, **(targets or {})}

        # Volume: requests opened inside the window. Same source as total_requests_per_hami,
        # minus the unknown bucket, which is Excel-only rows belonging to no real hami.
        counts = self.db.get_requests_count_per_hami(start_date=self.start_date_str,
                                                     end_date=self.end_date_str,
                                                     cities=self.cities)
        counts.pop('unknown', None)

        # Timing: requests that closed inside the window, measured across the whole thread.
        rows = self.db.get_hami_timing_data(start_date=self.start_date_str,
                                            end_date=self.end_date_str,
                                            cities=self.cities)
        request_dates = defaultdict(list)
        request_hami = {}
        for row in rows:
            request_dates[row['request_id']].append(row['date'])
            request_hami[row['request_id']] = row['hami_id']

        first_responses = defaultdict(list)
        durations = defaultdict(list)
        for request_id, dates in request_dates.items():
            hami_id = request_hami[request_id]
            times = []
            for date_str in dates:
                try:
                    times.append(jdatetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S'))
                except ValueError:
                    pass
            times = sorted(set(times))
            if len(times) >= 2:
                first_response = (times[1] - times[0]).total_seconds() / 3600
                if first_response > 0:
                    first_responses[hami_id].append(first_response)
                duration = (times[-1] - times[0]).total_seconds() / 3600
                if duration > 0:
                    durations[hami_id].append(duration)

        period_days = self._period_days()

        # Quality: whatever the user saved on the Evaluations page for exactly this period.
        quality = {row['person_key']: row['score']
                   for row in self.db.get_evaluations(start_date=self.start_date_str,
                                                      end_date=self.end_date_str,
                                                      person_type='hami')
                   if row['parameter'] == 'quality_of_response'}

        # The median, not the mean: these distributions are strongly right-skewed, so a
        # handful of forgotten tickets would otherwise decide a hami's score.
        names = self.db.get_hami_names()
        active = sorted(set(counts) & set(first_responses) & set(durations))
        df = pd.DataFrame([{
            'hami_id': hami_id,
            'hami_name': names.get(hami_id, ''),
            'count': counts[hami_id],
            'first_response_median_h': float(np.median(first_responses[hami_id])),
            'duration_median_h': float(np.median(durations[hami_id])),
            'quality': quality.get(hami_id, np.nan),
        } for hami_id in active])

        if df.empty:
            print("Warning: no hami has request, timing and quality data for this period.")
            return df

        # A hami with no quality score has no comparable final score, so they leave the
        # report rather than being ranked on three quarters of the formula. When nobody
        # has been graded yet the activity metrics are still worth exporting on their own.
        graded = bool(quality)
        if graded:
            ungraded = [h for h in df['hami_id'] if h not in quality]
            if ungraded:
                print(f"Warning: no Quality of Response score for {', '.join(ungraded)} "
                      f"- excluded from the performance score.")
            df = df[df['quality'].notna()].reset_index(drop=True)
        else:
            periods = self.db.get_evaluation_periods()
            available = ', '.join(f"{p['start_date']}..{p['end_date']}" for p in periods) or 'none'
            print(f"Warning: no Quality of Response scores saved for "
                  f"{self.start_date_str}..{self.end_date_str}, so the final score cannot be "
                  f"computed. Saved periods: {available}.")

        df['z_count'] = zscore(df['count'])
        df['z_first_response'] = zscore(df['first_response_median_h'], higher_is_better=False)
        df['z_duration'] = zscore(df['duration_median_h'], higher_is_better=False)
        if graded:
            df['z_quality'] = zscore(df['quality'])
            df['final_score'] = (weights['count'] * df['z_count']
                                 + weights['first_response'] * df['z_first_response']
                                 + weights['duration'] * df['z_duration']
                                 + weights['quality'] * df['z_quality'])
            df = df.sort_values('final_score', ascending=False).reset_index(drop=True)
        else:
            df['z_quality'] = np.nan
            df['final_score'] = np.nan
            df = df.sort_values('z_count', ascending=False).reset_index(drop=True)

        df.to_csv(self.csv_path / 'hami_performance_score.csv', index=False, encoding="utf-8-sig")

        self._hami_absolute_score(df, first_responses, durations, weights, targets,
                                  graded, period_days, plot, show_reference)

        if plot:
            fig = plt.figure(figsize=(16, 11))
            gs = GridSpec(2, 2, width_ratios=[3, 1], height_ratios=[1, 1], figure=fig)
            x = range(len(df))

            ax = fig.add_subplot(gs[0, 0])
            if graded:
                ax.bar(x, df['final_score'].values, color=PLOT_SINGLE_COLOR,
                       edgecolor='navy', alpha=0.8)
                for i, v in enumerate(df['final_score'].values):
                    ax.text(i, v, f"{v:.2f}", ha='center',
                            va='bottom' if v >= 0 else 'top', fontsize=11, fontweight='bold')
                ax.axhline(y=0, color='black', linewidth=0.8)
                ax.set_ylabel(reshape_text('Weighted z-score'), fontsize=10)
            else:
                ax.axis('off')
                ax.text(0.5, 0.5, reshape_text('No Quality of Response scores for this period'),
                        ha='center', va='center', fontsize=14)
            ax.set_title(reshape_text('Hami Performance Score'), fontsize=13, pad=15)
            ax.set_xticks(list(x))
            ax.set_xticklabels(df['hami_id'], rotation=45, ha='right')
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)

            # The components stay visible so it is clear which metric drove each score,
            # and so an extreme z-score is read as an outlier rather than a verdict.
            ax2 = fig.add_subplot(gs[1, 0])
            components = [('z_count', 'count', 'Requests'),
                          ('z_first_response', 'first_response', 'First Response'),
                          ('z_duration', 'duration', 'Duration'),
                          ('z_quality', 'quality', 'Quality')]
            width = 0.2
            for idx, (column, weight_key, label) in enumerate(components):
                offset = (idx - 1.5) * width
                values = (df[column] * weights[weight_key]).fillna(0).values
                ax2.bar([i + offset for i in x], values, width=width, color=PLOT_PALETTE[idx],
                        edgecolor='black', linewidth=0.3, alpha=0.85,
                        label=reshape_text(f"{label} ({weights[weight_key]:.1%})"))
            ax2.axhline(y=0, color='black', linewidth=0.8)
            ax2.set_title(reshape_text('Score Contribution by Metric'), fontsize=13, pad=15)
            ax2.set_xlabel(reshape_text('Hami ID'), fontsize=10)
            ax2.set_ylabel(reshape_text('Weighted z-score'), fontsize=10)
            ax2.set_xticks(list(x))
            ax2.set_xticklabels(df['hami_id'], rotation=45, ha='right')
            ax2.grid(True, axis='y', linestyle='--', alpha=0.7)
            ax2.legend(fontsize=9, ncol=4, loc='upper right')

            if show_reference:
                ref_ax = fig.add_subplot(gs[:, 1])
                self._add_reference_table(ref_ax, max_rows=25, ids=df['hami_id'].tolist())

            plt.tight_layout()
            plt.savefig(self.plot_path / 'hami_performance_score.png', dpi=300, bbox_inches='tight')
            plt.close()

        return df

    def _hami_absolute_score(self, base: pd.DataFrame, first_responses: dict, durations: dict,
                             weights: dict, targets: dict, graded: bool, period_days: float,
                             plot: bool, show_reference: bool) -> pd.DataFrame:
        """
        The 0-100 companion to the z-score, computed from the same data.

        Every metric is mapped through a fixed target rather than through the cohort mean,
        so the number a hami gets does not move when a colleague joins or leaves, and a
        period in which everyone answered faster reads as a higher score for everyone.
        That is the one question the z-score cannot answer.

        Timing is scored per request against hour tiers and averaged, not scored on the
        hami's median. One forgotten ticket then costs exactly one ticket instead of
        dragging a whole aggregate, which is what made the z-score outlier-sensitive.
        """
        import config

        df = base.copy()
        if df.empty:
            return df

        credits = np.asarray(config.HAMI_SCORE_TIER_CREDITS, dtype=float)

        def tiered(values, tiers) -> float:
            """Mean per-request credit: full credit at or under the first tier, none past the last."""
            if not values:
                return np.nan
            tiers = np.asarray(sorted(tiers), dtype=float)
            return float(credits[np.searchsorted(tiers, np.asarray(values, dtype=float))].mean())

        df['score_first_response'] = [tiered(first_responses.get(h, []), targets['first_response_hours'])
                                      for h in df['hami_id']]
        df['score_duration'] = [tiered(durations.get(h, []), targets['duration_hours'])
                                for h in df['hami_id']]

        # Volume is credited, not just contextualised: carrying more of the load is effort.
        # The curve saturates so that a heavy caseload cannot buy its way past bad service.
        months = max(period_days, 1) / 30.0
        df['requests_per_30d'] = df['count'] / months
        df['score_count'] = volume_score(df['requests_per_30d'], targets['volume_target_30d'],
                                         config.HAMI_SCORE_VOLUME_SHAPE,
                                         config.HAMI_SCORE_VOLUME_CREDIT_AT_TARGET)

        df['score_quality'] = df['quality'].astype(float)

        # How much of the score rests on evidence. A hami with a handful of requests can
        # land anywhere on the scale by chance, so the score is reported with the size of
        # the sample behind it rather than quietly adjusted for it. The half-way point
        # scales with the window, so a longer period demands proportionally more requests.
        n = df['count'].astype(float)
        n0 = float(targets['confidence_half_n']) * months
        df['confidence'] = 100.0 * n / (n + n0) if n0 > 0 else 100.0

        # With nobody graded the quality weight has nothing to apply to. Dropping it and
        # rescaling the rest keeps the result on 0-100 instead of voiding it, which is
        # worth doing here because the other three metrics need no human input at all.
        keys = ['count', 'first_response', 'duration'] + (['quality'] if graded else [])
        used = normalise_weights(weights, keys)

        df['final_score'] = sum(used[key] * df[f'score_{key}'] for key in used)
        df = df.sort_values('final_score', ascending=False).reset_index(drop=True)

        # The whole-population figure trims the weakest tail: a couple of barely-active or
        # struggling hamis otherwise drag the headline number around far more than any real
        # change in how the group is working.
        top_percent = float(targets['population_top_percent'])
        k = max(1, int(np.ceil(top_percent / 100.0 * len(df))))
        top = df.head(k)
        system_score = float(top['final_score'].mean())

        columns = ['hami_id', 'hami_name', 'count', 'requests_per_30d', 'first_response_median_h',
                   'duration_median_h', 'quality', 'score_count', 'score_first_response',
                   'score_duration', 'score_quality', 'confidence', 'final_score']
        df[columns].to_csv(self.csv_path / 'hami_performance_score_absolute.csv',
                           index=False, encoding="utf-8-sig")

        # One row per run, so the headline number can be lined up against last month's.
        summary = {
            'start_date': self.start_date_str or '',
            'end_date': self.end_date_str or '',
            'period_days': period_days,
            'cities': ', '.join(self.cities) if self.cities else 'all',
            'hamis': len(df),
            'top_percent': top_percent,
            'hamis_counted': k,
            'system_score': round(system_score, 2),
            'system_score_all_hamis': round(float(df['final_score'].mean()), 2),
            'score_count': round(float(top['score_count'].mean()), 2),
            'score_first_response': round(float(top['score_first_response'].mean()), 2),
            'score_duration': round(float(top['score_duration'].mean()), 2),
            'score_quality': round(float(top['score_quality'].mean()), 2) if graded else '',
        }
        pd.DataFrame([summary]).to_csv(self.csv_path / 'hami_performance_system_score.csv',
                                       index=False, encoding="utf-8-sig")

        if plot:
            fig = plt.figure(figsize=(16, 11))
            gs = GridSpec(2, 2, width_ratios=[3, 1], height_ratios=[1, 1], figure=fig)
            x = list(range(len(df)))

            ax = fig.add_subplot(gs[0, 0])
            for low, high, color in SCORE_BANDS:
                ax.axhspan(low, high, color=color, alpha=0.13, zorder=0)
            ax.bar(x, df['final_score'].values,
                   color=[band_color(v) for v in df['final_score']],
                   edgecolor='black', linewidth=0.5, alpha=0.9, zorder=2)
            for i, (score, count, conf) in enumerate(zip(df['final_score'], df['count'], df['confidence'])):
                ax.text(i, score + 1.5, f"{score:.0f}", ha='center', va='bottom',
                        fontsize=11, fontweight='bold', zorder=3)
                ax.text(i, 2, f"n={int(count)}\n{conf:.0f}%", ha='center', va='bottom',
                        fontsize=8, color='dimgray', linespacing=1.3, zorder=3)
            ax.axhline(y=system_score, color='navy', linestyle='--', linewidth=2, zorder=4,
                       label=f"System score (top {top_percent:.0f}% of hamis): {system_score:.1f}")
            ax.set_ylim(0, 108)
            ax.set_ylabel(reshape_text('Score (0-100)'), fontsize=10)
            ax.set_title(reshape_text('Hami Performance Score - Absolute (0-100)'), fontsize=13, pad=15)
            ax.set_xticks(x)
            ax.set_xticklabels(df['hami_id'], rotation=45, ha='right')
            ax.grid(True, axis='y', linestyle='--', alpha=0.5)
            ax.legend(fontsize=10, loc='upper right')

            # Stacked, unlike the z-score panel: absolute contributions are all positive
            # and add up to the bar above, so the split is readable straight off the chart.
            ax2 = fig.add_subplot(gs[1, 0])
            bottom = np.zeros(len(df))
            for idx, (key, label) in enumerate([('count', 'Requests'),
                                                ('first_response', 'First Response'),
                                                ('duration', 'Duration'),
                                                ('quality', 'Quality')]):
                if key not in used:
                    continue
                values = (df[f'score_{key}'] * used[key]).fillna(0).values
                ax2.bar(x, values, bottom=bottom, color=PLOT_PALETTE[idx], edgecolor='black',
                        linewidth=0.3, alpha=0.85,
                        label=reshape_text(f"{label} ({used[key]:.1%})"))
                bottom += values
            ax2.set_title(reshape_text('Score Contribution by Metric'), fontsize=13, pad=15)
            ax2.set_xlabel(reshape_text('Hami ID'), fontsize=10)
            ax2.set_ylabel(reshape_text('Weighted points'), fontsize=10)
            ax2.set_xticks(x)
            ax2.set_xticklabels(df['hami_id'], rotation=45, ha='right')
            ax2.grid(True, axis='y', linestyle='--', alpha=0.5)
            legend_with_headroom(ax2, fontsize=9, ncol=4)

            if show_reference:
                ref_ax = fig.add_subplot(gs[:, 1])
                self._add_reference_table(ref_ax, max_rows=25, ids=df['hami_id'].tolist())

            plt.tight_layout()
            plt.savefig(self.plot_path / 'hami_performance_score_absolute.png',
                        dpi=300, bbox_inches='tight')
            plt.close()

        return df

    # Metrics behind the employee score, in the order they appear in every plot legend.
    EMPLOYEE_METRICS = [('count', 'Requests answered'),
                        ('response_time', 'Response Time'),
                        ('quality', 'Quality of Response')]

    def employee_performance_score(self, plot: bool = False, weights: dict = None,
                                   targets: dict = None) -> pd.DataFrame:
        """
        The employee counterpart of `hami_performance_score`, scored two ways.

        Employees have no measurable timing of their own - a request's clock belongs to the
        hami who owns it - so speed arrives as the Response Time grade typed in on the
        Evaluations page, already on 0-100. That leaves three inputs: how many requests the
        employee answered, that Response Time grade, and Quality of Response.

        The cohort is an order of magnitude larger than the hamis, so the plots lead with
        the shape of the whole population and then name only the two ends of it.
        """
        import config

        weights = {**config.EMPLOYEE_SCORE_WEIGHTS, **(weights or {})}
        targets = {**config.EMPLOYEE_SCORE_TARGETS, **(targets or {})}

        # An employee "answers" a request by sending a message on someone else's request,
        # which is the senders-by-requests series behind the Top Employees plot.
        senders, _ = self.db.get_employee_stats_proper(by_messages=False,
                                                       start_date=self.start_date_str,
                                                       end_date=self.end_date_str,
                                                       cities=self.cities)

        evaluations = self.db.get_evaluations(start_date=self.start_date_str,
                                              end_date=self.end_date_str,
                                              person_type='employee')
        graded = {}
        for parameter in ('quality', 'response_time'):
            key = 'quality_of_response' if parameter == 'quality' else parameter
            graded[parameter] = {row['person_key']: row['score'] for row in evaluations
                                 if row['parameter'] == key}

        period_days = self._period_days()
        months = max(period_days, 1) / 30.0

        df = pd.DataFrame([{
            'employee': name,
            'count': count,
            'requests_per_30d': count / months,
            'response_time': graded['response_time'].get(name, np.nan),
            'quality': graded['quality'].get(name, np.nan),
        } for name, count in senders.items()])

        if df.empty:
            print("Warning: no employee answered a request in this period.")
            return df

        # Only metrics somebody was actually graded on can carry weight. An employee
        # missing a grade the others have would be ranked on a different formula, so they
        # leave the report rather than quietly scoring on fewer metrics.
        keys = ['count'] + [key for key in ('response_time', 'quality') if graded[key]]
        for key in keys[1:]:
            missing = df['employee'][df[key].isna()].tolist()
            if missing:
                print(f"Warning: {len(missing)} employee(s) have no {key} score "
                      f"- excluded from the performance score.")
            df = df[df[key].notna()]
        df = df.reset_index(drop=True)

        if len(keys) == 1:
            periods = self.db.get_evaluation_periods()
            available = ', '.join(f"{p['start_date']}..{p['end_date']}" for p in periods) or 'none'
            print(f"Warning: no employee evaluations saved for "
                  f"{self.start_date_str}..{self.end_date_str}, so the score rests on request "
                  f"volume alone. Saved periods: {available}.")
        if df.empty:
            print("Warning: no employee has both request and evaluation data for this period.")
            return df

        used = normalise_weights(weights, keys)
        labels = dict(self.EMPLOYEE_METRICS)

        df['score_count'] = volume_score(df['requests_per_30d'], targets['volume_target_30d'],
                                         config.HAMI_SCORE_VOLUME_SHAPE,
                                         config.HAMI_SCORE_VOLUME_CREDIT_AT_TARGET)
        df['score_response_time'] = df['response_time'].astype(float)
        df['score_quality'] = df['quality'].astype(float)

        n = df['count'].astype(float)
        n0 = float(targets['confidence_half_n']) * months
        df['confidence'] = 100.0 * n / (n + n0) if n0 > 0 else 100.0

        for key in keys:
            df[f'z_{key}'] = zscore(df['count' if key == 'count' else key])
        df['z_score'] = sum(used[key] * df[f'z_{key}'] for key in keys)
        df['absolute_score'] = sum(used[key] * df[f'score_{key}'] for key in keys)
        df = df.sort_values('absolute_score', ascending=False).reset_index(drop=True)

        top_percent = float(targets['population_top_percent'])
        k = max(1, int(np.ceil(top_percent / 100.0 * len(df))))
        top = df.head(k)
        system_score = float(top['absolute_score'].mean())

        shared = ['employee', 'count', 'requests_per_30d', 'response_time', 'quality', 'confidence']
        df.sort_values('z_score', ascending=False)[
            shared + [f'z_{key}' for key in keys] + ['z_score']
        ].to_csv(self.csv_path / 'employee_performance_score.csv', index=False, encoding="utf-8-sig")
        df[shared + [f'score_{key}' for key in keys] + ['absolute_score']].to_csv(
            self.csv_path / 'employee_performance_score_absolute.csv', index=False, encoding="utf-8-sig")

        summary = {
            'start_date': self.start_date_str or '',
            'end_date': self.end_date_str or '',
            'period_days': period_days,
            'cities': ', '.join(self.cities) if self.cities else 'all',
            'employees': len(df),
            'top_percent': top_percent,
            'employees_counted': k,
            'system_score': round(system_score, 2),
            'system_score_all_employees': round(float(df['absolute_score'].mean()), 2),
            **{f'score_{key}': round(float(top[f'score_{key}'].mean()), 2) for key in keys},
        }
        pd.DataFrame([summary]).to_csv(self.csv_path / 'employee_performance_system_score.csv',
                                       index=False, encoding="utf-8-sig")

        if plot:
            top_n = int(targets['top_n'])
            self._plot_person_scores(
                df.sort_values('absolute_score', ascending=False), keys, used, labels,
                score_column='absolute_score', prefix='score_', absolute=True, top_n=top_n,
                title='Employee Performance Score - Absolute (0-100)',
                filename='employee_performance_score_absolute.png',
                system_score=system_score, top_percent=top_percent, period_days=period_days)
            self._plot_person_scores(
                df.sort_values('z_score', ascending=False), keys, used, labels,
                score_column='z_score', prefix='z_', absolute=False, top_n=top_n,
                title='Employee Performance Score - Relative (z-score)',
                filename='employee_performance_score.png',
                system_score=None, top_percent=top_percent, period_days=period_days)

        return df

    def _plot_person_scores(self, df: pd.DataFrame, keys: list, weights: dict, labels: dict,
                            score_column: str, prefix: str, absolute: bool, top_n: int,
                            title: str, filename: str, system_score: float,
                            top_percent: float, period_days: int):
        """
        One figure for a cohort too large to fit on a single axis.

        Seventy bars side by side is not a chart anyone reads, so the top row describes the
        population as a whole - a headline card, the distribution of every score, and what
        separates the two ends - and only then do the lower panels name the best and the
        worst. Every named row carries its request count and confidence on the right, so a
        score built on four requests is never mistaken for a verdict.
        """
        scores = df[score_column]
        best = df.head(top_n)
        worst = df.tail(top_n).sort_values(score_column)

        fig = plt.figure(figsize=(20, 16))
        gs = GridSpec(3, 3, height_ratios=[0.75, 1.15, 1.15], figure=fig)

        # --- headline card -------------------------------------------------------
        ax_card = fig.add_subplot(gs[0, 0])
        ax_card.axis('off')
        ax_card.set_xlim(0, 100)
        ax_card.set_ylim(0, 1)
        if absolute:
            ax_card.text(50, 0.93, f"{system_score:.1f}", ha='center', va='center',
                         fontsize=44, fontweight='bold', color=band_color(system_score))
            ax_card.text(50, 0.68, reshape_text('System score out of 100'),
                         ha='center', va='center', fontsize=12)
            ax_card.text(50, 0.59, reshape_text(f"best {top_percent:.0f}% of {len(df)} employees "
                                                f"over {period_days} days"),
                         ha='center', va='center', fontsize=10, color='dimgray')
            for low, high, color in SCORE_BANDS:
                ax_card.axvspan(low, high, ymin=0.34, ymax=0.45, color=color, alpha=0.45)
            ax_card.plot([system_score, system_score], [0.31, 0.48], color='black', linewidth=2.5)
            for edge in (0, 50, 100):
                ax_card.text(edge, 0.27, str(edge), ha='center', va='top', fontsize=8, color='gray')
            lines = [f"All {len(df)} employees: {scores.mean():.1f}",
                     f"Median: {scores.median():.1f}",
                     f"Best: {scores.max():.1f}   Weakest: {scores.min():.1f}"]
            lines += [f"{labels[key]}: {df[prefix + key].mean():.1f}" for key in keys]
        else:
            ax_card.text(50, 0.90, reshape_text('Relative'), ha='center', va='center',
                         fontsize=30, fontweight='bold', color='#4a6fa5')
            ax_card.text(50, 0.68, reshape_text('z-score, not a mark out of 100'),
                         ha='center', va='center', fontsize=12)
            lines = [f"{len(df)} employees over {period_days} days",
                     "The average is 0 by construction, so this",
                     "chart ranks people and cannot show the",
                     "group as a whole getting better.",
                     "Use the absolute plot for that.",
                     "",
                     f"Range: {scores.min():+.2f} to {scores.max():+.2f}",
                     f"Spread (sd): {scores.std(ddof=1):.2f}"]
        ax_card.text(2, 0.20, reshape_text('\n'.join(lines)), ha='left', va='top',
                     fontsize=10, linespacing=1.6)

        # --- distribution of the whole population --------------------------------
        ax_dist = fig.add_subplot(gs[0, 1])
        if absolute:
            bins = np.arange(0, 101, 10)
            counts, edges, patches = ax_dist.hist(scores, bins=bins, edgecolor='black', linewidth=0.6)
            for patch, left in zip(patches, edges[:-1]):
                patch.set_facecolor(band_color(left + 5))
            ax_dist.set_xlim(0, 100)
            ax_dist.axvline(system_score, color='navy', linestyle='--', linewidth=2,
                            label=f"System: {system_score:.1f}")
        else:
            ax_dist.hist(scores, bins=12, color=PLOT_SINGLE_COLOR, edgecolor='black', linewidth=0.6)
            ax_dist.axvline(0, color='black', linewidth=1)
        ax_dist.axvline(scores.median(), color='darkred', linestyle=':', linewidth=2,
                        label=f"Median: {scores.median():.1f}")
        ax_dist.set_title(reshape_text('How the whole population is spread'), fontsize=12, pad=12)
        ax_dist.set_xlabel(reshape_text('Score'), fontsize=10)
        ax_dist.set_ylabel(reshape_text('Employees'), fontsize=10)
        ax_dist.grid(True, axis='y', linestyle='--', alpha=0.5)
        ax_dist.legend(fontsize=9)

        # --- what separates the two ends -----------------------------------------
        ax_cmp = fig.add_subplot(gs[0, 2])
        y = np.arange(len(keys))
        height = 0.36
        ax_cmp.barh(y + height / 2, [best[prefix + key].mean() for key in keys], height,
                    color=PLOT_PALETTE[2], edgecolor='black', linewidth=0.4,
                    label=reshape_text(f"Best {len(best)}"))
        ax_cmp.barh(y - height / 2, [worst[prefix + key].mean() for key in keys], height,
                    color=PLOT_PALETTE[3], edgecolor='black', linewidth=0.4,
                    label=reshape_text(f"Weakest {len(worst)}"))
        ax_cmp.axvline(0, color='black', linewidth=0.8)
        ax_cmp.set_yticks(y)
        ax_cmp.set_yticklabels([reshape_text(labels[key]) for key in keys], fontsize=9)
        ax_cmp.set_title(reshape_text('What separates the two ends'), fontsize=12, pad=12)
        ax_cmp.set_xlabel(reshape_text('Average raw metric score'), fontsize=10)
        ax_cmp.grid(True, axis='x', linestyle='--', alpha=0.5)
        ax_cmp.legend(fontsize=9, loc='lower right')

        # --- the two ends, named --------------------------------------------------
        panels = []
        for row, (group, heading, accent) in enumerate(
                [(best, f"Best {len(best)} employees", '#2e7d32'),
                 (worst, f"Weakest {len(worst)} employees", '#b71c1c')], start=1):
            ax = fig.add_subplot(gs[row, :])
            panels.append(ax)
            y = np.arange(len(group))
            # Positives stack to the right and negatives to the left, so the bar still ends
            # at the final score while showing which metric put it there.
            right = np.zeros(len(group))
            left = np.zeros(len(group))
            for idx, key in enumerate(keys):
                values = (group[prefix + key] * weights[key]).fillna(0).values
                starts = np.where(values >= 0, right, left)
                ax.barh(y, values, left=starts, height=0.62, color=PLOT_PALETTE[idx],
                        edgecolor='black', linewidth=0.3, alpha=0.9,
                        label=reshape_text(f"{labels[key]} ({weights[key]:.0%})") if row == 1 else None)
                right += np.clip(values, 0, None)
                left += np.clip(values, None, 0)
            for i, value in enumerate(group[score_column].values):
                anchor = right[i] if value >= 0 else left[i]
                ax.text(anchor, i, f"  {value:.1f}" if absolute else f"  {value:+.2f}",
                        va='center', ha='left' if value >= 0 else 'right',
                        fontsize=10, fontweight='bold')
            ax.axvline(0, color='black', linewidth=0.8)
            ax.set_yticks(y)
            ax.set_yticklabels([reshape_text(str(name)) for name in group['employee']], fontsize=9)
            ax.invert_yaxis()
            ax.set_title(reshape_text(heading), fontsize=12, color=accent, pad=10, loc='left')
            ax.set_xlabel(reshape_text('Weighted points' if absolute else 'Weighted z-score'), fontsize=10)
            ax.grid(True, axis='x', linestyle='--', alpha=0.5)
            if row == 1:
                ax.legend(fontsize=9, ncol=len(keys), loc='lower right', bbox_to_anchor=(1.0, 1.0),
                          frameon=False)

            # Evidence behind each row, opposite the name so it can never be missed.
            ax_info = ax.twinx()
            ax_info.set_ylim(ax.get_ylim())
            ax_info.set_yticks(y)
            ax_info.set_yticklabels([f"n={int(c)}  ·  {conf:.0f}%"
                                     for c, conf in zip(group['count'], group['confidence'])],
                                    fontsize=8, color='dimgray')
            ax_info.tick_params(length=0)

        # Both ends share one x-axis: on separate scales the weakest panel would look as
        # long as the best one and the gap between them would disappear.
        low = min(ax.get_xlim()[0] for ax in panels)
        high = max(ax.get_xlim()[1] for ax in panels)
        span = high - low
        for ax in panels:
            ax.set_xlim(low - 0.02 * span, high + 0.10 * span)

        fig.suptitle(reshape_text(title), fontsize=16, y=0.995)
        plt.tight_layout(rect=[0, 0, 1, 0.98])
        plt.savefig(self.plot_path / filename, dpi=300, bbox_inches='tight')
        plt.close()

    def place_filtered(self):
        """
        Parse place data and create expanded CSV files.
        
        Reads top_place_{i}_by_{j}.csv files (from top_communicators_for_place)
        and parses the Place field to extract educational_level, field, city, year.
        Creates top_place_{i}_by_{j}_expanded.csv files needed by place_filtered_by_grouped.
        """
        a = ["receivers", "senders"]
        b = ["messages", "requests"]
        
        for i in a:
            for j in b:
                csv_path = self.csv_path / f"top_place_{i}_by_{j}.csv"
                if not csv_path.exists():
                    print(f"Warning: {csv_path} not found. Run top_communicators_for_place() first.")
                    continue
                    
                data = pd.read_csv(csv_path)
                data.columns = ["Place", "Count"]
                new_data = pd.DataFrame(columns=["educational_level", "field", "city", "year", "count"])
                
                for k, v in data.iterrows():
                    try:
                        place_str = str(v["Place"])
                        if "_" in place_str:
                            dataaa = place_str.split("_")
                            if len(dataaa) == 4:
                                educational_level, field, city, year = dataaa
                            elif len(dataaa) == 5:
                                educational_level, field, city, year = dataaa[0], dataaa[1] + "_" + dataaa[2], dataaa[3], dataaa[4]
                            else:
                                # Handle other cases with more underscores
                                educational_level = dataaa[0]
                                year = dataaa[-1]
                                city = dataaa[-2]
                                field = "_".join(dataaa[1:-2])
                        else:
                            parts = place_str.split("-")
                            if len(parts) == 4:
                                educational_level, field, city, year = parts
                            else:
                                continue
                        new_data.loc[len(new_data)] = {
                            "educational_level": educational_level,
                            "field": field,
                            "city": city,
                            "year": year,
                            "count": v["Count"]
                        }
                    except (ValueError, IndexError) as e:
                        print(f"Error processing row {k}: {v['Place']} - {e}")
                
                new_data.to_csv(self.csv_path / f"top_place_{i}_by_{j}_expanded.csv", index=False, encoding="utf-8-sig")
        
        # Also store place data for other uses
        self.place_data = self.db.get_place_request_details(cities=self.cities)
        return self.place_data
    
    def place_filtered_by(self, by: str = "field", top_n: int = 20, plot: bool = True):
        """
        Analyze all requests grouped by field/year/edu_level.
        
        This counts ALL requests from the requests table, not just those
        that have messages to places.
        
        Args:
            by: Grouping method - 'field', 'year', or 'educational_level'
            top_n: Number of top results to show
            plot: Whether to generate a plot
        """
        
        # Get counts directly from database based on grouping
        if by == "field":
            result = self.db.get_requests_count_by_field(start_date=self.start_date_str, end_date=self.end_date_str, cities=self.cities)
        elif by == "year":
            result = self.db.get_requests_count_by_year(start_date=self.start_date_str, end_date=self.end_date_str, cities=self.cities)
        elif by == "educational_level":
            result = self.db.get_requests_count_by_education_level(start_date=self.start_date_str, end_date=self.end_date_str, cities=self.cities)
        else:
            result = self.db.get_requests_count_by_field(start_date=self.start_date_str, end_date=self.end_date_str, cities=self.cities)
        
        result_series = pd.Series(result).sort_values(ascending=False).head(top_n)
        
        result_series.to_csv(self.csv_path / f'places_by_{by}.csv', index=True, encoding="utf-8-sig")
        
        if plot:
            fig, ax = plt.subplots(figsize=(14, 8))
            
            bars = ax.bar(range(len(result_series)), result_series.values,
                         color=PLOT_SINGLE_COLOR, edgecolor='navy', alpha=0.7)
            
            for i, v in enumerate(result_series.values):
                ax.text(i, v + 0.5, str(v), ha='center', fontsize=12, fontweight='bold')
            
            ax.set_title(f'Requests by {by.replace("_", " ").title()}', fontsize=12, pad=20)
            ax.set_xlabel(by.replace("_", " ").title(), fontsize=10)
            ax.set_ylabel('Number of Requests', fontsize=10)
            ax.set_xticks(range(len(result_series)))
            ax.set_xticklabels([reshape_text(str(lbl)) for lbl in result_series.index], rotation=45, ha='right')
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            plt.savefig(self.plot_path / f'places_by_{by}.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        return result_series
    
    def place_filtered_by_grouped(self, by: str = "field", top_n: int = 20, plot: bool = True):
        """
        Analyze places with complex grouping by field/year/edu_level.
        
        This replicates the DataAnalyzer.place_filtered_by() behavior:
        - Groups fields into major categories (روانشناسی, حقوق, etc.)
        - Shows 4 panels: receivers/senders × messages/requests
        - Generates top_place_grouped_by_{by}.png
        
        REQUIRES: top_communicators_for_place() and place_filtered() to be run first
        to generate the required CSV files.
        """
        
        if by == "field":
            a = ["receivers", "senders"]
            b = ["messages", "requests"]

            grouped_results = {}

            for i in a:
                for j in b:
                    csv_path = self.csv_path / f"top_place_{i}_by_{j}_expanded.csv"
                    if not csv_path.exists():
                        print(f"Warning: {csv_path} not found. Run place_filtered() first.")
                        continue
                    
                    data = pd.read_csv(csv_path)
                    data.columns = ["educational_level", "field", "city", "year", "count"]

                    new_data = {major[0]: [0] for major in self.RESHTE_HA}

                    for _, v in data.iterrows():
                        matched_any = False

                        if v["educational_level"] in ["کاردانی ناپیوسته", "کاردانی پیوسته", "کارشناسی ناپیوسته"] and "آموزش و پرورش" not in str(v["field"]):
                            new_data["مهارت"][0] += v["count"]
                            new_data["مهارت"].append(v["field"])
                            continue

                        for major in self.RESHTE_HA:
                            for field_token in major:
                                if field_token in str(v["field"]):
                                    new_data[major[0]][0] += v["count"]
                                    if v["field"] not in new_data[major[0]]:
                                        new_data[major[0]].append(v["field"])
                                    matched_any = True
                                    break
                            if matched_any:
                                break

                    new_data_df = pd.DataFrame({
                        'field': list(new_data.keys()),
                        'count': [values[0] for values in new_data.values()],
                        'subfields': [', '.join(str(x) for x in values[1:]) if len(values) > 1 else '' for values in new_data.values()]
                    })

                    new_data_df.to_csv(
                        self.csv_path / f"top_place_{i}_by_{j}_expanded_grouped_by_field.csv",
                        index=False,
                        encoding="utf-8-sig"
                    )

                    grouped_results[(i, j)] = new_data_df

            if plot and grouped_results:
                fig, axes = plt.subplots(2, 2, figsize=(18, 12))
                panels = [
                    ("receivers", "messages", axes[0, 0], PLOT_PALETTE[0]),
                    ("receivers", "requests", axes[0, 1], PLOT_PALETTE[1]),
                    ("senders", "messages", axes[1, 0], PLOT_PALETTE[2]),
                    ("senders", "requests", axes[1, 1], PLOT_PALETTE[3]),
                ]

                for i_key, j_key, ax, color in panels:
                    df = grouped_results.get((i_key, j_key), pd.DataFrame(columns=['field', 'count', 'subfields']))
                    if df.empty:
                        ax.axis('off')
                        ax.set_title(reshape_text(f"No data for {i_key} by {j_key}"))
                        continue

                    df_plot = df[df['count'] > 0].sort_values('count', ascending=False).head(top_n)
                    x = range(len(df_plot))
                    ax.bar(x, df_plot['count'].values, color=color, edgecolor='black', alpha=0.8)

                    for idx, v in enumerate(df_plot['count'].values):
                        ax.text(idx, v + 0.5, str(int(v)), ha='center', fontsize=12, fontweight='bold')

                    ax.set_title(reshape_text(f"Grouped by Major — {i_key.capitalize()} by {j_key.capitalize()}"), fontsize=12, pad=12)
                    ax.set_xlabel(reshape_text('Major Group'), fontsize=10)
                    ax.set_ylabel(reshape_text('Count'), fontsize=10)
                    ax.set_xticks(list(x))
                    ax.set_xticklabels([reshape_text(lbl) for lbl in df_plot['field']], rotation=45, ha='right')
                    ax.grid(True, axis='y', linestyle='--', alpha=0.7)

                plt.tight_layout()
                plt.savefig(self.plot_path / f'top_place_grouped_by_{by}.png', dpi=300, bbox_inches='tight')
                plt.close()

        elif by == "year":
            a = ["receivers", "senders"]
            b = ["messages", "requests"]
            grouped_results = {}

            for i in a:
                for j in b:
                    csv_path = self.csv_path / f"top_place_{i}_by_{j}_expanded.csv"
                    if not csv_path.exists():
                        print(f"Warning: {csv_path} not found. Run place_filtered() first.")
                        continue
                    
                    data = pd.read_csv(csv_path)
                    data.columns = ["educational_level", "field", "city", "year", "count"]

                    grp = (
                        data.groupby("year", as_index=False)["count"].sum()
                        .sort_values("count", ascending=False)
                    )

                    grp.to_csv(
                        self.csv_path / f"top_place_{i}_by_{j}_expanded_grouped_by_year.csv",
                        index=False,
                        encoding="utf-8-sig"
                    )

                    grouped_results[(i, j)] = grp.rename(columns={"year": "field"})

            if plot and grouped_results:
                fig, axes = plt.subplots(2, 2, figsize=(18, 12))
                panels = [
                    ("receivers", "messages", axes[0, 0], PLOT_PALETTE[0]),
                    ("receivers", "requests", axes[0, 1], PLOT_PALETTE[1]),
                    ("senders", "messages", axes[1, 0], PLOT_PALETTE[2]),
                    ("senders", "requests", axes[1, 1], PLOT_PALETTE[3]),
                ]

                for i_key, j_key, ax, color in panels:
                    df = grouped_results.get((i_key, j_key), pd.DataFrame(columns=['field', 'count']))
                    if df.empty:
                        ax.axis('off')
                        ax.set_title(reshape_text(f"No data for {i_key} by {j_key}"))
                        continue

                    df_plot = df[df['count'] > 0].sort_values('count', ascending=False).head(top_n)
                    x = range(len(df_plot))
                    ax.bar(x, df_plot['count'].values, color=color, edgecolor='black', alpha=0.8)

                    for idx, v in enumerate(df_plot['count'].values):
                        ax.text(idx, v + 0.5, str(int(v)), ha='center', fontsize=12, fontweight='bold')

                    ax.set_title(reshape_text(f"Grouped by Year — {i_key.capitalize()} by {j_key.capitalize()}"), fontsize=12, pad=12)
                    ax.set_xlabel(reshape_text('Year'), fontsize=10)
                    ax.set_ylabel(reshape_text('Count'), fontsize=10)
                    ax.set_xticks(list(x))
                    ax.set_xticklabels([reshape_text(str(lbl)) for lbl in df_plot['field']], rotation=45, ha='right')
                    ax.grid(True, axis='y', linestyle='--', alpha=0.7)

                plt.tight_layout()
                plt.savefig(self.plot_path / f'top_place_grouped_by_{by}.png', dpi=300, bbox_inches='tight')
                plt.close()

        elif by == "educational_level":
            a = ["receivers", "senders"]
            b = ["messages", "requests"]
            grouped_results = {}

            for i in a:
                for j in b:
                    csv_path = self.csv_path / f"top_place_{i}_by_{j}_expanded.csv"
                    if not csv_path.exists():
                        print(f"Warning: {csv_path} not found. Run place_filtered() first.")
                        continue
                    
                    data = pd.read_csv(csv_path)
                    data.columns = ["educational_level", "field", "city", "year", "count"]

                    grp = (
                        data.groupby("educational_level", as_index=False)["count"].sum()
                        .sort_values("count", ascending=False)
                    )

                    grp.to_csv(
                        self.csv_path / f"top_place_{i}_by_{j}_expanded_grouped_by_educational_level.csv",
                        index=False,
                        encoding="utf-8-sig"
                    )

                    grouped_results[(i, j)] = grp.rename(columns={"educational_level": "field"})

            if plot and grouped_results:
                fig, axes = plt.subplots(2, 2, figsize=(18, 12))
                panels = [
                    ("receivers", "messages", axes[0, 0], PLOT_PALETTE[0]),
                    ("receivers", "requests", axes[0, 1], PLOT_PALETTE[1]),
                    ("senders", "messages", axes[1, 0], PLOT_PALETTE[2]),
                    ("senders", "requests", axes[1, 1], PLOT_PALETTE[3]),
                ]

                for i_key, j_key, ax, color in panels:
                    df = grouped_results.get((i_key, j_key), pd.DataFrame(columns=['field', 'count']))
                    if df.empty:
                        ax.axis('off')
                        ax.set_title(reshape_text(f"No data for {i_key} by {j_key}"))
                        continue

                    df_plot = df[df['count'] > 0].sort_values('count', ascending=False).head(top_n)
                    x = range(len(df_plot))
                    ax.bar(x, df_plot['count'].values, color=color, edgecolor='black', alpha=0.8)

                    for idx, v in enumerate(df_plot['count'].values):
                        ax.text(idx, v + 0.5, str(int(v)), ha='center', fontsize=12, fontweight='bold')

                    ax.set_title(reshape_text(f"Grouped by Educational Level — {i_key.capitalize()} by {j_key.capitalize()}"), fontsize=12, pad=12)
                    ax.set_xlabel(reshape_text('Educational Level'), fontsize=10)
                    ax.set_ylabel(reshape_text('Count'), fontsize=10)
                    ax.set_xticks(list(x))
                    ax.set_xticklabels([reshape_text(lbl) for lbl in df_plot['field']], rotation=45, ha='right')
                    ax.grid(True, axis='y', linestyle='--', alpha=0.7)

                plt.tight_layout()
                plt.savefig(self.plot_path / f'top_place_grouped_by_{by}.png', dpi=300, bbox_inches='tight')
                plt.close()

        elif by == "faculty":
            self.place_filtered_by_grouped(by="field", top_n=top_n, plot=False)  # Ensure field grouping is done first
            
            a = ["receivers", "senders"]
            b = ["messages", "requests"]
            grouped_results = {}

            for i in a:
                for j in b:
                    csv_path = self.csv_path / f"top_place_{i}_by_{j}_expanded_grouped_by_field.csv"
                    if not csv_path.exists():
                        print(f"Warning: {csv_path} not found. Run place_filtered_by_grouped(by='field') first.")
                        continue
                    
                    data = pd.read_csv(csv_path)
                    data = data.iloc[:, :2]
                    data.columns = ["field", "count"]
                    
                    # Sum counts for each faculty
                    new_data = {}
                    for faculty_name, fields in self.FACULTY.items():
                        total = data[data["field"].isin(fields)]["count"].sum()
                        new_data[faculty_name] = total
                    
                    new_data_df = pd.DataFrame({
                        'faculty': list(new_data.keys()),
                        'count': list(new_data.values())
                    })

                    # Request counts are also expressed as a share of the faculty's
                    # students. Message counts are not: one student can send many
                    # messages, so that ratio would not be a percentage.
                    if j == "requests":
                        totals = [self.faculty_totals.get(name, 0) for name in new_data_df['faculty']]
                        new_data_df['total_students'] = totals
                        new_data_df['percent'] = [
                            round(count / total * 100, 1) if total else ''
                            for count, total in zip(new_data_df['count'], totals)
                        ]
                        # Ranked by share rather than by raw count, so the CSV reads in
                        # the same order as the plot. Faculties with no student total
                        # have no share and sort last.
                        new_data_df = new_data_df.sort_values(
                            'percent',
                            key=lambda col: col.map(lambda v: v if v != '' else -1),
                            ascending=False
                        ).reset_index(drop=True)
                    
                    # Save CSV
                    new_data_df.to_csv(
                        self.csv_path / f"top_place_{i}_by_{j}_expanded_grouped_by_faculty.csv",
                        index=False,
                        encoding="utf-8-sig"
                    )
                    
                    grouped_results[(i, j)] = new_data_df

            if plot and grouped_results:
                fig, axes = plt.subplots(2, 2, figsize=(18, 12))
                panels = [
                    ("receivers", "messages", axes[0, 0], PLOT_PALETTE[0]),
                    ("receivers", "requests", axes[0, 1], PLOT_PALETTE[1]),
                    ("senders", "messages", axes[1, 0], PLOT_PALETTE[2]),
                    ("senders", "requests", axes[1, 1], PLOT_PALETTE[3]),
                ]

                for i_key, j_key, ax, color in panels:
                    df = grouped_results.get((i_key, j_key), pd.DataFrame(columns=['faculty', 'count']))
                    if df.empty:
                        ax.axis('off')
                        ax.set_title(reshape_text(f"No data for {i_key} by {j_key}"))
                        continue

                    # Request panels are drawn as a share of each faculty's students, so
                    # that a small but heavily engaged faculty is not buried under a large
                    # one. Message counts stay raw: one student sends many messages, so
                    # that ratio would not be a percentage.
                    show_percent = j_key == "requests"
                    if show_percent:
                        df = df.assign(percent_value=[
                            count / self.faculty_totals[name] * 100 if self.faculty_totals.get(name) else None
                            for name, count in zip(df['faculty'], df['count'])
                        ])
                        df_plot = df[df['percent_value'].notna()].sort_values('percent_value', ascending=False).head(top_n)
                        values = df_plot['percent_value'].values
                    else:
                        df_plot = df[df['count'] > 0].sort_values('count', ascending=False).head(top_n)
                        values = df_plot['count'].values

                    if df_plot.empty:
                        # Only reachable on a request panel, when no student total was entered.
                        ax.axis('off')
                        ax.set_title(reshape_text("Enter faculty student totals on the Analyze page"))
                        continue

                    x = range(len(df_plot))
                    ax.bar(x, values, color=color, edgecolor='black', alpha=0.8)

                    # The bar height is the share, so lead the label with it and keep the
                    # raw count underneath.
                    for idx, (v, count) in enumerate(zip(values, df_plot['count'].values)):
                        label = f"{v:.1f}%\n({int(count)})" if show_percent else str(int(v))
                        ax.text(idx, v, label, ha='center', va='bottom', fontsize=12, fontweight='bold')

                    # Headroom for the second label line
                    ax.set_ylim(top=ax.get_ylim()[1] * 1.12)

                    ax.set_title(reshape_text(f"Grouped by Faculty — {i_key.capitalize()} by {j_key.capitalize()}"), fontsize=12, pad=12)
                    ax.set_xlabel(reshape_text('Faculty'), fontsize=10)
                    ax.set_ylabel(reshape_text('Percentage of Faculty Students' if show_percent else 'Count'), fontsize=10)
                    ax.set_xticks(list(x))
                    ax.set_xticklabels([reshape_text(lbl) for lbl in df_plot['faculty']], rotation=45, ha='right')
                    ax.grid(True, axis='y', linestyle='--', alpha=0.7)

                plt.tight_layout()
                plt.savefig(self.plot_path / f'top_place_grouped_by_{by}.png', dpi=300, bbox_inches='tight')
                plt.close()
    
    def _add_reference_table(self, ref_ax, max_rows: int = 25,
                            fontsize: int = 10, alpha: float = 0.9,
                            title: str = "Hami Reference",
                            data_dict: dict = None, ids: list = None):
        """
        Add reference table to plot showing hami ID → name mapping with Persian font support.

        Args:
            ref_ax: matplotlib axis for the reference table
            max_rows: maximum number of rows to show
            fontsize: font size for the text
            alpha: transparency for data rows
            title: title for the reference table
            data_dict: optional custom dict to display (if None, uses people_index)
            ids: optional list of hami IDs to scope the table to (if None, shows every
                 hami_id in the database, unfiltered by date/city)
        """
        ref_ax.clear()
        ref_ax.axis('off')

        if data_dict is None:
            # Use people_index to show hami_id -> name mapping
            data_dict = self.people_index

        # Show only the hami IDs actually present in this plot's data, unless
        # the caller didn't scope it (falls back to every hami_id in the DB)
        hami_ids = ids if ids is not None else self.db.get_unique_hami_ids()
        
        # Build table data: ID -> Name
        items = []
        for hami_id in sorted(hami_ids):
            # Convert hami_id to int for lookup if needed
            try:
                hami_key = int(hami_id)
            except:
                hami_key = hami_id
            
            name = data_dict.get(hami_key, data_dict.get(str(hami_key), 'Unknown'))
            items.append((hami_id, name))
        
        # Limit rows
        truncated = len(items) > max_rows
        items = items[:max_rows]
        
        if items:
            # Create table data with Persian text reshaping
            table_data = []
            for hami_id, name in items:
                # Truncate long names
                name_display = name[:25] + "..." if len(str(name)) > 25 else name
                table_data.append([
                    reshape_text(str(hami_id)),
                    reshape_text(str(name_display))
                ])
            
            if truncated:
                table_data.append([reshape_text("..."), reshape_text("...")])
            
            # Persian column labels
            col_labels = [reshape_text(lbl) for lbl in ['ID', 'Name']]
            
            # Create and style the table
            table = ref_ax.table(
                cellText=table_data,
                colLabels=col_labels,
                cellLoc='left',
                loc='center',
                bbox=[0, 0, 1, 1]
            )
            
            # Auto size columns
            table.auto_set_column_width(col=list(range(len(col_labels))))
            
            # Make Name column wider
            for key, cell in table.get_celld().items():
                if key[1] == 1:  # column index 1 = "Name"
                    cell.set_width(0.6)  # 60% of table width
            
            table.auto_set_font_size(False)
            table.set_fontsize(fontsize)
            table.scale(1, 1.2)
            
            # Style header row
            for i in range(2):
                table[(0, i)].set_facecolor('#4CAF50')
                table[(0, i)].set_text_props(weight='bold', color='white')
            
            # Style data rows with alternating colors
            for i in range(1, len(table_data) + 1):
                for j in range(2):
                    if i % 2 == 0:
                        table[(i, j)].set_facecolor('#f0f0f0')
                    else:
                        table[(i, j)].set_facecolor('white')
                    table[(i, j)].set_alpha(alpha)
        
        # Add reshaped Persian title
        ref_ax.set_title(reshape_text(title), pad=5, fontsize=fontsize+1, weight='bold')


class SQLiteDataLoader:
    """
    Data loader that loads data from SQLite database.
    This is the preferred method for loading data.
    """
    def __init__(self, db: 'HamiDatabase', mapping_data_file_path: Path,
                 start_date: jdatetime.datetime = None, end_date: jdatetime.datetime = None):
        self.db = db
        self.data_frames = {}
        self.hami_frames = {}
        self.people_index = None
        self.mapping_data_file = mapping_data_file_path
        self.start_date = start_date
        self.end_date = end_date
        # For compatibility with DataAnalyzer (date_source not needed for SQLite)
        self.date_source = "first"  # Default value for compatibility
    
    def load_data(self, hami_ids: list = None):
        """Load data from SQLite database"""
        # If hami_ids is None, get all hami IDs
        if hami_ids is None:
            hami_ids = self.db.get_unique_hami_ids()
        
        for hami_id in hami_ids:
            requests = self.db.get_requests_by_hami(hami_id)
            
            for request in requests:
                # Apply date filtering if specified
                if self.start_date or self.end_date:
                    include = True
                    first_date_str = request.get('first_date')
                    if first_date_str:
                        try:
                            first_date = jdatetime.datetime.strptime(first_date_str[:19], '%Y-%m-%d %H:%M:%S')
                            if self.start_date and first_date < self.start_date:
                                include = False
                            if self.end_date and first_date >= self.end_date:
                                include = False
                        except:
                            pass
                    if not include:
                        continue
                
                number = request['number']
                
                # Load messages for this request
                messages = self.db.get_messages_for_request(request['id'])
                
                if messages:
                    # Convert to DataFrame format matching old structure
                    df_data = [{
                        'date': m['date'],
                        'message': m['message'],
                        'from': m['from_name'],
                        'to': m['to_name'],
                        'to_email': m['to_email'],
                        'from_id': m['from_id'],
                        'to_id': m['to_id'],
                        'matched': m['matched']
                    } for m in messages]
                    
                    self.data_frames[(str(hami_id), str(number))] = pd.DataFrame(df_data)
                
                # Store hami data
                if str(hami_id) not in self.hami_frames:
                    self.hami_frames[str(hami_id)] = pd.DataFrame()
                
                hami_row = {
                    'number': request['number'],
                    'subject': request['subject'],
                    'reference_code': request['reference_code'],
                    'major': request['major'],
                    'name': request['name'],
                    'national_id': request['national_id'],
                    'student_id': request['student_id'],
                    'field': request['field']
                }
                self.hami_frames[str(hami_id)] = pd.concat([
                    self.hami_frames[str(hami_id)],
                    pd.DataFrame([hami_row])
                ], ignore_index=True)
        
        # Load people index
        if self.mapping_data_file.exists():
            self.people_index = pd.read_csv(self.mapping_data_file, dtype=str)
            self.people_index.columns = ["id", "name"]
        else:
            self.people_index = pd.DataFrame(columns=["id", "name"])
        
        self.places = list(set(self.get_places()))
        self.employees = list(set(self.get_employees()))
        self.students = list(set(self.get_students()))
    
    def get_data(self, i: str, j: str) -> pd.DataFrame:
        """Retrieve a specific DataFrame by i and j."""
        return self.data_frames.get((i, j), None)

    def get_hami(self, i: str) -> pd.DataFrame:
        """Retrieve a specific Hami DataFrame by i."""
        return self.hami_frames.get(i, None)
    
    def get_places(self) -> list:
        """
        Return a set of all unique place names (from 'from' and 'to' columns) across all data_frames.
        Places are identified as names that end with 4 digit numbers.
        """
        names = []
        for df in self.data_frames.values():
            if 'from' in df.columns:
                names.extend(df['from'].dropna().unique())
            if 'to' in df.columns:
                names.extend(df['to'].dropna().unique())
        # Only keep names that end with 4 digit numbers (these are places/hamis)
        names = [name for name in names if isinstance(name, str) and name.strip()[-4:].isdigit()]
        return list(set(names))
    
    def get_employees(self) -> list:
        """
        Get all employees (people who receive messages but have non-student email patterns).
        Employees are identified by to_email NOT matching the student pattern (10digits@iau.ir).
        """
        employees = []
        for df in self.data_frames.values():
            employees_temp = []
            for i, row in df.iterrows():
                to_value = str(row["to"])
                to_email = str(row["to_email"])
                # Employee emails don't match the student pattern
                if not re.fullmatch(r'^\d{10}@iau\.ir$', to_email):
                    if to_value not in ["<empty>", "Not in workflow"]:
                        employees_temp.append(to_value)
            employees.extend(list(set(employees_temp)))
        
        # Remove places from employee list
        employees = [r for r in employees if r not in self.places]
        return list(set(employees))
    
    def get_students(self) -> list:
        """Get all students from hami files (excluding employees and places)"""
        students = []
        for df in self.hami_frames.values():
            if 'name' in df.columns:
                students_temp = df["name"].tolist()
                students.extend(students_temp)
        students = [r for r in students if r not in self.employees and r not in self.places]
        return list(set(students))
    
    def get_llm_input(self, i: str, j: str) -> str:
        """Get formatted conversation for LLM input"""
        conversation = self.get_data(i, j)
        res = ""
        if conversation is not None and 'date' in conversation.columns:
            unique_dates = conversation.drop_duplicates(subset=['date'])
            for idx, row in unique_dates.iterrows():
                invalids = ["<empty>", None, "Not in workflow", "There is nothing about this message in the Emails."]
                if row["message"] not in invalids:
                    from_ = row["from"]
                    to_ = row["to"]
                    message_ = row["message"]
                    
                    if from_ in invalids:
                        from_ = "someone"
                    elif from_ in self.students:
                        from_ = "student"
                    elif from_ in self.employees:
                        from_ = "employee"
                    elif from_ in self.places:
                        from_ = "hami"
                    
                    if to_ in invalids:
                        to_ = "someone"
                    elif to_ in self.students:
                        to_ = "student"
                    elif to_ in self.employees:
                        to_ = "employee"
                    elif to_ in self.places:
                        to_ = "hami"
                    
                    res += f"{from_} to {to_} : {message_}\n\n"
        return res


class DataLoader:
    def __init__(self, hami_output_folder: Path, mapping_data_file_path: Path, date_source: str, 
                 start_date: jdatetime.datetime = None, end_date: jdatetime.datetime = None):
        self.data_frames = {}
        self.hami_frames = {}
        self.people_index = None
        self.hami_output_folder = hami_output_folder
        self.mapping_data_file = mapping_data_file_path
        self.date_source = date_source
        self.start_date = start_date
        self.end_date = end_date
        if self.date_source not in ["first", "last"]:
            raise ValueError("date_source must be one of ['first', 'last']")

    def load_data(self, dates: list = None):
        # If dates is None, get all date folders
        if dates is None:
            base_path = self.hami_output_folder / self.date_source
            if base_path.exists():
                dates = [d.name for d in base_path.iterdir() if d.is_dir()]
            else:
                dates = []
        
        for date in dates:
            combined_output_path = self.hami_output_folder / self.date_source / date / "combined_output"
            for file in os.listdir(combined_output_path):
                if file.startswith('combined_') and file.endswith('.csv'):
                    parts = file.split('_')
                    if len(parts) == 3:
                        i, j = parts[1], parts[2].replace('.csv', '')
                        path = combined_output_path / file
                
                        # Find the next available j for this i
                        existing_keys = [key for key in self.data_frames.keys() if key[0] == str(i)]
                        next_j = max([int(key[1]) for key in existing_keys], default=0) + 1 if existing_keys else int(j)
                
                        self.data_frames[(str(i), str(next_j))] = pd.read_csv(path)

            # Load hami files (only once, not per date)
            hami_output_path = self.hami_output_folder / self.date_source / date / "hami_output"
            for file in os.listdir(hami_output_path):
                if file.startswith('hami_') and file.endswith('.csv'):
                    parts = file.split('_')
                    if len(parts) == 2:
                        i = parts[1].replace('.csv', '')
                        # Only load if not already loaded
                        if str(i) not in self.hami_frames:
                            path = hami_output_path / file
                            self.hami_frames[str(i)] = pd.read_csv(path)
                        else:
                            path = hami_output_path / file
                            self.hami_frames[str(i)] = pd.concat([self.hami_frames[str(i)], pd.read_csv(path)], axis=0)

        self.people_index = pd.read_csv(self.mapping_data_file, dtype=str)
        self.people_index.columns = ["id", "name"]
        self.places = list(set(self.get_places()))
        self.employees = list(set(self.get_employees()))
        self.students = list(set(self.get_students()))
        
        # Apply date filtering if date range is specified
        if self.start_date or self.end_date:
            self._filter_by_date_range()
    
    def _filter_by_date_range(self):
        """Filter data frames based on start_date and end_date"""
        filtered_data_frames = {}
        filtered_hami_frames = {}
        
        for key, df in self.data_frames.items():
            if 'date' in df.columns:
                # Convert date strings to jdatetime objects
                df_copy = df.copy()
                df_copy['date_obj'] = df_copy['date'].apply(
                    lambda x: jdatetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S') 
                    if x != '1500-01-01 00:00:00' else None
                )
                
                # Filter out dummy dates
                valid_dates = df_copy[df_copy['date_obj'].notna()]
                
                if len(valid_dates) > 0:
                    # Determine the reference date for this dataframe
                    if self.date_source == "first":
                        ref_date = valid_dates['date_obj'].min()
                    else:  # "last"
                        ref_date = valid_dates['date_obj'].max()
                    
                    # Check if this dataframe falls within the date range
                    include = True
                    if self.start_date and ref_date < self.start_date:
                        include = False
                    if self.end_date and ref_date >= self.end_date:
                        include = False
                    
                    if include:
                        filtered_data_frames[key] = df
                        # Also include the corresponding hami entry
                        hami_id = key[0]
                        if hami_id in self.hami_frames:
                            if hami_id not in filtered_hami_frames:
                                # Get the specific row from hami_frames
                                hami_df = self.hami_frames[hami_id]
                                hami_j = int(key[1])
                                if 'number' in hami_df.columns:
                                    matching_rows = hami_df[hami_df['number'] == hami_j]
                                    if len(matching_rows) > 0:
                                        if hami_id not in filtered_hami_frames:
                                            filtered_hami_frames[hami_id] = matching_rows.copy()
                                        else:
                                            filtered_hami_frames[hami_id] = pd.concat([
                                                filtered_hami_frames[hami_id], 
                                                matching_rows
                                            ], axis=0)
        
        # Update the data frames with filtered versions
        self.data_frames = filtered_data_frames
        self.hami_frames = filtered_hami_frames

    def get_data(self, i: str, j: str) -> pd.DataFrame:
        """Retrieve a specific DataFrame by i and j."""
        return self.data_frames.get((i, j), None)

    def get_hami(self, i: str) -> pd.DataFrame:
        """Retrieve a specific Hami DataFrame by i."""
        return self.hami_frames.get(i, None)
    
    def get_llm_input(self, i: str, j: str) -> str:
        conversation = self.get_data(i, j)
        res = ""
        # Get only the rows with unique 'date' values (keep the first occurrence of each date)
        if conversation is not None and 'date' in conversation.columns:
            unique_dates = conversation.drop_duplicates(subset=['date'])
            items = unique_dates.iterrows()
        for i, row in items:
            invalids = ["<empty>", None, "Not in workflow", "There is nothing about this message in the Emails."]
            if not row["message"] in invalids:
                from_ = row["from"]
                to_ = row["to"]
                message_ = row["message"]
                if from_ in invalids:
                    from_ = "someone"
                elif from_ in self.students:
                    from_ = "student"
                elif from_ in self.employees:
                    from_ = "employee"
                elif from_ in self.places:
                    from_ = "hami"
                else:
                    raise ValueError(f"something strage happens 1 : {from_}")

                if to_ in invalids:
                    to_ = "someone"
                elif to_ in self.students:
                    to_ = "student"
                elif to_ in self.employees:
                    to_ = "employee"
                elif to_ in self.places:
                    to_ = "hami"
                else:
                    raise ValueError("Something strage happens 2")
                
                res += f"{from_} to {to_} : {message_}\n\n"
        return res
    
    def get_places(self):
        """
        Return a set of all unique place names (from 'from' and 'to' columns) across all data_frames.
        """
        names = []
        for df in self.data_frames.values():
            if 'from' in df.columns:
                names.extend(df['from'].dropna().unique())
            if 'to' in df.columns:
                names.extend(df['to'].dropna().unique())
        # Only keep names that end with 4 digit numbers
        names = [name for name in names if isinstance(name, str) and name.strip()[-4:].isdigit()]
        return names
    
    def get_employees(self):
        employees = []
        for df in self.data_frames.values():
            employees_temp = []
            for i, row in df.iterrows():
                to_value = str(row["to"])
                to_email = str(row["to_email"])
                if not re.fullmatch(r'^\d{10}@iau\.ir$', to_email):
                    if to_value not in ["<empty>", "Not in workflow"]:
                        employees_temp.append(to_value)
            employees.extend(list(set(employees_temp)))

        employees = [r for r in employees if r not in self.places]
        return employees
    
    def get_students(self):
        students = []
        for df_name, df in self.hami_frames.items():
            students_temp = df["name"].tolist()
            students.extend(students_temp)
        students = [r for r in students if r not in self.employees and r not in self.places]
        return students

class DataAnalyzer:
    # Define major categories for field grouping
    # Order matters! First match wins. Put keshavarzi before pezeshki 
    # so "گیاه پزشکی" matches keshavarzi (via "گیاه") before pezeshki (via "پزشکی")
    RAVAN_SHENASI = ["روانشناسی", "روان_شناسی", "روان شناسی"]
    SANAIE_GAZAII = ["غذا"]
    MODIRIAT_SANATI = ["مهندسی صنایع", "محیط زیست", "محیط_زیست", "صنایع"]
    ZABAN = ["زبان"]
    MODIRIAT_AMOZESHI = ["مدیریت آموزشی", "مدیریت_آموزشی", "ابتدایی", "آموزش"]
    TARBIAT_BADANI = ["تربیت بدنی", "تربیت_بدنی", "ورزشی", "ورزش"]
    GORAN = ["قرآن", "قران"]
    BARG = ["برق"]
    SHIMI = ["شیمی"]
    HOGOG = ["حقوق"]
    MECHANIC = ["مکانیک", "مکاترونیک"]
    GOGRAFIA = ["جغرافیا"]
    KESHAVARZI = ["کشاورزی", "گیاه"]
    MOHANDESI_PEZESHKI = ["مهندسی پزشکی"]
    PEZESHKI = ["پزشکی"]
    COMPUTER = ["کامپیوتر"]
    EGTESAD = ["اقتصاد"]
    NASAJI = ["نساجی"]
    ADABIAT = ["ادبیات"]
    MOSHAVERE = ["مشاوره"]
    OMRAN = ["عمران", "ساخت"]
    HONAR = ["هنر", "مرمت", "نقاشی", "گرافیک", "طراحی", "پارچه", "تصویری", "معماری", "شهری"]
    MICROBIOLOGY = ["میکروبیولوژی", "بیوتکنولوژی", "زیست فناوری"]
    MAVAD = ["مواد", "متالورژی"]
    PARASTARI = ["پرستاری"]
    OTAG_AMAL = ["اتاق عمل"]
    HOSHBARI = ["هوشبری"]
    MODIRIAT = ["مدیریت", "مدیریتی"]
    OLOM_ERTEBATAT = ["علوم ارتباطات", "ارتباطات", "رسانه"]
    HESABDARI = ["حسابداری", "مالی"]
    OLOM_TARBIATI = ["علوم تربیتی", "تربیتی"]
    MAHARAT = ["مهارت"]
    
    # List of all majors in priority order (first match wins)
    RESHTE_HA = [
        RAVAN_SHENASI, SANAIE_GAZAII, MODIRIAT_SANATI, ZABAN, MODIRIAT_AMOZESHI, 
        TARBIAT_BADANI, GORAN, BARG, SHIMI, HOGOG, MECHANIC, GOGRAFIA, KESHAVARZI, 
        MOHANDESI_PEZESHKI, PEZESHKI, COMPUTER, EGTESAD, NASAJI, ADABIAT, MOSHAVERE, 
        OMRAN, HONAR, MICROBIOLOGY, MAVAD, OLOM_ERTEBATAT, PARASTARI, OTAG_AMAL, 
        HOSHBARI, MODIRIAT, OLOM_TARBIATI, HESABDARI, MAHARAT
    ]
    
    # Faculty groupings (uses first element of each major as the key name)
    FACULTY = {"تعلیم و تربیت": RAVAN_SHENASI+MODIRIAT_AMOZESHI+MOSHAVERE+ZABAN+OLOM_TARBIATI,
                "علوم انسانی": MODIRIAT_SANATI+GORAN+HOGOG+HESABDARI+EGTESAD+ADABIAT+OLOM_ERTEBATAT+MODIRIAT,
                "پزشکی": PEZESHKI+PARASTARI+OTAG_AMAL+HOSHBARI,
                "فنی و مهندسی": SHIMI+MECHANIC+NASAJI+OMRAN+KESHAVARZI+SANAIE_GAZAII+MICROBIOLOGY+MAVAD,
                "مهارت و فناوری": MAHARAT,
                "هنر و معماری": TARBIAT_BADANI+GOGRAFIA+HONAR,
                "هوش مصنوعی": BARG+MOHANDESI_PEZESHKI+COMPUTER
                }   
    
    def __init__(self, dataloader: DataLoader, plot_folder:Path, csv_folder:Path):
        self.data_loader = dataloader
        self.plot_path = plot_folder
        if not self.plot_path.exists():
            self.plot_path.mkdir(parents=True, exist_ok=True)
        self.csv_path = csv_folder
        if not self.csv_path.exists():
            self.csv_path.mkdir(parents=True, exist_ok=True)
        
    def total_requests_per_hami(self, plot: bool = False, show_reference: bool = True) -> pd.Series:
        result = pd.Series(dtype=int)
        for hami_id in self.data_loader.hami_frames:
            result[hami_id] = len(self.data_loader.hami_frames[hami_id])
        result.sort_values(ascending=False, inplace=True)

        result.to_csv(self.csv_path / 'total_requests_per_hami.csv', index=True, encoding="utf-8-sig")

        if plot:
            fig = plt.figure(figsize=(14, 8))
            gs = GridSpec(1, 2, width_ratios=[3, 1], figure=fig)

            # Main plot (left, wider area)
            ax = fig.add_subplot(gs[0])
            plot_data = result

            bars = ax.bar(range(len(plot_data)), plot_data.values, 
                color='skyblue', edgecolor='navy', alpha=0.7)

            for i, v in enumerate(plot_data.values):
                ax.text(i, v, str(v), ha='center', fontsize=12, fontweight='bold')

            ax.set_title('Total Requests per Hami', fontsize=12, pad=20)
            ax.set_xlabel("Hami ID", fontsize=10)
            ax.set_ylabel('Requests', fontsize=10)            
            ax.set_xticks(range(len(plot_data)))
            ax.set_xticklabels(plot_data.index, rotation=45, ha='right')
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)

            # Reference table subplot (right, narrower area)
            if show_reference:
                ref_ax = fig.add_subplot(gs[1])
                self._add_reference_table(ref_ax, max_rows=25)

            plt.tight_layout()
            plt.savefig(self.plot_path / 'total_requests_per_hami.png',
                dpi=300, bbox_inches='tight')
            plt.close()  # Close the figure to free memory
            
        return result

    def message_date_distribution(self, plot=False, per='month'):
        """
        Return Series: distribution of all message dates (excluding 1500-01-01), 
        grouped by Jalali month (YYYY-MM).
        Optionally plot the distribution.
        
        Args:
            plot (bool): If True, plots the distribution.
        
        Returns:
            pd.Series: Counts of messages per Jalali month (YYYY-MM).
        """
        dates_requests = []
        dates_messages = []
        for df in self.data_loader.data_frames.values():
            d = df['date'].dropna()
            d = d[d != '1500-01-01 00:00:00']
            
            if self.data_loader.date_source == "last":
                dates_requests.append(jdatetime.datetime.strptime(d.iloc[-1], '%Y-%m-%d %H:%M:%S'))
                for date_str in d:
                    dates_messages.append(jdatetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S'))
            elif self.data_loader.date_source == "first":
                dates_requests.append(jdatetime.datetime.strptime(d.iloc[0], '%Y-%m-%d %H:%M:%S'))
                for date_str in d:
                    dates_messages.append(jdatetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S'))
                
        dates_messages = list(set(dates_messages))
        date_counts = {}
        for date in dates_messages:
            date_key = f"{date.year:04d}-{date.month:02d}-{date.day:02d}"
            date_counts[date_key] = date_counts.get(date_key, 0) + 1
        counts_day = pd.Series(date_counts).sort_index()

        monthly_counts = {}
        for date in dates_messages:
            month_key = f"{date.year:04d}-{date.month:02d}"
            monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
        counts_months = pd.Series(monthly_counts).sort_index()

        monthly_counts_request = {}
        for date in dates_requests:
            month_key = f"{date.year:04d}-{date.month:02d}"
            monthly_counts_request[month_key] = monthly_counts_request.get(month_key, 0) + 1
        counts_months_request = pd.Series(monthly_counts_request).sort_index()

        counts_day.to_csv(self.csv_path / 'message_count_per_day.csv', index=True, encoding="utf-8-sig")
        counts_months.to_csv(self.csv_path / 'message_count_per_month.csv', index=True, encoding="utf-8-sig")
        counts_months_request.to_csv(self.csv_path / 'request_count_per_month.csv', index=True, encoding="utf-8-sig")

        if per == 'day':
            counts = counts_day
        elif per == 'month':
            counts = counts_months
        elif per == 'month_request':
            counts = counts_months_request
        else:
            raise ValueError("Invalid 'per' argument. Expected one of ['day', 'month', 'month_request'].")


        t = "Request" if per == "month_request" else "Message"

        if plot:
            fig = plt.figure(figsize=(14, 8))
            gs = GridSpec(1, 2, width_ratios=[3, 1], figure=fig)

            # Main plot (left, wider area)
            ax = fig.add_subplot(gs[0])
            plot_data = counts

            bars = ax.bar(range(len(plot_data)), plot_data.values, 
            color='skyblue', edgecolor='navy', alpha=0.7)

            for i, v in enumerate(plot_data.values):
                ax.text(i, v, str(v), ha='center', fontsize=12, fontweight='bold')

            ax.set_title(f'{t} Count per Jalali {per.capitalize()}', fontsize=12, pad=20)
            ax.set_xlabel(f'Jalali {per.capitalize()} (YYYY-{per[:3]})', fontsize=10)
            ax.set_ylabel(f'Number of {t}s', fontsize=10)
            ax.set_xticks(range(len(plot_data)))
            ax.set_xticklabels(plot_data.index, rotation=45, ha='right')
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)

            plt.tight_layout()
            # Use correct filename based on type
            if per == 'month_request':
                plot_filename = 'request_count_per_jalali_month.png'
            else:
                plot_filename = f'message_count_per_jalali_{per}.png'
            plt.savefig(self.plot_path / plot_filename, dpi=300, bbox_inches='tight')
            plt.close()  # Close the figure to free memory
        return counts

    def top_communicators_for_employee(self, if_plot: bool = False, n=10):
        """Analyze and plot top employee communicators by message and request counts."""
        
        # Count by messages (all occurrences) - OPTIMIZED with vectorized operations
        send_employee, receive_employee = [], []
        
        for df_name, df in self.data_loader.data_frames.items():
            # Vectorized check: emails that DON'T match student pattern (employee emails)
            is_employee_email = ~df['to_email'].astype(str).str.fullmatch(r'^\d{10}@iau\.ir$', na=False)
            
            # Get employee receivers (where to_value is valid)
            valid_to = ~df['to'].astype(str).isin(["<empty>", "Not in workflow"])
            employee_receivers = df.loc[is_employee_email & valid_to, 'to'].astype(str).tolist()
            receive_employee.extend(employee_receivers)
            
            # Get employee IDs who received messages
            employee_to_ids = df.loc[is_employee_email, 'to_id'].astype(str).unique()
            
            # Get senders who sent to employees (where from_value is valid)
            valid_from = ~df['from'].astype(str).isin(["<empty>", "Not in workflow"])
            is_sender_to_employee = df['from_id'].astype(str).isin(employee_to_ids)
            employee_senders = df.loc[valid_from & is_sender_to_employee, 'from'].astype(str).tolist()
            send_employee.extend(employee_senders)
        
        # Filter out places
        places_set = set(self.data_loader.places)
        send_employee = [r for r in send_employee if r not in places_set]
        receive_employee = [r for r in receive_employee if r not in places_set]
        
        senders_employee_m = pd.Series(Counter(send_employee)).sort_values(ascending=False)
        self.senders_employee_m = senders_employee_m
        senders_employee_m_n = senders_employee_m.head(n)

        receivers_employee_m = pd.Series(Counter(receive_employee)).sort_values(ascending=False)
        self.receivers_employee_m = receivers_employee_m
        receivers_employee_m_n = receivers_employee_m.head(n)
    
        senders_employee_m.to_csv(self.csv_path / 'top_employee_senders_by_messages.csv', index=True, encoding="utf-8-sig")
        receivers_employee_m.to_csv(self.csv_path / 'top_employee_receivers_by_messages.csv', index=True, encoding="utf-8-sig")

        # Count by requests (unique per dataframe) - OPTIMIZED with vectorized operations
        send_employee, receive_employee = [], []
        
        for df_name, df in self.data_loader.data_frames.items():
            # Vectorized check: emails that DON'T match student pattern (employee emails)
            is_employee_email = ~df['to_email'].astype(str).str.fullmatch(r'^\d{10}@iau\.ir$', na=False)
            
            # Get unique employee receivers per request
            valid_to = ~df['to'].astype(str).isin(["<empty>", "Not in workflow"])
            employee_receivers_unique = df.loc[is_employee_email & valid_to, 'to'].astype(str).unique().tolist()
            receive_employee.extend(employee_receivers_unique)
            
            # Get employee IDs who received messages
            employee_to_ids = df.loc[is_employee_email, 'to_id'].astype(str).unique()
            
            # Get unique senders who sent to employees
            valid_from = ~df['from'].astype(str).isin(["<empty>", "Not in workflow"])
            is_sender_to_employee = df['from_id'].astype(str).isin(employee_to_ids)
            employee_senders_unique = df.loc[valid_from & is_sender_to_employee, 'from'].astype(str).unique().tolist()
            send_employee.extend(employee_senders_unique)
        
        # Filter out places
        send_employee = [r for r in send_employee if r not in places_set]
        receive_employee = [r for r in receive_employee if r not in places_set]
        
        senders_employee_r = pd.Series(Counter(send_employee)).sort_values(ascending=False)
        self.senders_employee_r = senders_employee_r
        senders_employee_r_n = senders_employee_r.head(n)

        receivers_employee_r = pd.Series(Counter(receive_employee)).sort_values(ascending=False)
        self.receivers_employee_r = receivers_employee_r
        receivers_employee_r_n = receivers_employee_r.head(n)
        
        senders_employee_r.to_csv(self.csv_path / 'top_employee_senders_by_requests.csv', index=True, encoding="utf-8-sig")
        receivers_employee_r.to_csv(self.csv_path / 'top_employee_receivers_by_requests.csv', index=True, encoding="utf-8-sig")

        if if_plot:
            fig, axes = plt.subplots(2, 2, figsize=(18, 12))
            # Top Employee Receivers plot (left)
            ax1 = axes[0][0]
            if len(receivers_employee_m_n) > 0:
                bars1 = ax1.bar(range(len(receivers_employee_m_n)), receivers_employee_m_n.values, 
                    color='lightblue', edgecolor='darkblue', alpha=0.7)
            for i, v in enumerate(receivers_employee_m_n.values):
                ax1.text(i, v + 0.5, str(v), ha='center', fontsize=12, fontweight='bold')
            ax1.set_title(f'Top {n} Employee Receivers by Message Count', fontsize=12, pad=20)
            ax1.set_xlabel('Employee Name', fontsize=10)
            ax1.set_ylabel('Number of Messages Received', fontsize=10)
            ax1.set_xticks(range(len(receivers_employee_m_n)))
            ax1.set_xticklabels([reshape_text(lbl) for lbl in receivers_employee_m_n.index], rotation=45, ha='right')
            ax1.grid(True, axis='y', linestyle='--', alpha=0.7)

            ax2 = axes[0][1]
            if len(receivers_employee_r_n) > 0:
                bars1 = ax2.bar(range(len(receivers_employee_r_n)), receivers_employee_r_n.values, 
                    color='lightblue', edgecolor='darkblue', alpha=0.7)
            for i, v in enumerate(receivers_employee_r_n.values):
                ax2.text(i, v + 0.5, str(v), ha='center', fontsize=12, fontweight='bold')
            ax2.set_title(f'Top {n} Employee Receivers by Request Count', fontsize=12, pad=20)
            ax2.set_xlabel('Employee Name', fontsize=10)
            ax2.set_ylabel('Number of Requests Received', fontsize=10)
            ax2.set_xticks(range(len(receivers_employee_r_n)))
            ax2.set_xticklabels([reshape_text(lbl) for lbl in receivers_employee_r_n.index], rotation=45, ha='right')
            ax2.grid(True, axis='y', linestyle='--', alpha=0.7)

            ax3 = axes[1][0]
            if len(senders_employee_m_n) > 0:
                bars1 = ax3.bar(range(len(senders_employee_m_n)), senders_employee_m_n.values, 
                    color='lightblue', edgecolor='darkblue', alpha=0.7)
            for i, v in enumerate(senders_employee_m_n.values):
                ax3.text(i, v + 0.5, str(v), ha='center', fontsize=12, fontweight='bold')
            ax3.set_title(f'Top {n} Employee Senders by Message Count', fontsize=12, pad=20)
            ax3.set_xlabel('Employee Name', fontsize=10)
            ax3.set_ylabel('Number of Messages Sent', fontsize=10)
            ax3.set_xticks(range(len(senders_employee_m_n)))
            ax3.set_xticklabels([reshape_text(lbl) for lbl in senders_employee_m_n.index], rotation=45, ha='right')
            ax3.grid(True, axis='y', linestyle='--', alpha=0.7)

            ax4 = axes[1][1]
            if len(senders_employee_r_n) > 0:
                bars1 = ax4.bar(range(len(senders_employee_r_n)), senders_employee_r_n.values, 
                    color='lightblue', edgecolor='darkblue', alpha=0.7)
            for i, v in enumerate(senders_employee_r_n.values):
                ax4.text(i, v + 0.5, str(v), ha='center', fontsize=12, fontweight='bold')
            ax4.set_title(f'Top {n} Employee Senders by Request Count', fontsize=12, pad=20)
            ax4.set_xlabel('Employee Name', fontsize=10)
            ax4.set_ylabel('Number of Requests Sent', fontsize=10)
            ax4.set_xticks(range(len(senders_employee_r_n)))
            ax4.set_xticklabels([reshape_text(lbl) for lbl in senders_employee_r_n.index], rotation=45, ha='right')
            ax4.grid(True, axis='y', linestyle='--', alpha=0.7)

            plt.tight_layout()
            plt.savefig(self.plot_path / 'top_employees.png', dpi=300, bbox_inches='tight')
            plt.close()  # Close the figure to free memory
    
    def top_communicators_for_student(self, if_plot: bool = False, n=10):
        """Analyze and plot top student communicators by message and request counts."""
        
        # Count by messages (all occurrences) - OPTIMIZED with vectorized operations
        send_student, receive_student = [], []
        
        for df_name, df in self.data_loader.data_frames.items():
            # Vectorized check: emails that MATCH student pattern
            is_student_email = df['to_email'].astype(str).str.fullmatch(r'^\d{10}@iau\.ir$', na=False)
            
            # Get student receivers (where to_value is valid)
            valid_to = ~df['to'].astype(str).isin(["<empty>", "Not in workflow"])
            student_receivers = df.loc[is_student_email & valid_to, 'to'].astype(str).tolist()
            receive_student.extend(student_receivers)
            
            # Get student IDs who received messages
            student_to_ids = df.loc[is_student_email, 'to_id'].astype(str).unique()
            
            # Get senders who sent to students (where from_value is valid)
            valid_from = ~df['from'].astype(str).isin(["<empty>", "Not in workflow"])
            is_sender_to_student = df['from_id'].astype(str).isin(student_to_ids)
            student_senders = df.loc[valid_from & is_sender_to_student, 'from'].astype(str).tolist()
            send_student.extend(student_senders)
            
            # Add the student from hami data
            student__ = self.data_loader.get_hami(df_name[0])
            if student__ is not None and not student__.empty:
                student_name = student__[student__["number"] == int(df_name[1])]["name"].values
                if len(student_name) > 0 and student_name[0] != "<empty>":
                    send_student.append(str(student_name[0]))
        
        # Filter out places
        places_set = set(self.data_loader.places)
        send_student = [r for r in send_student if r not in places_set]
        receive_student = [r for r in receive_student if r not in places_set]
        
        senders_student_m = pd.Series(Counter(send_student)).sort_values(ascending=False)
        self.senders_student_m = senders_student_m
        senders_student_m_n = senders_student_m.head(n)

        receivers_student_m = pd.Series(Counter(receive_student)).sort_values(ascending=False)
        self.receivers_student_m = receivers_student_m
        receivers_student_m_n = receivers_student_m.head(n)
        
        senders_student_m.to_csv(self.csv_path / 'top_students_senders_by_messages.csv', index=True, encoding="utf-8-sig")
        receivers_student_m.to_csv(self.csv_path / 'top_student_receivers_by_messages.csv', index=True, encoding="utf-8-sig")

        # Count by requests (unique per dataframe) - OPTIMIZED with vectorized operations
        send_student, receive_student = [], []
        
        for df_name, df in self.data_loader.data_frames.items():
            # Vectorized check: emails that MATCH student pattern
            is_student_email = df['to_email'].astype(str).str.fullmatch(r'^\d{10}@iau\.ir$', na=False)
            
            # Get unique student receivers per request
            valid_to = ~df['to'].astype(str).isin(["<empty>", "Not in workflow"])
            student_receivers_unique = df.loc[is_student_email & valid_to, 'to'].astype(str).unique().tolist()
            receive_student.extend(student_receivers_unique)
            
            # Get student IDs who received messages
            student_to_ids = df.loc[is_student_email, 'to_id'].astype(str).unique()
            
            # Get unique senders who sent to students
            valid_from = ~df['from'].astype(str).isin(["<empty>", "Not in workflow"])
            is_sender_to_student = df['from_id'].astype(str).isin(student_to_ids)
            student_senders_unique = df.loc[valid_from & is_sender_to_student, 'from'].astype(str).unique().tolist()
            send_student.extend(student_senders_unique)
            
            # Add the student from hami data
            student__ = self.data_loader.get_hami(df_name[0])
            if student__ is not None and not student__.empty:
                student_name = student__[student__["number"] == int(df_name[1])]["name"].values
                if len(student_name) > 0 and student_name[0] != "<empty>":
                    send_student.append(str(student_name[0]))
        
        # Filter out places
        send_student = [r for r in send_student if r not in places_set]
        receive_student = [r for r in receive_student if r not in places_set]
        
        senders_student_r = pd.Series(Counter(send_student)).sort_values(ascending=False)
        self.senders_student_r = senders_student_r
        senders_student_r_n = senders_student_r.head(n)

        receivers_student_r = pd.Series(Counter(receive_student)).sort_values(ascending=False)
        self.receivers_student_r = receivers_student_r
        receivers_student_r_n = receivers_student_r.head(n)
        
        senders_student_r.to_csv(self.csv_path / 'top_students_senders_by_requests.csv', index=True, encoding="utf-8-sig")
        receivers_student_r.to_csv(self.csv_path / 'top_student_receivers_by_requests.csv', index=True, encoding="utf-8-sig")

        if if_plot:
            fig, axes = plt.subplots(2, 2, figsize=(18, 12))
            # Top Student Receivers plot (left)
            ax1 = axes[0][0]
            if len(receivers_student_m_n) > 0:
                bars1 = ax1.bar(range(len(receivers_student_m_n)), receivers_student_m_n.values, 
                    color='lightgreen', edgecolor='darkgreen', alpha=0.7)
            for i, v in enumerate(receivers_student_m_n.values):
                ax1.text(i, v + 0.5, str(v), ha='center', fontsize=12, fontweight='bold')
            ax1.set_title(f'Top {n} Student Receivers by Message Count', fontsize=12, pad=20)
            ax1.set_xlabel('Student Name', fontsize=10)
            ax1.set_ylabel('Number of Messages Received', fontsize=10)
            ax1.set_xticks(range(len(receivers_student_m_n)))
            ax1.set_xticklabels([reshape_text(lbl) for lbl in receivers_student_m_n.index], rotation=45, ha='right')
            ax1.grid(True, axis='y', linestyle='--', alpha=0.7)

            ax2 = axes[0][1]
            if len(receivers_student_r_n) > 0:
                bars1 = ax2.bar(range(len(receivers_student_r_n)), receivers_student_r_n.values, 
                    color='lightgreen', edgecolor='darkgreen', alpha=0.7)
            for i, v in enumerate(receivers_student_r_n.values):
                ax2.text(i, v + 0.5, str(v), ha='center', fontsize=12, fontweight='bold')
            ax2.set_title(f'Top {n} Student Receivers by Request Count', fontsize=12, pad=20)
            ax2.set_xlabel('Student Name', fontsize=10)
            ax2.set_ylabel('Number of Requests Received', fontsize=10)
            ax2.set_xticks(range(len(receivers_student_r_n)))
            ax2.set_xticklabels([reshape_text(lbl) for lbl in receivers_student_r_n.index], rotation=45, ha='right')
            ax2.grid(True, axis='y', linestyle='--', alpha=0.7)

            ax3 = axes[1][0]
            if len(senders_student_m_n) > 0:
                bars1 = ax3.bar(range(len(senders_student_m_n)), senders_student_m_n.values, 
                    color='lightgreen', edgecolor='darkgreen', alpha=0.7)
            for i, v in enumerate(senders_student_m_n.values):
                ax3.text(i, v + 0.5, str(v), ha='center', fontsize=12, fontweight='bold')
            ax3.set_title(f'Top {n} Student Senders by Message Count', fontsize=12, pad=20)
            ax3.set_xlabel('Student Name', fontsize=10)
            ax3.set_ylabel('Number of Messages Sent', fontsize=10)
            ax3.set_xticks(range(len(senders_student_m_n)))
            ax3.set_xticklabels([reshape_text(lbl) for lbl in senders_student_m_n.index], rotation=45, ha='right')
            ax3.grid(True, axis='y', linestyle='--', alpha=0.7)

            ax4 = axes[1][1]
            if len(senders_student_r_n) > 0:
                bars1 = ax4.bar(range(len(senders_student_r_n)), senders_student_r_n.values, 
                    color='lightgreen', edgecolor='darkgreen', alpha=0.7)
            for i, v in enumerate(senders_student_r_n.values):
                ax4.text(i, v + 0.5, str(v), ha='center', fontsize=12, fontweight='bold')
            ax4.set_title(f'Top {n} Student Senders by Request Count', fontsize=12, pad=20)
            ax4.set_xlabel('Student Name', fontsize=10)
            ax4.set_ylabel('Number of Requests Sent', fontsize=10)
            ax4.set_xticks(range(len(senders_student_r_n)))
            ax4.set_xticklabels([reshape_text(lbl) for lbl in senders_student_r_n.index], rotation=45, ha='right')
            ax4.grid(True, axis='y', linestyle='--', alpha=0.7)

            plt.tight_layout()
            plt.savefig(self.plot_path / 'top_students.png', dpi=300, bbox_inches='tight')
            plt.close()  # Close the figure to free memory

    def top_communicators_for_place(self, if_plot: bool, n=10):
        send_place, receive_place = [], []
        for df in self.data_loader.data_frames.values():
            if 'from' in df.columns:
                send_place.extend(df['from'].dropna())
            if 'to' in df.columns:
                receive_place.extend(df['to'].dropna())
        # Only keep names that end with 4 digit numbers
        send_place = [name for name in send_place if isinstance(name, str) and name.strip()[-4:].isdigit()]
        receive_place = [name for name in receive_place if isinstance(name, str) and name.strip()[-4:].isdigit()]

        senders_place_m = pd.Series(Counter(send_place)).sort_values(ascending=False)
        self.senders_place_m = senders_place_m
        senders_place_m_n = senders_place_m.head(n)

        receivers_place_m = pd.Series(Counter(receive_place)).sort_values(ascending=False)
        self.receivers_place_m = receivers_place_m
        receivers_place_m_n = receivers_place_m.head(n)
        
        senders_place_m.to_csv(self.csv_path / 'top_place_senders_by_messages.csv', index=True, encoding="utf-8-sig")
        receivers_place_m.to_csv(self.csv_path / 'top_place_receivers_by_messages.csv', index=True, encoding="utf-8-sig")

        send_place, receive_place = [], []
        for df in self.data_loader.data_frames.values():
            if 'from' in df.columns:
                send_place.extend(df['from'].dropna().unique())
            if 'to' in df.columns:
                receive_place.extend(df['to'].dropna().unique())
        send_place = [name for name in send_place if isinstance(name, str) and name.strip()[-4:].isdigit()]
        receive_place = [name for name in receive_place if isinstance(name, str) and name.strip()[-4:].isdigit()]
    
        senders_place_r = pd.Series(Counter(send_place)).sort_values(ascending=False)
        self.senders_place_r = senders_place_r
        senders_place_r_n = senders_place_r.head(n)

        receivers_place_r = pd.Series(Counter(receive_place)).sort_values(ascending=False)
        self.receivers_place_r = receivers_place_r
        receivers_place_r_n = receivers_place_r.head(n)
        
        senders_place_r.to_csv(self.csv_path / 'top_place_senders_by_requests.csv', index=True, encoding="utf-8-sig")
        receivers_place_r.to_csv(self.csv_path / 'top_place_receivers_by_requests.csv', index=True, encoding="utf-8-sig")

        if if_plot:
            fig, axes = plt.subplots(2, 2, figsize=(18, 12))
            ax1 = axes[0][0]
            if len(receivers_place_m_n) > 0:
                bars1 = ax1.bar(range(len(receivers_place_m_n)), receivers_place_m_n.values, 
                    color='orange', edgecolor='brown', alpha=0.7)
            for i, v in enumerate(receivers_place_m_n.values):
                ax1.text(i, v + 0.5, str(v), ha='center', fontsize=12, fontweight='bold')
            ax1.set_title(f'Top {n} Place Receivers by Message Count', fontsize=12, pad=20)
            ax1.set_xlabel('Place Name', fontsize=10)
            ax1.set_ylabel('Number of Messages Received', fontsize=10)
            ax1.set_xticks(range(len(receivers_place_m_n)))
            ax1.set_xticklabels([reshape_text(lbl) for lbl in receivers_place_m_n.index], rotation=45, ha='right')
            ax1.grid(True, axis='y', linestyle='--', alpha=0.7)

            ax2 = axes[0][1]
            if len(receivers_place_r_n) > 0:
                bars1 = ax2.bar(range(len(receivers_place_r_n)), receivers_place_r_n.values, 
                    color='orange', edgecolor='brown', alpha=0.7)
            for i, v in enumerate(receivers_place_r_n.values):
                ax2.text(i, v + 0.5, str(v), ha='center', fontsize=12, fontweight='bold')
            ax2.set_title(f'Top {n} Place Receivers by Request Count', fontsize=12, pad=20)
            ax2.set_xlabel('Place Name', fontsize=10)
            ax2.set_ylabel('Number of Requests Received', fontsize=10)
            ax2.set_xticks(range(len(receivers_place_r_n)))
            ax2.set_xticklabels([reshape_text(lbl) for lbl in receivers_place_r_n.index], rotation=45, ha='right')
            ax2.grid(True, axis='y', linestyle='--', alpha=0.7)

            ax3 = axes[1][0]
            if len(senders_place_m_n) > 0:
                bars1 = ax3.bar(range(len(senders_place_m_n)), senders_place_m_n.values, 
                    color='orange', edgecolor='brown', alpha=0.7)
            for i, v in enumerate(senders_place_m_n.values):
                ax3.text(i, v + 0.5, str(v), ha='center', fontsize=12, fontweight='bold')
            ax3.set_title(f'Top {n} Place Senders by Message Count', fontsize=12, pad=20)
            ax3.set_xlabel('Place Name', fontsize=10)
            ax3.set_ylabel('Number of Messages Sent', fontsize=10)
            ax3.set_xticks(range(len(senders_place_m_n)))
            ax3.set_xticklabels([reshape_text(lbl) for lbl in senders_place_m_n.index], rotation=45, ha='right')
            ax3.grid(True, axis='y', linestyle='--', alpha=0.7)

            ax4 = axes[1][1]
            if len(senders_place_r_n) > 0:
                bars1 = ax4.bar(range(len(senders_place_r_n)), senders_place_r_n.values, 
                    color='orange', edgecolor='brown', alpha=0.7)
            for i, v in enumerate(senders_place_r_n.values):
                ax4.text(i, v + 0.5, str(v), ha='center', fontsize=12, fontweight='bold')
            ax4.set_title(f'Top {n} Place Senders by Request Count', fontsize=12, pad=20)
            ax4.set_xlabel('Place Name', fontsize=10)
            ax4.set_ylabel('Number of Requests Sent', fontsize=10)
            ax4.set_xticks(range(len(senders_place_r_n)))
            ax4.set_xticklabels([reshape_text(lbl) for lbl in senders_place_r_n.index], rotation=45, ha='right')
            ax4.grid(True, axis='y', linestyle='--', alpha=0.7)

            plt.tight_layout()
            plt.savefig(self.plot_path / 'top_places.png', dpi=300, bbox_inches='tight')
            plt.close()  # Close the figure to free memory

    def communication_network(self, plot: bool = False, min_count: int = 5, top_n: int = 20):
        edges = []
        for df in self.data_loader.data_frames.values():
            for _, row in df.iterrows():
                f, t = row.get('from', None), row.get('to', None)
                if pd.notna(f) and pd.notna(t) and f not in ['<empty>', 'Not in workflow'] and t not in ['<empty>', 'Not in workflow']:
                    edges.append((f, t))
        edge_counts = Counter(edges)
        result = pd.DataFrame([(f, t, c) for (f, t), c in edge_counts.items()], columns=['from', 'to', 'count'])
        
        # Save to CSV
        result.to_csv(self.csv_path / 'communication_network.csv', index=False, encoding="utf-8-sig")
        
        if plot:
            # Filter edges by minimum count
            filtered_result = result[result['count'] >= min_count].copy()
            
            if len(filtered_result) == 0:
                print(f"No communication edges found with count >= {min_count}")
                return result
            
            # Get top communicators to limit heatmap size
            all_communicators = set(filtered_result['from'].tolist() + filtered_result['to'].tolist())
            communicator_counts = {}
            for comm in all_communicators:
                send_count = filtered_result[filtered_result['from'] == comm]['count'].sum()
                receive_count = filtered_result[filtered_result['to'] == comm]['count'].sum()
                communicator_counts[comm] = send_count + receive_count
            
            top_communicators = sorted(communicator_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
            top_comm_names = [comm[0] for comm in top_communicators]
            
            # Filter result to only include top communicators
            heatmap_data = filtered_result[
            (filtered_result['from'].isin(top_comm_names)) & 
            (filtered_result['to'].isin(top_comm_names))
            ].copy()
            
            if len(heatmap_data) == 0:
                print(f"No communication data found among top {top_n} communicators")
                return result
            
            # Create pivot table for heatmap
            pivot_table = heatmap_data.pivot_table(
            index='from', 
            columns='to', 
            values='count', 
            fill_value=0
            )
            
            # Ensure all top communicators are included as both rows and columns
            for comm in top_comm_names:
                if comm not in pivot_table.index:
                    pivot_table.loc[comm] = 0
                if comm not in pivot_table.columns:
                    pivot_table[comm] = 0
            
            # Reindex to ensure consistent ordering
            pivot_table = pivot_table.reindex(index=top_comm_names, columns=top_comm_names, fill_value=0)
            
            # Create the plot with reference table for labels
            fig = plt.figure(figsize=(16, 10))
            gs = GridSpec(1, 2, width_ratios=[3, 1], figure=fig)
            ax = fig.add_subplot(gs[0])
            ref_ax = fig.add_subplot(gs[1])

            # Create heatmap with grid and low transparency
            mask = pivot_table == 0  # Mask zero values for better visualization
            sns.heatmap(
            pivot_table.astype(int), 
            annot=True, 
            fmt='d', 
            cmap='YlOrRd',
            ax=ax,
            cbar_kws={'label': 'Number of Messages'},
            mask=mask,
            linewidths=1,           # Thicker grid lines
            linecolor='gray',       # Grid color
            square=True,
            alpha=0.5               # Low transparency for the heatmap
            )
            # Draw grid lines manually for more visible grid (optional)
            for i in range(pivot_table.shape[0] + 1):
                ax.axhline(i, color='gray', lw=0.7, alpha=0.3, zorder=2)
            for j in range(pivot_table.shape[1] + 1):
                ax.axvline(j, color='gray', lw=0.7, alpha=0.3, zorder=2)

            ax.set_title(f'Communication Network Heatmap\n(Top {len(top_comm_names)} Communicators, Min Count: {min_count})', 
                fontsize=14, pad=20)
            ax.set_xlabel('Message Receiver', fontsize=12)
            ax.set_ylabel('Message Sender', fontsize=12)
            # Rotate labels for better readability
            ax.set_xticklabels(ax.get_xticklabels(), rotation=0, ha='right')
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            
            # Replace axis labels with numbers and add reference table
            _, mapping_x = self._add_label_reference_table(ax, ref_ax, axis='x', title="Receiver Mapping")
            _, mapping_y = self._add_label_reference_table(ax, ref_ax, axis='y', title="Sender Mapping")

            plt.tight_layout()
            plt.savefig(self.plot_path / 'communication_network_heatmap.png', 
                   dpi=300, bbox_inches='tight')
            plt.close()  # Close the figure to free memory
            
            # Print summary statistics
            print(f"\nCommunication Network Summary:")
            print(f"Total unique edges: {len(result)}")
            print(f"Total messages in network: {result['count'].sum()}")
            print(f"Edges with count >= {min_count}: {len(filtered_result)}")
            print(f"Top {len(top_comm_names)} communicators included in heatmap")
        
        return result
    
    def total_messages_per_student(self, plot: bool = False):
        # Compute histograms (value_counts) for each
        sent_message_hist = self.senders_student_m.value_counts().sort_index()
        sent_request_hist = self.senders_student_r.value_counts().sort_index()
        received_message_hist = self.receivers_student_m.value_counts().sort_index()
        received_request_hist = self.receivers_student_r.value_counts().sort_index()

        stats = {
            'sent_message_hist': sent_message_hist,
            'sent_request_hist': sent_request_hist,
            'received_message_hist': received_message_hist,
            'received_request_hist': received_request_hist
        }

        if plot:
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            axes = axes.flatten()
            titles = [
            'Messages Sent per Student',
            'Requests Sent per Student',
            'Messages Received per Student',
            'Requests Received per Student'
            ]
            hists = [
            sent_message_hist,
            sent_request_hist,
            received_message_hist,
            received_request_hist
            ]
            colors = ['skyblue', 'lightgreen', 'salmon', 'orange']
            for ax, hist, title, color in zip(axes, hists, titles, colors):
                ax.bar(hist.index, hist.values, color=color)
                for i, v in enumerate(hist.values):
                    ax.text(hist.index[i], v + 0.5, str(v), ha='center', fontsize=12, fontweight='bold')
                    ax.set_title(title)
                ax.set_xlabel(title[:-12])
                ax.set_ylabel('Number of Students')
                ax.grid(True, axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(self.plot_path / 'total_messages_per_student.png', dpi=300, bbox_inches='tight')
            plt.close()  # Close the figure to free memory

        return stats    

    def common_titles(self, n=20, plot_: bool = False):
        from collections import Counter
        titles = []
        for df in self.data_loader.hami_frames.values():
            if 'subject' in df.columns:
                subjects = df['subject'].dropna()
                titles.extend(subjects[subjects != '<empty>'])
        result = pd.Series(Counter(titles)).sort_values(ascending=False).head(n)
        result2 = pd.Series(Counter(titles)).sort_values(ascending=False)
        # Save to CSV
        result2.to_csv(self.csv_path / 'common_titles.csv', index=True, encoding="utf-8-sig")
        # Plot if requested
        if plot_:
            fig, ax = plt.subplots(figsize=(12, 6))
            bars = ax.bar(range(len(result.index)), result.values, color='skyblue', edgecolor='navy', alpha=0.7)
            for i, v in enumerate(result.values):
                ax.text(i, v + 0.5, str(v), ha='center', fontsize=12, fontweight='bold')
                ax.set_title(reshape_text('Most Common Titles (Subjects)'), fontsize=12, pad=20)
                ax.set_xlabel(reshape_text('Title'), fontsize=10)
                ax.set_ylabel(reshape_text('Count'), fontsize=10)
                ax.set_xticks(range(len(result.index)))
                ax.set_xticklabels([reshape_text(lbl) for lbl in result.index], rotation=45, ha='right')
                ax.grid(True, axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(self.plot_path / 'common_titles.png', dpi=300, bbox_inches='tight')
            plt.close()  # Close the figure to free memory
        
        return result

    def response_time_per_person(self, plot: bool = False):
        response_times = defaultdict(list)
        first_response_times = defaultdict(list)
        for k, df in self.data_loader.data_frames.items():
            person_id = k[0]
            d = df['date'].dropna()
            d = d[d != '1500-01-01 00:00:00']
            if len(d) > 1:
                times = []
                for date_str in d:
                    jalali_dt = jdatetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    times.append(jalali_dt)
                # Remove duplicate times (keep order)
                seen = set()
                unique_times = []
                for t in times:
                    if t not in seen:
                        unique_times.append(t)
                        seen.add(t)
                times = sorted(unique_times)
                # Only compute deltas if there are at least 2 unique times
                if len(times) > 1:
                    deltas = [(t2 - t1).total_seconds() / 3600 for t1, t2 in zip(times[:-1], times[1:])]
                    # Filter out zero deltas
                    deltas = [delta for delta in deltas if delta != 0]
                    if deltas:
                        response_times[person_id].extend(deltas)
                    # First response time (between first and second unique message)
                    first_response = (times[1] - times[0]).total_seconds() / 3600
                    if first_response != 0:
                        first_response_times[person_id].append(first_response)
        # Compute average per person
        avg_response = {pid: np.mean(times) for pid, times in response_times.items() if times}
        avg_first_response = {pid: np.mean(times) for pid, times in first_response_times.items() if times}
        avg_response_series = pd.Series(avg_response).sort_values(ascending=False)
        avg_first_response_series = pd.Series(avg_first_response).sort_values(ascending=False)

        avg_first_response_series.to_csv(self.csv_path / 'avg_first_response_time_per_person.csv', index=True, encoding="utf-8-sig")
        avg_response_series.to_csv(self.csv_path / 'avg_response_time_per_person.csv', index=True, encoding="utf-8-sig")

        if plot:
            fig = plt.figure(figsize=(20, 10))
            # Create a GridSpec with 2 rows, 2 columns; right column is for reference table
            gs = gridspec.GridSpec(2, 2, width_ratios=[5, 2], height_ratios=[1, 1], figure=fig)

            # Top: avg_response_series bar plot (spans both rows in left column)
            ax1 = fig.add_subplot(gs[0, 0])
            ax1.bar(avg_response_series.index, avg_response_series.values, color='skyblue', edgecolor='navy', alpha=0.7)
            ax1.set_title('Average Response Time per Person (hours)')
            ax1.set_ylabel('Avg Response Time (h)')
            ax1.set_xticks(range(len(avg_response_series.index)))
            ax1.set_xticklabels(avg_response_series.index, rotation=45, ha='right')
            ax1.grid(True, axis='y', linestyle='--', alpha=0.7)

            # Bottom: avg_first_response_series bar plot (below the first plot, same width)
            ax2 = fig.add_subplot(gs[1, 0])
            ax2.bar(avg_first_response_series.index, avg_first_response_series.values, color='lightcoral', edgecolor='darkred', alpha=0.7)
            ax2.set_title('Average First Response Time per Person (hours)')
            ax2.set_ylabel('Avg First Response (h)')
            ax2.set_xlabel('Person ID')
            ax2.set_xticks(range(len(avg_first_response_series.index)))
            ax2.set_xticklabels(avg_first_response_series.index, rotation=45, ha='right')
            ax2.grid(True, axis='y', linestyle='--', alpha=0.7)

            # Reference table: right side, spanning both rows
            ref_ax = fig.add_subplot(gs[:, 1])
            self._add_reference_table(ref_ax, max_rows=40, title="Hami Reference")
            plt.tight_layout()
            plt.savefig(self.plot_path / 'response_time_per_person.png', dpi=300, bbox_inches='tight')
            plt.close()  # Close the figure to free memory
        return avg_response_series, avg_first_response_series

    def place_filtered(self):
        a = ["receivers", "senders"]
        b = ["messages", "requests"]
        for i in a:
            for j in b:
                data = pd.read_csv(self.csv_path / f"top_place_{i}_by_{j}.csv")
                data.columns = ["Place", "Count"]
                new_data = pd.DataFrame(columns=["educational_level", "field", "city", "year", "count"])
                for k, v in data.iterrows():
                    try:
                        if "_" in v["Place"]:
                            dataaa = v["Place"].split("_")
                            if len(dataaa) == 4:
                                educational_level, field, city, year = dataaa
                            elif len(dataaa) == 5:
                                educational_level, field, city, year = dataaa[0], dataaa[1] + "_" + dataaa[2], dataaa[3], dataaa[4]
                        else:
                            educational_level, field, city, year = v["Place"].split("-")
                        new_data.loc[len(new_data)] = {"educational_level": educational_level, "field": field, "city": city, "year": year, "count": v["Count"]}
                    except ValueError:
                        print(f"Error processing row {i}: {v['Place']}")

                new_data.to_csv(self.csv_path / f"top_place_{i}_by_{j}_expanded.csv", index=False, encoding="utf-8-sig")

    def place_filtered_by(self, by="field", top_n=20, plot=True):
        if by == "field":
            a = ["receivers", "senders"]
            b = ["messages", "requests"]


            # Keep grouped results to plot 4 subplots at the end
            grouped_results = {}  # key: (i, j) -> DataFrame

            for i in a:
                for j in b:
                    data = pd.read_csv(self.csv_path / f"top_place_{i}_by_{j}_expanded.csv")
                    data.columns = ["educational_level", "field", "city", "year", "count"]

                    # Initialize dictionary with group labels and counters
                    new_data = {major[0]: [0] for major in self.RESHTE_HA}

                    for _, v in data.iterrows():
                        matched_any = False

                        # Vocational-ish bucket (کاردانی...) unless it's explicit teacher training
                        if v["educational_level"] in ["کاردانی ناپیوسته", "کاردانی پیوسته", "کارشناسی ناپیوسته"] and "آموزش و پرورش" not in v["field"]:
                            new_data["مهارت"][0] += v["count"]
                            new_data["مهارت"].append(v["field"])
                            continue

                        # Match field tokens to a major bucket
                        for major in self.RESHTE_HA:
                            for field_token in major:
                                if field_token in v["field"]:
                                    new_data[major[0][0:]][0] += v["count"]
                                    if v["field"] not in new_data[major[0]]:
                                        new_data[major[0]].append(v["field"])
                                    matched_any = True
                                    break
                            if matched_any:
                                break

                        if not matched_any:
                            # Unmatched fields will be printed for review
                            print(v["field"])

                    new_data_df = pd.DataFrame({
                        'field': list(new_data.keys()),
                        'count': [values[0] for values in new_data.values()],
                        'subfields': [', '.join(values[1:]) if len(values) > 1 else '' for values in new_data.values()]
                    })

                    # Save CSV per combination
                    new_data_df.to_csv(
                        self.csv_path / f"top_place_{i}_by_{j}_expanded_grouped_by_field.csv",
                        index=False,
                        encoding="utf-8-sig"
                    )

                    grouped_results[(i, j)] = new_data_df

            if plot:
                # Plot 4 panels: receivers/messages, receivers/requests, senders/messages, senders/requests
                fig, axes = plt.subplots(2, 2, figsize=(18, 12))
                panels = [
                    ("receivers", "messages", axes[0, 0], PLOT_PALETTE[0]),
                    ("receivers", "requests", axes[0, 1], PLOT_PALETTE[1]),
                    ("senders", "messages", axes[1, 0], PLOT_PALETTE[2]),
                    ("senders", "requests", axes[1, 1], PLOT_PALETTE[3]),
                ]

                for i_key, j_key, ax, color in panels:
                    df = grouped_results.get((i_key, j_key), pd.DataFrame(columns=['field', 'count', 'subfields']))
                    if df.empty:
                        ax.axis('off')
                        ax.set_title(reshape_text(f"No data for {i_key} by {j_key}"))
                        continue

                    df_plot = df[df['count'] > 0].sort_values('count', ascending=False).head(top_n)
                    x = range(len(df_plot))
                    ax.bar(x, df_plot['count'].values, color=color, edgecolor='black', alpha=0.8)

                    for idx, v in enumerate(df_plot['count'].values):
                        ax.text(idx, v + 0.5, str(int(v)), ha='center', fontsize=12, fontweight='bold')

                    ax.set_title(reshape_text(f"Grouped by Major — {i_key.capitalize()} by {j_key.capitalize()}"), fontsize=12, pad=12)
                    ax.set_xlabel(reshape_text('Major Group'), fontsize=10)
                    ax.set_ylabel(reshape_text('Count'), fontsize=10)
                    ax.set_xticks(list(x))
                    ax.set_xticklabels([reshape_text(lbl) for lbl in df_plot['field']], rotation=45, ha='right')
                    ax.grid(True, axis='y', linestyle='--', alpha=0.7)

                plt.tight_layout()
                plt.savefig(self.plot_path / f'top_place_grouped_by_{by}.png', dpi=300, bbox_inches='tight')
                plt.close()
                
        elif by =="faculty":
            self.place_filtered_by(by="field", top_n=top_n, plot=False)  # Ensure field grouping is done first
            
            a = ["receivers", "senders"]
            b = ["messages", "requests"]
            grouped_results = {}

            for i in a:
                for j in b:
                    csv_path = self.csv_path / f"top_place_{i}_by_{j}_expanded_grouped_by_field.csv"
                    if not csv_path.exists():
                        print(f"Warning: {csv_path} not found. Run place_filtered_by(by='field') first.")
                        continue
                    
                    data = pd.read_csv(csv_path)
                    data = data.iloc[:, :2]
                    data.columns = ["field", "count"]
                    
                    # Sum counts for each faculty
                    new_data = {}
                    for faculty_name, fields in self.FACULTY.items():
                        total = data[data["field"].isin(fields)]["count"].sum()
                        new_data[faculty_name] = total
                    
                    new_data_df = pd.DataFrame({
                        'faculty': list(new_data.keys()),
                        'count': list(new_data.values())
                    })
                    
                    # Save CSV
                    new_data_df.to_csv(
                        self.csv_path / f"top_place_{i}_by_{j}_expanded_grouped_by_faculty.csv",
                        index=False,
                        encoding="utf-8-sig"
                    )
                    
                    grouped_results[(i, j)] = new_data_df

            if plot and grouped_results:
                fig, axes = plt.subplots(2, 2, figsize=(18, 12))
                panels = [
                    ("receivers", "messages", axes[0, 0], PLOT_PALETTE[0]),
                    ("receivers", "requests", axes[0, 1], PLOT_PALETTE[1]),
                    ("senders", "messages", axes[1, 0], PLOT_PALETTE[2]),
                    ("senders", "requests", axes[1, 1], PLOT_PALETTE[3]),
                ]

                for i_key, j_key, ax, color in panels:
                    df = grouped_results.get((i_key, j_key), pd.DataFrame(columns=['faculty', 'count']))
                    if df.empty:
                        ax.axis('off')
                        ax.set_title(reshape_text(f"No data for {i_key} by {j_key}"))
                        continue

                    df_plot = df[df['count'] > 0].sort_values('count', ascending=False).head(top_n)
                    x = range(len(df_plot))
                    ax.bar(x, df_plot['count'].values, color=color, edgecolor='black', alpha=0.8)

                    for idx, v in enumerate(df_plot['count'].values):
                        ax.text(idx, v + 0.5, str(int(v)), ha='center', fontsize=12, fontweight='bold')

                    ax.set_title(reshape_text(f"Grouped by Faculty — {i_key.capitalize()} by {j_key.capitalize()}"), fontsize=12, pad=12)
                    ax.set_xlabel(reshape_text('Faculty'), fontsize=10)
                    ax.set_ylabel(reshape_text('Count'), fontsize=10)
                    ax.set_xticks(list(x))
                    ax.set_xticklabels([reshape_text(lbl) for lbl in df_plot['faculty']], rotation=45, ha='right')
                    ax.grid(True, axis='y', linestyle='--', alpha=0.7)

                plt.tight_layout()
                plt.savefig(self.plot_path / f'top_place_grouped_by_{by}.png', dpi=300, bbox_inches='tight')
                plt.close()
                
        elif by =="year":
            a = ["receivers", "senders"]
            b = ["messages", "requests"]

            grouped_results = {}

            for i in a:
                for j in b:
                    data = pd.read_csv(self.csv_path / f"top_place_{i}_by_{j}_expanded.csv")
                    data.columns = ["educational_level", "field", "city", "year", "count"]

                    # Group by year and sum counts
                    grp = (
                        data.groupby("year", as_index=False)["count"].sum()
                        .sort_values("count", ascending=False)
                    )

                    # Save CSV per combination
                    grp.to_csv(
                        self.csv_path / f"top_place_{i}_by_{j}_expanded_grouped_by_year.csv",
                        index=False,
                        encoding="utf-8-sig"
                    )

                    # Keep for plotting
                    grouped_results[(i, j)] = grp.rename(columns={"year": "field"})

            if plot:
                # Plot 4 panels
                fig, axes = plt.subplots(2, 2, figsize=(18, 12))
                panels = [
                    ("receivers", "messages", axes[0, 0], PLOT_PALETTE[0]),
                    ("receivers", "requests", axes[0, 1], PLOT_PALETTE[1]),
                    ("senders", "messages", axes[1, 0], PLOT_PALETTE[2]),
                    ("senders", "requests", axes[1, 1], PLOT_PALETTE[3]),
                ]

                for i_key, j_key, ax, color in panels:
                    df = grouped_results.get((i_key, j_key), pd.DataFrame(columns=['field', 'count']))
                    if df.empty:
                        ax.axis('off')
                        ax.set_title(reshape_text(f"No data for {i_key} by {j_key}"))
                        continue

                    df_plot = df[df['count'] > 0].sort_values('count', ascending=False).head(top_n)
                    x = range(len(df_plot))
                    ax.bar(x, df_plot['count'].values, color=color, edgecolor='black', alpha=0.8)

                    for idx, v in enumerate(df_plot['count'].values):
                        ax.text(idx, v + 0.5, str(int(v)), ha='center', fontsize=12, fontweight='bold')

                    ax.set_title(reshape_text(f"Grouped by Year — {i_key.capitalize()} by {j_key.capitalize()}"), fontsize=12, pad=12)
                    ax.set_xlabel(reshape_text('Year'), fontsize=10)
                    ax.set_ylabel(reshape_text('Count'), fontsize=10)
                    ax.set_xticks(list(x))
                    ax.set_xticklabels([reshape_text(str(lbl)) for lbl in df_plot['field']], rotation=45, ha='right')
                    ax.grid(True, axis='y', linestyle='--', alpha=0.7)

                plt.tight_layout()
                plt.savefig(self.plot_path / f'top_place_grouped_by_{by}.png', dpi=300, bbox_inches='tight')
                plt.close()
        elif by =="educational_level":
            a = ["receivers", "senders"]
            b = ["messages", "requests"]

            grouped_results = {}

            for i in a:
                for j in b:
                    data = pd.read_csv(self.csv_path / f"top_place_{i}_by_{j}_expanded.csv")
                    data.columns = ["educational_level", "field", "city", "year", "count"]

                    # Group by educational level and sum counts
                    grp = (
                        data.groupby("educational_level", as_index=False)["count"].sum()
                        .sort_values("count", ascending=False)
                    )

                    # Save CSV per combination
                    grp.to_csv(
                        self.csv_path / f"top_place_{i}_by_{j}_expanded_grouped_by_educational_level.csv",
                        index=False,
                        encoding="utf-8-sig"
                    )

                    # Keep for plotting
                    grouped_results[(i, j)] = grp.rename(columns={"educational_level": "field"})

            if plot:
                # Plot 4 panels
                fig, axes = plt.subplots(2, 2, figsize=(18, 12))
                panels = [
                    ("receivers", "messages", axes[0, 0], PLOT_PALETTE[0]),
                    ("receivers", "requests", axes[0, 1], PLOT_PALETTE[1]),
                    ("senders", "messages", axes[1, 0], PLOT_PALETTE[2]),
                    ("senders", "requests", axes[1, 1], PLOT_PALETTE[3]),
                ]

                for i_key, j_key, ax, color in panels:
                    df = grouped_results.get((i_key, j_key), pd.DataFrame(columns=['field', 'count']))
                    if df.empty:
                        ax.axis('off')
                        ax.set_title(reshape_text(f"No data for {i_key} by {j_key}"))
                        continue

                    df_plot = df[df['count'] > 0].sort_values('count', ascending=False).head(top_n)
                    x = range(len(df_plot))
                    ax.bar(x, df_plot['count'].values, color=color, edgecolor='black', alpha=0.8)

                    for idx, v in enumerate(df_plot['count'].values):
                        ax.text(idx, v + 0.5, str(int(v)), ha='center', fontsize=12, fontweight='bold')

                    ax.set_title(reshape_text(f"Grouped by Educational Level — {i_key.capitalize()} by {j_key.capitalize()}"), fontsize=12, pad=12)
                    ax.set_xlabel(reshape_text('Educational Level'), fontsize=10)
                    ax.set_ylabel(reshape_text('Count'), fontsize=10)
                    ax.set_xticks(list(x))
                    ax.set_xticklabels([reshape_text(lbl) for lbl in df_plot['field']], rotation=45, ha='right')
                    ax.grid(True, axis='y', linestyle='--', alpha=0.7)

                plt.tight_layout()
                plt.savefig(self.plot_path / f'top_place_grouped_by_{by}.png', dpi=300, bbox_inches='tight')
                plt.close()

    def _add_reference_table(self, ref_ax, max_rows=10, 
                            fontsize=12, alpha=0.9, title="Hami Reference"):
        """
        Add a reference subplot showing the mapping from reference_id(id) numbers 
        to employee ID and name, with Persian font support.

        Args:
            ref_ax: matplotlib axis object for the reference table (created via GridSpec)
            max_rows: int, maximum number of rows to display
            fontsize: int, font size for the text
            alpha: float, transparency
            title: str, title for the reference subplot
        
        Returns:
            matplotlib axis object for the reference subplot
        """
        # Create reference data
        ref_data = self.data_loader.people_index.copy()
        ref_data['file_num'] = ref_data["id"].astype(int)
        ref_data = ref_data.sort_values('file_num')

        # Limit rows if needed
        if len(ref_data) > max_rows:
            ref_data = ref_data.head(max_rows)
            truncated = True
        else:
            truncated = False

        # Clear and turn off axis
        ref_ax.clear()
        ref_ax.axis('off')

        # Create table data, reshape for Persian support
        table_data = []
        for _, row in ref_data.iterrows():
            name = row['name'][:25] + "..." if len(row['name']) > 25 else row['name']
            table_data.append([
                reshape_text(f"{row['id']}"),
                reshape_text(name)
            ])
        if truncated:
            table_data.append([reshape_text("..."), reshape_text("..."), reshape_text("...")])

        # Persian column labels
        col_labels = [reshape_text(lbl) for lbl in ['ID', 'Name']]

        # Create and style the table
        table = ref_ax.table(cellText=table_data,
                            colLabels=col_labels,
                            cellLoc='left',
                            loc='center',
                            bbox=[0, 0, 1, 1])

        table.auto_set_column_width(col=list(range(len(col_labels))))  # auto size
        for key, cell in table.get_celld().items():
            if key[1] == 1:   # column index 2 = "Name"
                cell.set_width(0.5)   # make wider (0.5 = 50% of table width)

        table.auto_set_font_size(False)
        table.set_fontsize(fontsize)
        table.scale(1, 1.2)

        # Style header row
        for i in range(2):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')

        # Style data rows
        for i in range(1, len(table_data) + 1):
            for j in range(2):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#f0f0f0')
                else:
                    table[(i, j)].set_facecolor('white')
                table[(i, j)].set_alpha(alpha)

        # Add reshaped Persian title
        ref_ax.set_title(reshape_text(title), pad=5, fontsize=fontsize+1, weight='bold')

        return ref_ax

    def _add_label_reference_table(self, ax, ref_ax, axis='x', 
                                fontsize=8, alpha=0.9, title="Label Reference"):
        """
        Replace axis labels with numeric codes and add a reference table subplot
        showing the mapping from numbers to original labels, with Persian font support.

        Args:
            ax: matplotlib axis object for the main plot
            ref_ax: matplotlib axis object for the reference table (GridSpec subplot)
            axis: 'x' or 'y' – which axis labels to replace
            fontsize: int, font size for the text
            alpha: float, transparency
            title: str, title for the reference subplot

        Returns:
            ref_ax: matplotlib axis object for the reference subplot
            mapping: dict {number -> original label}
        """
        # 1. Get original labels
        if axis == 'x':
            orig_labels = [tick.get_text() for tick in ax.get_xticklabels()]
        else:
            orig_labels = [tick.get_text() for tick in ax.get_yticklabels()]

        # 2. Build mapping
        mapping = {i+1: lbl for i, lbl in enumerate(orig_labels)}

        # 3. Replace axis labels with numbers
        if axis == 'x':
            ax.set_xticks(range(len(orig_labels)))
            ax.set_xticklabels([str(i+1) for i in range(len(orig_labels))], rotation=45, ha='right')
        else:
            ax.set_yticks(range(len(orig_labels)))
            ax.set_yticklabels([str(i+1) for i in range(len(orig_labels))], rotation=0)

        # 4. Clear and turn off ref_ax
        ref_ax.clear()
        ref_ax.axis('off')

        # 5. Prepare table data (Number → Label), reshape for Persian support
        table_data = [[str(k), reshape_text(v)] for k, v in mapping.items()]

        # 6. Create table
        table = ref_ax.table(cellText=table_data,
                            colLabels=[reshape_text('#'), reshape_text('برچسب')],
                            cellLoc='left',
                            loc='center',
                            bbox=[0, 0, 1, 1])

        table.auto_set_column_width(col=[0, 1])  # let it size columns
        for key, cell in table.get_celld().items():
            if key[1] == 1:  # Label column
                cell.set_width(0.7)

        table.auto_set_font_size(False)
        table.set_fontsize(fontsize)
        table.scale(1, 1.2)

        # Style header row
        for i in range(2):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')

        # Style data rows
        for i in range(1, len(table_data) + 1):
            for j in range(2):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#f0f0f0')
                else:
                    table[(i, j)].set_facecolor('white')
                table[(i, j)].set_alpha(alpha)

        # Add reshaped Persian title
        ref_ax.set_title(reshape_text(title), pad=5, fontsize=fontsize+1, weight='bold')

        return ref_ax, mapping
    