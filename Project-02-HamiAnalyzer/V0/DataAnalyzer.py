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
    def __init__(self, hami_output_folder: Path, extra_data_file_path: Path):
        self.data_frames = {}
        self.hami_frames = {}
        self.people_index = None
        self.hami_output_folder = hami_output_folder
        self.extra_data_file = extra_data_file_path

    def load_data(self):
        """Load all CSV files matching 'combined_{i}_{j}.csv' into a dictionary of DataFrames."""
        for file in os.listdir(self.hami_output_folder / "combined_output"):
            if file.startswith('combined_') and file.endswith('.csv'):
                parts = file.split('_')
                if len(parts) == 3:
                    i, j = parts[1], parts[2].replace('.csv', '')
                    path = self.hami_output_folder / "combined_output" / file
                    self.data_frames[(str(i), str(j))] = pd.read_csv(path)

        for file in os.listdir(self.hami_output_folder / "hami_output"):
            if file.startswith('hami_') and file.endswith('.csv'):
                parts = file.split('_')
                if len(parts) == 2:
                    _, i = parts[0], parts[1].replace('.csv', '')
                    path = self.hami_output_folder / "hami_output" / file
                    self.hami_frames[str(i)] = pd.read_csv(path)

        self.people_index = pd.read_csv(self.extra_data_file, dtype=str)
        self.people_index.columns = ["id", "name"]
        self.places = self.get_places()
        self.employees = self.get_employees()
        self.students = self.get_students()

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
                elif from_ == "STUDENT":
                    from_ = "student"
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
        names = set()
        for df in self.data_frames.values():
            if 'from' in df.columns:
                names.update(df['from'].dropna().unique())
            if 'to' in df.columns:
                names.update(df['to'].dropna().unique())
        # Only keep names that end with 4 digit numbers
        names = {name for name in names if isinstance(name, str) and name.strip()[-4:].isdigit()}
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
        employees = list(set(employees))
        return employees
    
    def get_students(self):
        students = []
        for df_name, df in self.data_frames.items():
            students_temp = []
            for i, row in df.iterrows():
                to_value = str(row["to"])
                to_email = str(row["to_email"])
                if re.fullmatch(r'^\d{10}@iau\.ir$', to_email):
                    if to_value not in ["<empty>", "Not in workflow"]:
                        students_temp.append(to_value)
                student__ = self.get_hami(df_name[0])
                student__ = student__[student__["number"] == int(df_name[1])]["name"].values[0]
                if not student__ == "<empty>":
                    students_temp.append(student__)

            students.extend(list(set(students_temp)))

        students = [r for r in students if r not in self.places]
        students = list(set(students))
        return students


