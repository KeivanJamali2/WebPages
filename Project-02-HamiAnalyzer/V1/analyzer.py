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

configure_matplotlib_for_persian(font_size=12, font_family="sans-serif")

class DataLoader:
    def __init__(self, hami_output_folder: Path, mapping_data_file_path: Path, date_source: str):
        self.data_frames = {}
        self.hami_frames = {}
        self.people_index = None
        self.hami_output_folder = hami_output_folder
        self.mapping_data_file = mapping_data_file_path
        self.date_source = date_source
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
                ax.text(i, v, str(v), ha='center', fontsize=9)

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
            plt.show()
            
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
        dates = []
        data_request = []
        for df in self.data_loader.data_frames.values():
            d = df['date'].dropna()
            d = d[d != '1500-01-01 00:00:00']
            
            if self.data_loader.date_source == "last":
                dates.append(jdatetime.datetime.strptime(d.iloc[-1], '%Y-%m-%d %H:%M:%S'))
            elif self.data_loader.date_source == "first":
                dates.append(jdatetime.datetime.strptime(d.iloc[0], '%Y-%m-%d %H:%M:%S'))
                
        date_counts = {}
        for date in dates:
            date_key = f"{date.year:04d}-{date.month:02d}-{date.day:02d}"
            date_counts[date_key] = date_counts.get(date_key, 0) + 1
        counts_day = pd.Series(date_counts).sort_index()

        monthly_counts = {}
        for date in dates:
            month_key = f"{date.year:04d}-{date.month:02d}"
            monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
        counts_months = pd.Series(monthly_counts).sort_index()

        monthly_counts_request = {}
        for date in data_request:
            month_key = f"{date.year:04d}-{date.month:02d}"
            monthly_counts_request[month_key] = monthly_counts_request.get(month_key, 0) + 1
        counts_months_request = pd.Series(monthly_counts_request).sort_index()

        counts_day.to_csv(self.csv_path / 'message_count_per_day.csv', index=True, encoding="utf-8-sig")
        counts_months.to_csv(self.csv_path / 'message_count_per_month.csv', index=True, encoding="utf-8-sig")
        counts_months_request.to_csv(self.csv_path / 'message_count_per_month_requests.csv', index=True, encoding="utf-8-sig")

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
                ax.text(i, v, str(v), ha='center', fontsize=9)

            ax.set_title(f'{t} Count per Jalali {per.capitalize()}', fontsize=12, pad=20)
            ax.set_xlabel(f'Jalali {per.capitalize()} (YYYY-{per[:3]})', fontsize=10)
            ax.set_ylabel(f'Number of {t}s', fontsize=10)
            ax.set_xticks(range(len(plot_data)))
            ax.set_xticklabels(plot_data.index, rotation=45, ha='right')
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)

            plt.tight_layout()
            plt.savefig(self.plot_path / f'message_count_per_jalali_{per}.png', dpi=300, bbox_inches='tight')
            plt.show()
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
                ax1.text(i, v + 0.5, str(v), ha='center', fontsize=9)
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
                ax2.text(i, v + 0.5, str(v), ha='center', fontsize=9)
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
                ax3.text(i, v + 0.5, str(v), ha='center', fontsize=9)
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
                ax4.text(i, v + 0.5, str(v), ha='center', fontsize=9)
            ax4.set_title(f'Top {n} Employee Senders by Request Count', fontsize=12, pad=20)
            ax4.set_xlabel('Employee Name', fontsize=10)
            ax4.set_ylabel('Number of Requests Sent', fontsize=10)
            ax4.set_xticks(range(len(senders_employee_r_n)))
            ax4.set_xticklabels([reshape_text(lbl) for lbl in senders_employee_r_n.index], rotation=45, ha='right')
            ax4.grid(True, axis='y', linestyle='--', alpha=0.7)

            plt.tight_layout()
            plt.savefig(self.plot_path / 'top_employees.png', dpi=300, bbox_inches='tight')
            plt.show()
    
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
                ax1.text(i, v + 0.5, str(v), ha='center', fontsize=9)
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
                ax2.text(i, v + 0.5, str(v), ha='center', fontsize=9)
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
                ax3.text(i, v + 0.5, str(v), ha='center', fontsize=9)
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
                ax4.text(i, v + 0.5, str(v), ha='center', fontsize=9)
            ax4.set_title(f'Top {n} Student Senders by Request Count', fontsize=12, pad=20)
            ax4.set_xlabel('Student Name', fontsize=10)
            ax4.set_ylabel('Number of Requests Sent', fontsize=10)
            ax4.set_xticks(range(len(senders_student_r_n)))
            ax4.set_xticklabels([reshape_text(lbl) for lbl in senders_student_r_n.index], rotation=45, ha='right')
            ax4.grid(True, axis='y', linestyle='--', alpha=0.7)

            plt.tight_layout()
            plt.savefig(self.plot_path / 'top_students.png', dpi=300, bbox_inches='tight')
            plt.show()

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

        if if_plot:
            fig, axes = plt.subplots(2, 2, figsize=(18, 12))
            ax1 = axes[0][0]
            if len(receivers_place_m_n) > 0:
                bars1 = ax1.bar(range(len(receivers_place_m_n)), receivers_place_m_n.values, 
                    color='orange', edgecolor='brown', alpha=0.7)
            for i, v in enumerate(receivers_place_m_n.values):
                ax1.text(i, v + 0.5, str(v), ha='center', fontsize=9)
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
                ax2.text(i, v + 0.5, str(v), ha='center', fontsize=9)
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
                ax3.text(i, v + 0.5, str(v), ha='center', fontsize=9)
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
                ax4.text(i, v + 0.5, str(v), ha='center', fontsize=9)
            ax4.set_title(f'Top {n} Place Senders by Request Count', fontsize=12, pad=20)
            ax4.set_xlabel('Place Name', fontsize=10)
            ax4.set_ylabel('Number of Requests Sent', fontsize=10)
            ax4.set_xticks(range(len(senders_place_r_n)))
            ax4.set_xticklabels([reshape_text(lbl) for lbl in senders_place_r_n.index], rotation=45, ha='right')
            ax4.grid(True, axis='y', linestyle='--', alpha=0.7)

            plt.tight_layout()
            plt.savefig(self.plot_path / 'top_places.png', dpi=300, bbox_inches='tight')
            plt.show()

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
            plt.show()
            
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
                    ax.text(hist.index[i], v + 0.5, str(v), ha='center', fontsize=9)
                    ax.set_title(title)
                ax.set_xlabel(title[:-12])
                ax.set_ylabel('Number of Students')
                ax.grid(True, axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(self.plot_path / 'total_messages_per_student.png', dpi=300, bbox_inches='tight')
            plt.show()

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
                ax.text(i, v + 0.5, str(v), ha='center', fontsize=9)
                ax.set_title(reshape_text('Most Common Titles (Subjects)'), fontsize=12, pad=20)
                ax.set_xlabel(reshape_text('Title'), fontsize=10)
                ax.set_ylabel(reshape_text('Count'), fontsize=10)
                ax.set_xticks(range(len(result.index)))
                ax.set_xticklabels([reshape_text(lbl) for lbl in result.index], rotation=45, ha='right')
                ax.grid(True, axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(self.plot_path / 'common_titles.png', dpi=300, bbox_inches='tight')
            plt.show()

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
            plt.show()
        return avg_response_series, avg_first_response_series


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