class DataAnalyzer:
    def __init__(self, dataloader: DataLoader, plot_folder:Path, csv_folder:Path):
        self.data_loader = dataloader
        self.places = self.data_loader.places
        self.employees = self.data_loader.employees
        self.students = self.data_loader.students
        self.plot_path = plot_folder
        self.csv_path = csv_folder
        self.top_communicators()

    # 1. General Statistics & Data Quality
    def total_requests_per_hami(self, plot: bool = False, show_reference: bool = True) -> pd.Series:
        """
        Return a Series: number of requests per Hami (first element of key).
        
        Args:
            plot (bool): If True, creates a bar plot of the results.
            show_reference (bool): If True, adds a reference table to the plot.
            
        Returns:
            pd.Series: Count of requests per employee
        """
        # Get the counts of requests per employee ID
        keys = [k[0] for k in self.data_loader.data_frames.keys()]
        result = pd.Series(Counter(keys)).sort_values(ascending=False)

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
            ax.set_xticklabels(plot_data.index, rotation=0, ha='right')
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)

            # Reference table subplot (right, narrower area)
            if show_reference:
                ref_ax = fig.add_subplot(gs[1])
                self.add_reference_table(ref_ax, max_rows=25, title="Hami Reference")
            plt.tight_layout()
            plt.savefig(self.plot_path / 'total_requests_per_hami.png',
                dpi=300, bbox_inches='tight')
            plt.show()
            
        return result

    def total_messages_per_request(self, plot: bool = False, top_n: int = 20, show_reference: bool = True) -> pd.Series:
        """
        Return a Series: number of messages per request (key).
        
        Args:
            plot (bool): If True, creates a bar plot of the results.
            top_n (int): Number of top requests to show in the plot
            show_reference (bool): If True, adds a reference table to the plot.
            
        Returns:
            pd.Series: Count of messages per request
        """
        result = pd.Series({k: len(df) for k, df in self.data_loader.data_frames.items()}).sort_values(ascending=False)
        
        result.to_csv(self.csv_path / 'total_messages_per_request.csv', index=True, encoding="utf-8-sig")

        if plot:
            fig = plt.figure(figsize=(14, 8))
            gs = GridSpec(1, 2, width_ratios=[3, 1], figure=fig)

            # Main plot (left, wider area)
            ax = fig.add_subplot(gs[0])
            plot_data = result.head(top_n)
            bars = ax.bar(range(len(plot_data)), plot_data.values, 
                  color='skyblue', edgecolor='navy', alpha=0.7)
            
            for i, v in enumerate(plot_data.values):
                ax.text(i, v + 0.5, str(v), ha='center', fontsize=9)
            
            # Persian and English titles and labels
            title = f"Top {top_n} Requests by Number of Messages"
            xlabel = "Request ID (Hami-id, request)"
            ylabel = "Number of Messages"

            ax.set_title(title, fontsize=12, pad=20)
            ax.set_xlabel(xlabel, fontsize=10)
            ax.set_ylabel(ylabel, fontsize=10)            
            ax.set_xticks(range(len(plot_data)))
            ax.set_xticklabels([f"({','.join(idx)})" for idx in plot_data.index], 
                    rotation=45, ha='right')
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)

            # Reference table subplot (right, narrower area)
            if show_reference:
                ref_ax = fig.add_subplot(gs[1])
                self.add_reference_table(ref_ax, max_rows=25)

            plt.tight_layout()
            plt.savefig(self.plot_path / 'total_messages_per_request.png', 
                   dpi=300, bbox_inches='tight')
            plt.show()
            
        return result

    def missing_data_stats(self):
        """
        Return DataFrame: percent missing for sender, receiver, text, per request and overall.
        Optionally plot the top requests with the most missing data.
        
        Returns:
            pd.DataFrame: Stats per request (key, total, missing_sender, missing_receiver, missing_text)
        """
        stats = []
        for k, df in self.data_loader.data_frames.items():
            # Note: <empty> means the message is empty. not missing.
            total = len(df["date"].unique())
            missing_sender = (df['from'] == 'Not in workflow').sum()
            missing_receiver = (df['to'] == 'Not in workflow').sum()
            missing_text = (df['message'] == 'There is nothing about this message in the Emails.').sum()
            stats.append({
                'key': k,
                'total': total,
                'missing_sender': missing_sender,
                'missing_receiver': missing_receiver,
                'missing_text': missing_text
            })
        df_stats = pd.DataFrame(stats)
        df_stats['total_missing'] = df_stats[['missing_receiver', 'missing_text']].sum(axis=1)
        df_stats = df_stats.sort_values('total_missing', ascending=False)
        df_stats.to_csv(self.csv_path / 'missing_data_stats_per_request.csv', index=False, encoding="utf-8-sig")
        return df_stats

    def message_date_distribution(self, plot=False, per='month', date_source='last'):
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
            if date_source == "last":
                data_request.append(jdatetime.datetime.strptime(d.iloc[-1], '%Y-%m-%d %H:%M:%S'))
            else:
                data_request.append(jdatetime.datetime.strptime(d.iloc[0], '%Y-%m-%d %H:%M:%S'))
            for date_str in d:
                jalali_dt = jdatetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                dates.append(jalali_dt.date())
        
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
            ax.set_xticklabels(plot_data.index, rotation=90, ha='right')
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)

            plt.tight_layout()
            plt.savefig(self.plot_path / f'message_count_per_jalali_{per}.png', dpi=300, bbox_inches='tight')
            plt.show()
        
        return counts

    # 2. Communication Patterns
    def top_communicators(self, for_who: str=None, n=10):
        """
        Return top n senders and receivers by message count, separated by persons and places.
        
        Args:
            n (int): Number of top communicators to return
            plot (bool): If True, creates bar plots of the results
            show_reference (bool): If True, adds a reference table to the plot
            
        Returns:
            dict: Contains separate Series for person_senders, person_receivers, place_senders, place_receivers
        """
        send_place, receive_place = [], []
        for df in self.data_loader.data_frames.values():
            if 'from' in df.columns:
                send_place.extend(df['from'].dropna())
            if 'to' in df.columns:
                receive_place.extend(df['to'].dropna())
        # Only keep names that end with 4 digit numbers
        send_place = [name for name in send_place if isinstance(name, str) and name.strip()[-4:].isdigit()]
        receive_place = [name for name in receive_place if isinstance(name, str) and name.strip()[-4:].isdigit()]
    
        send_employee, receive_employee = [], []
        send_student, receive_student = [], []
        for df_name, df in self.data_loader.data_frames.items():
            check_sender_employee = []
            check_sender_student = []
            for i, row in df.iterrows():
                to_value = str(row["to"])
                to_email = str(row["to_email"])
                from_id = str(row["from_id"])
                from_value = str(row["from"])
                if not re.fullmatch(r'^\d{10}@iau\.ir$', to_email):
                    check_sender_employee.append(str(row["to_id"]))
                    if to_value not in ["<empty>", "Not in workflow"]:
                        receive_employee.append(to_value)
                if from_value not in ["<empty>", "Not in workflow"]:
                    if from_id in check_sender_employee:
                        send_employee.append(from_value)

                if re.fullmatch(r'^\d{10}@iau\.ir$', to_email):
                    check_sender_student.append(str(row["to_id"]))
                    if to_value not in ["<empty>", "Not in workflow"]:
                        receive_student.append(to_value)
                if from_value not in ["<empty>", "Not in workflow"]:
                    if from_id in check_sender_student:
                        send_student.append(from_value)
                student__ = self.data_loader.get_hami(df_name[0])
                student__ = student__[student__["number"] == int(df_name[1])]["name"].values[0]
                if not student__ == "<empty>":
                    send_student.append(student__)


        send_employee = [r for r in send_employee if r not in self.places]
        receive_employee = [r for r in receive_employee if r not in self.places]
        send_student = [r for r in send_student if r not in self.places]
        receive_student = [r for r in receive_student if r not in self.places]
    
        senders_place_m = pd.Series(Counter(send_place)).sort_values(ascending=False)
        self.senders_place_m = senders_place_m
        senders_place_m_n = senders_place_m.head(n)

        receivers_place_m = pd.Series(Counter(receive_place)).sort_values(ascending=False)
        self.receivers_place_m = receivers_place_m
        receivers_place_m_n = receivers_place_m.head(n)

        senders_employee_m = pd.Series(Counter(send_employee)).sort_values(ascending=False)
        self.senders_employee_m = senders_employee_m
        senders_employee_m_n = senders_employee_m.head(n)

        receivers_employee_m = pd.Series(Counter(receive_employee)).sort_values(ascending=False)
        self.receivers_employee_m = receivers_employee_m
        receivers_employee_m_n = receivers_employee_m.head(n)

        senders_student_m = pd.Series(Counter(send_student)).sort_values(ascending=False)
        self.senders_student_m = senders_student_m
        senders_student_m_n = senders_student_m.head(n)

        receivers_student_m = pd.Series(Counter(receive_student)).sort_values(ascending=False)
        self.receivers_student_m = receivers_student_m
        receivers_student_m_n = senders_student_m.head(n)

        senders_place_m.to_csv(self.csv_path / 'top_place_senders_by_messages.csv', index=True, encoding="utf-8-sig")
        receivers_place_m.to_csv(self.csv_path / 'top_place_receivers_by_messages.csv', index=True, encoding="utf-8-sig")
        senders_employee_m.to_csv(self.csv_path / 'top_employee_senders_by_messages.csv', index=True, encoding="utf-8-sig")
        receivers_employee_m.to_csv(self.csv_path / 'top_employee_receivers_by_messages.csv', index=True, encoding="utf-8-sig")
        senders_student_m.to_csv(self.csv_path / 'top_students_senders_by_messages.csv', index=True, encoding="utf-8-sig")
        receivers_student_m.to_csv(self.csv_path / 'top_student_receivers_by_messages.csv', index=True, encoding="utf-8-sig")

        ################################################
        send_place, receive_place = [], []
        for df in self.data_loader.data_frames.values():
            if 'from' in df.columns:
                send_place.extend(df['from'].dropna().unique())
            if 'to' in df.columns:
                receive_place.extend(df['to'].dropna().unique())
        send_place = [name for name in send_place if isinstance(name, str) and name.strip()[-4:].isdigit()]
        receive_place = [name for name in receive_place if isinstance(name, str) and name.strip()[-4:].isdigit()]
    
        send_employee, receive_employee = [], []
        send_student, receive_student = [], []
        for df_name, df in self.data_loader.data_frames.items():
            check_sender_employee = []
            check_sender_student = []
            es_temp, er_temp = [], []
            ss_temp, sr_temp = [], []
            for i, row in df.iterrows():
                to_value = str(row["to"])
                to_email = str(row["to_email"])
                from_id = str(row["from_id"])
                from_value = str(row["from"])
                if not re.fullmatch(r'^\d{10}@iau\.ir$', to_email):
                    check_sender_employee.append(str(row["to_id"]))
                    if to_value not in ["<empty>", "Not in workflow"]:
                        er_temp.append(to_value)
                if from_value not in ["<empty>", "Not in workflow"]:
                    if from_id in check_sender_employee:
                        es_temp.append(from_value)
                    
                if re.fullmatch(r'^\d{10}@iau\.ir$', to_email):
                    check_sender_student.append(str(row["to_id"]))
                    if to_value not in ["<empty>", "Not in workflow"]:
                        sr_temp.append(to_value)
                if from_value not in ["<empty>", "Not in workflow"]:
                    if from_id in check_sender_student:
                        ss_temp.append(from_value)
                student__ = self.data_loader.get_hami(df_name[0])
                student__ = student__[student__["number"] == int(df_name[1])]["name"].values[0]
                if not student__ == "<empty>":
                    ss_temp.append(student__)

            send_student.extend(list(set(ss_temp)))
            receive_student.extend(list(set(sr_temp)))
            send_employee.extend(list(set(es_temp)))
            receive_employee.extend(list(set(er_temp)))
            
        print(len(send_student))
        print(len(self.data_loader.data_frames.values()))

        send_employee = [r for r in send_employee if r not in self.places]
        receive_employee = [r for r in receive_employee if r not in self.places]
        send_student = [r for r in send_student if r not in self.places]
        receive_student = [r for r in receive_student if r not in self.places]

        senders_place_r = pd.Series(Counter(send_place)).sort_values(ascending=False)
        self.senders_place_r = senders_place_r
        senders_place_r_n = senders_place_r.head(n)

        receivers_place_r = pd.Series(Counter(receive_place)).sort_values(ascending=False)
        self.receivers_place_r = receivers_place_r
        receivers_place_r_n = receivers_place_r.head(n)

        senders_employee_r = pd.Series(Counter(send_employee)).sort_values(ascending=False)
        self.senders_employee_r = senders_employee_r
        senders_employee_r_n = senders_employee_r.head(n)

        receivers_employee_r = pd.Series(Counter(receive_employee)).sort_values(ascending=False)
        self.receivers_employee_r = receivers_employee_r
        receivers_employee_r_n = receivers_employee_r.head(n)

        senders_student_r = pd.Series(Counter(send_student)).sort_values(ascending=False)
        self.senders_student_r = senders_student_r
        senders_student_r_n = senders_student_r.head(n)

        receivers_student_r = pd.Series(Counter(receive_student)).sort_values(ascending=False)
        self.receivers_student_r = receivers_student_r
        receivers_student_r_n = senders_student_r.head(n)

        senders_place_r.to_csv(self.csv_path / 'top_place_senders_by_requests.csv', index=True, encoding="utf-8-sig")
        receivers_place_r.to_csv(self.csv_path / 'top_place_receivers_by_requests.csv', index=True, encoding="utf-8-sig")
        senders_employee_r.to_csv(self.csv_path / 'top_employee_senders_by_requests.csv', index=True, encoding="utf-8-sig")
        receivers_employee_r.to_csv(self.csv_path / 'top_employee_receivers_by_requests.csv', index=True, encoding="utf-8-sig")
        senders_student_r.to_csv(self.csv_path / 'top_students_senders_by_requests.csv', index=True, encoding="utf-8-sig")
        receivers_student_r.to_csv(self.csv_path / 'top_student_receivers_by_requests.csv', index=True, encoding="utf-8-sig")

        if for_who == "employee":
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

        elif for_who == "student":
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

        elif for_who == "place":
            fig, axes = plt.subplots(2, 2, figsize=(18, 12))
            # Top Place Receivers plot (left)
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
        """
        Return DataFrame: edges (from, to, count) for network graph.
        Optionally create a heatmap visualization of the communication network.
        
        Args:
            plot (bool): If True, creates a heatmap of the communication network
            min_count (int): Minimum count threshold for including edges in heatmap
            top_n (int): Maximum number of top communicators to include in heatmap
            show_reference (bool): If True, adds a reference table to the plot
            
        Returns:
            pd.DataFrame: Communication edges with columns ['from', 'to', 'count']
        """
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
            _, mapping_x = self.add_label_reference_table(ax, ref_ax, axis='x', title="Receiver Mapping")
            _, mapping_y = self.add_label_reference_table(ax, ref_ax, axis='y', title="Sender Mapping")

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
        """
        Returns histograms of how many students sent/received 1, 2, 3, ... messages or requests.
        Uses self.senders_student_m (messages sent), self.senders_student_r (requests sent),
        self.receivers_student_m (messages received), and self.receivers_student_r (requests received).
        Optionally plots the histograms.
        Returns:
            dict: {
            'sent_message_hist': pd.Series,
            'sent_request_hist': pd.Series,
            'received_message_hist': pd.Series,
            'received_request_hist': pd.Series
            }
        """
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
        """
        Return Series: most common titles (subjects) in all hami_output DataFrames.
        Optionally saves to CSV and plots a histogram.
        """
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
        """
        Return Series: average response time (in hours) per person (person_id from k[0]), using Jalali dates.
        Also returns the mean response time between the first two messages for each person.
        Optionally plots both series.
        
        Args:
            plot (bool): If True, plots the average response times.
        
        Returns:
            tuple: (avg_response: pd.Series, avg_first_response: pd.Series)
        """
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
            self.add_reference_table(ref_ax, max_rows=40, title="Hami Reference")
            plt.tight_layout()
            plt.savefig(self.plot_path / 'response_time_per_person.png', dpi=300, bbox_inches='tight')
            plt.show()
        return avg_response_series, avg_first_response_series

    # Reference Table Function (GridSpec-compatible, Persian support)
    def add_reference_table(self, ref_ax, max_rows=10, 
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

    def add_label_reference_table(self, ax, ref_ax, axis='x', 
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

    def place_filtered_by(self, by="field", top_n=20):
        if by == "field":
            a = ["receivers", "senders"]
            b = ["messages", "requests"]

            ravan_shenasi = ["روانشناسی", "روان_شناسی", "روان شناسی"]
            moridriat_sanati = ["مدیریت صنعتی", "مدیریت_صنعتی", "محیط زیست", "محیط_زیست", "صنایع"]
            modiriat_amozeshi = ["مدیریت آموزشی", "مدیریت_آموزشی", "ابتدایی", "آموزش"]
            tarbiat_badani = ["تربیت بدنی", "تربیت_بدنی", "ورزشی", "ورزش"]
            goran = ["قرآن", "قران"]
            barg = ["برق"]
            shimi = ["شیمی"]
            hogog = ["حقوق"]
            hesabdari = ["حسابداری", "مالی"]
            mechanic = ["مکانیک", "مکاترونیک"]
            gografia = ["جغرافیا"]
            mohandesi_pezeshki = ["مهندسی پزشکی"]
            pezeshki = ["پزشکی"]
            computer = ["کامپیوتر"]
            egtesad = ["اقتصاد"]
            nasagi = ["نساجی"]
            adabiat = ["ادبیات"]
            moshavere = ["مشاوره"]
            orman = ["عمران"]
            keshavarzi = ["کشاورزی"]
            honar = ["هنر", "مرمت", "نقاشی", "گرافیک", "طراحی", "پارچه", "تصویری", "معماری", "شهری"]
            zaban = ["زبان"]
            sanaie_gazaii = ["صنایع غذایی"]
            microbiology = ["میکروبیولوژی", "بیوتکنولوژی", "زیست فناوری"]
            mavad = ["مواد", "متالورژی"]
            olom_ertebatat = ["علوم ارتباطات", "ارتباطات", "رسانه"]
            parastari = ["پرستاری"]
            otag_amav = ["اتاق عمل"]
            hoshbari = ["هوشبری"]
            modiriat = ["مدیریت", "مدیریتی"]
            olom_tarbiati = ["تربیتی"]
            maharat = ["مهارت خاصصصصصص"]

            reshte_ha = [
                ravan_shenasi, moridriat_sanati, modiriat_amozeshi, tarbiat_badani, goran, barg, shimi, hogog,
                hesabdari, mechanic, gografia, mohandesi_pezeshki, pezeshki, computer, egtesad, nasagi, adabiat,
                moshavere, orman, keshavarzi, honar, zaban, sanaie_gazaii, microbiology, mavad, olom_ertebatat,
                parastari, otag_amav, hoshbari, modiriat, olom_tarbiati, maharat
            ]

            # Keep grouped results to plot 4 subplots at the end
            grouped_results = {}  # key: (i, j) -> DataFrame

            for i in a:
                for j in b:
                    data = pd.read_csv(self.csv_path / f"top_place_{i}_by_{j}_expanded.csv")
                    data.columns = ["educational_level", "field", "city", "year", "count"]

                    # Initialize dictionary with group labels and counters
                    new_data = {major[0]: [0] for major in reshte_ha}

                    for _, v in data.iterrows():
                        matched_any = False

                        # Vocational-ish bucket (کاردانی...) unless it's explicit teacher training
                        if v["educational_level"] in ["کاردانی ناپیوسته", "کاردانی پیوسته", "کارشناسی ناپیوسته"] and "آموزش و پرورش" not in v["field"]:
                            new_data["مهارت خاصصصصصص"][0] += v["count"]
                            new_data["مهارت خاصصصصصص"].append(v["field"])
                            continue

                        # Match field tokens to a major bucket
                        for major in reshte_ha:
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

            # Plot 4 panels: receivers/messages, receivers/requests, senders/messages, senders/requests
            fig, axes = plt.subplots(2, 2, figsize=(18, 12))
            panels = [
                ("receivers", "messages", axes[0, 0], 'orange'),
                ("receivers", "requests", axes[0, 1], 'skyblue'),
                ("senders", "messages", axes[1, 0], 'lightgreen'),
                ("senders", "requests", axes[1, 1], 'salmon'),
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
                    ax.text(idx, v + 0.5, str(int(v)), ha='center', fontsize=9)

                ax.set_title(reshape_text(f"Grouped by Major — {i_key.capitalize()} by {j_key.capitalize()}"), fontsize=12, pad=12)
                ax.set_xlabel(reshape_text('Major Group'), fontsize=10)
                ax.set_ylabel(reshape_text('Count'), fontsize=10)
                ax.set_xticks(list(x))
                ax.set_xticklabels([reshape_text(lbl) for lbl in df_plot['field']], rotation=45, ha='right')
                ax.grid(True, axis='y', linestyle='--', alpha=0.7)

            plt.tight_layout()
            plt.savefig(self.plot_path / f'top_place_grouped_by_{by}.png', dpi=300, bbox_inches='tight')
            plt.show()
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

            # Plot 4 panels
            fig, axes = plt.subplots(2, 2, figsize=(18, 12))
            panels = [
                ("receivers", "messages", axes[0, 0], 'orange'),
                ("receivers", "requests", axes[0, 1], 'skyblue'),
                ("senders", "messages", axes[1, 0], 'lightgreen'),
                ("senders", "requests", axes[1, 1], 'salmon'),
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
                    ax.text(idx, v + 0.5, str(int(v)), ha='center', fontsize=9)

                ax.set_title(reshape_text(f"Grouped by Year — {i_key.capitalize()} by {j_key.capitalize()}"), fontsize=12, pad=12)
                ax.set_xlabel(reshape_text('Year'), fontsize=10)
                ax.set_ylabel(reshape_text('Count'), fontsize=10)
                ax.set_xticks(list(x))
                ax.set_xticklabels([reshape_text(str(lbl)) for lbl in df_plot['field']], rotation=45, ha='right')
                ax.grid(True, axis='y', linestyle='--', alpha=0.7)

            plt.tight_layout()
            plt.savefig(self.plot_path / f'top_place_grouped_by_{by}.png', dpi=300, bbox_inches='tight')
            plt.show()
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

            # Plot 4 panels
            fig, axes = plt.subplots(2, 2, figsize=(18, 12))
            panels = [
                ("receivers", "messages", axes[0, 0], 'orange'),
                ("receivers", "requests", axes[0, 1], 'skyblue'),
                ("senders", "messages", axes[1, 0], 'lightgreen'),
                ("senders", "requests", axes[1, 1], 'salmon'),
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
                    ax.text(idx, v + 0.5, str(int(v)), ha='center', fontsize=9)

                ax.set_title(reshape_text(f"Grouped by Educational Level — {i_key.capitalize()} by {j_key.capitalize()}"), fontsize=12, pad=12)
                ax.set_xlabel(reshape_text('Educational Level'), fontsize=10)
                ax.set_ylabel(reshape_text('Count'), fontsize=10)
                ax.set_xticks(list(x))
                ax.set_xticklabels([reshape_text(lbl) for lbl in df_plot['field']], rotation=45, ha='right')
                ax.grid(True, axis='y', linestyle='--', alpha=0.7)

            plt.tight_layout()
            plt.savefig(self.plot_path / f'top_place_grouped_by_{by}.png', dpi=300, bbox_inches='tight')
            plt.show()