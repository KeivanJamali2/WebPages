from pathlib import Path
import pandas as pd
import jdatetime
import time
from typing import List, Dict, Tuple
import re


def strip_excel_formula(value):
    """
    Strip Excel formula format from a value.
    Converts '=\"00123\"' back to '00123'.
    """
    if value is None:
        return None
    value_str = str(value)
    # Match pattern like ="..." and extract the inner value
    match = re.match(r'^="(.+)"$', value_str)
    if match:
        return match.group(1)
    return value_str


class RawDataReader:
    def __init__(self, raw_data_dir: Path):
        self.raw_data_dir = raw_data_dir

    def read_data(self, filename: str) -> pd.DataFrame:
        file_path = self.raw_data_dir / filename
        with open(file_path, 'r', encoding='utf-8') as file:
            data = file.readlines()
            return data
        
class DataLoader:
    def __init__(self, data: RawDataReader):
        self.data = data
        
    def fit(self, filename_number: str) -> None:
        self.filename_number = filename_number
        self.i, self.j = filename_number.split('_')
        self.data_message: list[str] = self.data.read_data("file_" + filename_number + '.txt')
        
        # Try to load workflow, but allow it to be None if it doesn't exist
        try:
            self.data_workflow: list[str] = self.data.read_data("workflow_" + filename_number + ".txt")
        except FileNotFoundError:
            self.data_workflow = None
        
    def extract_subject(self) -> str:
        for line in self.data_message:
            if "Subject" in line:
                subject = line.split("Subject : ")[1].strip()
                return subject
        else:
            raise ValueError("Subject not found in the message data.")
    
    def extract_refrence_code(self) -> str:
        for line in self.data_message:
            if "Code" in line:
                code = line.split("Code: ")[1].strip()
                return code
            
    def extract_major(self) -> str:
        for line in self.data_message:
            if "Major" in line:
                major = line.split("Major: ")[1].strip()
                return major
            
    def extract_student_info(self) -> dict:
        student_section = False
        student_info = {"name": "<empty>", "national_id": "<empty>", "field": "<empty>", "student_id": "<empty>"}
        for line in self.data_message:
            if "اطلاعات دانشجو" in line:
                student_section = True
                continue
            if student_section:
                if "نام و نام خانوادگی:" in line:
                    student_info["name"] = line.split("نام و نام خانوادگی:")[1].strip()
                elif "کد ملی:" in line:
                    student_info["national_id"] = line.split("کد ملی:")[1].strip()
                elif "شماره دانشجویی:" in line:
                    student_info["student_id"] = line.split("شماره دانشجویی:")[1].strip()
                elif "رشته محل:" in line:
                    student_info["field"] = line.split("رشته محل:")[1].strip()
                    break
        return student_info
            
    def extract_messages(self) -> dict:
        messages = {}
        current_date = None
        current_message = []
        
        for line in self.data_message:
            if "ارسال شده:" in line:
                if current_date and current_message:
                    ms = "".join(current_message).strip()
                    messages[current_date] = ms if ms else "<empty>"
                date_str = line.split("ارسال شده: ")[1].strip().strip("'")
                date_part = date_str.split("،")[1].strip()
                current_date = jdatetime.datetime.strptime(date_part, "%d %B %Y %H:%M:%S")
                current_message = []
            elif current_date is not None and "-" * 8 in line:
                if current_date and current_message:
                    ms = "".join(current_message).strip()
                    messages[current_date] = ms if ms else "<empty>"
                current_date = None
                current_message = []
            elif current_date is not None:
                current_message.append(line)
        if current_date and current_message:
            ms = "".join(current_message).strip()
            messages[current_date] = ms if ms else "<empty>"
            
        return messages
    
    def extract_external_message(self) -> str:
        message = []
        
        for line in reversed(self.data_message):
            if "رشته محل:" in line:
                break
            if line.strip():
                message.insert(0, line)
        msg = "".join(message)
        msg = msg.replace("-", "").strip()
        return msg if message else None
    
    def extract_workflow(self) -> dict:
        # If no workflow file exists, return empty workflow
        if self.data_workflow is None:
            return {}
        
        workflow = {}
        prev_name = self.extract_student_info()["name"]
        
        current_date = None
        current_name = None 
        current_email = None
        date_counters = {}
        
        for line in self.data_workflow:
            if "date: " in line:
                date_str = line.split("date: ")[1].strip("'")
                date_part = date_str.split("،")[1].strip()
                base_date = jdatetime.datetime.strptime(date_part, "%d %B %Y %H:%M")
                
                # Add counter for repeated dates
                if base_date in date_counters:
                    date_counters[base_date] += 1
                else:
                    date_counters[base_date] = 0
                    
                # Add hours to differentiate same-day entries
                current_date = base_date.replace(second=date_counters[base_date])
                
            elif "name:" in line:
                current_name = line.split("name: ")[1].strip()
            elif "email:" in line:
                current_email = line.split("email: ")[1].strip()
            elif "parent_id:" in line:
                parent_id = line.split("parent_id: ")[1].strip()
                if parent_id == "None":
                    parent_id = "<empty>"
            elif "id:" in line:
                current_id = line.split("id: ")[1].strip()
            elif "-" * 8 in line and current_date:
                for date, entry in workflow.items():
                    if entry["id"] == parent_id:
                        prev_name = entry["to"]
                        break
                workflow[current_date] = {
                    "from": prev_name,
                    "to": current_name,
                    "to_email": current_email,
                    "id": current_id,
                    "parent_id": parent_id
                }
                current_date = None
                
        return workflow
        
class CombineData:
    def fit(self, loader: DataLoader) -> None:
        self.loader = loader
        self.subject = self.loader.extract_subject()
        self.reference_code = self.loader.extract_refrence_code()
        self.major = self.loader.extract_major()
        self.student_info = self.loader.extract_student_info()
        self.messages = self.loader.extract_messages()
        self.external_message = self.loader.extract_external_message()
        self.workflow = self.loader.extract_workflow()
        self.compressed_data = self._combine_text_flow()
        
    def _combine_text_flow(self):
        combined_data = []
        
        # Helper function to create normalized date keys for matching
        def create_date_keys(date):
            """Creates multiple date keys to handle 12-hour format differences"""
            base_key = (date.year, date.month, date.day, date.minute)
            return [
                (base_key, date.hour),
                (base_key, (date.hour + 12) % 24),
                (base_key, (date.hour - 12) % 24)
            ]
        
        # Build lookup dictionary for messages with all possible hour variations
        message_lookup = {}
        for date_m, message in self.messages.items():
            for key in create_date_keys(date_m):
                if key not in message_lookup:
                    message_lookup[key] = (date_m, message)
        
        # Track which message dates have been matched
        matched_message_dates = set()
        
        # Process workflow dates and match with messages
        for date_w in sorted(self.workflow.keys()):
            found = False
            # Try to find matching message using lookup
            for key in create_date_keys(date_w):
                if key in message_lookup:
                    date_m, message = message_lookup[key]
                    row = {
                        'date': date_w,
                        'message': message,
                        'from': self.workflow[date_w]['from'],
                        'to': self.workflow[date_w]['to'],
                        'to_email': self.workflow[date_w]['to_email'],
                        "from_id": self.workflow[date_w]['parent_id'],
                        "to_id": self.workflow[date_w]['id'],
                        "matched": True
                    }
                    combined_data.append(row)
                    matched_message_dates.add(date_m)
                    found = True
                    break
            
            if not found:
                row = {
                    'date': date_w,
                    'message': "There is nothing about this message in the Emails.",
                    'from': self.workflow[date_w]['from'],
                    'to': self.workflow[date_w]['to'],
                    'to_email': self.workflow[date_w]['to_email'],
                    "from_id": self.workflow[date_w]['parent_id'],
                    "to_id": self.workflow[date_w]['id'],
                    "matched": False
                }
                combined_data.append(row)
        
        # Add unmatched messages
        for date_m in sorted(self.messages.keys()):
            if date_m not in matched_message_dates:
                row = {
                    'date': date_m,
                    'message': self.messages[date_m],
                    'from': "Not in workflow",
                    'to': "Not in workflow",
                    'to_email': "Not in workflow",
                    "from_id": "Not in workflow",
                    "to_id": "Not in workflow",
                    "matched": False
                }
                combined_data.append(row)
        
        # Add external message if exists
        if self.external_message:
            row = {
                'date': jdatetime.datetime(1500, 1, 1, 0, 0, 0),
                'message': self.external_message,
                'from': "Not in workflow",
                'to': "Not in workflow",
                'to_email': "Not in workflow",
                "from_id": "Not in workflow",
                "to_id": "Not in workflow",
                "matched": False
            }
            combined_data.append(row)

        return pd.DataFrame(combined_data).sort_values(by='date').reset_index(drop=True)
    
    def save_combined_data(self, file_name: Path):
        self.compressed_data.to_csv(file_name, index=False, encoding="utf-8-sig")
    
    def save_hami_data(self, file_name: Path):
        row = {
            'number': self.loader.j,
            'subject': self.subject,
            'reference_code': f'="{self.reference_code}"' if self.reference_code else '',
            'major': self.major,
            'name': self.student_info['name'],
            'national_id': f'="{self.student_info["national_id"]}"' if self.student_info['national_id'] != '<empty>' else '<empty>',
            'student_id': f'="{self.student_info["student_id"]}"' if self.student_info['student_id'] != '<empty>' else '<empty>',
            'field': self.student_info['field']
        }
        if file_name.exists():
            df = pd.read_csv(file_name, dtype={'reference_code': str, 'national_id': str, 'student_id': str})
            df.loc[len(df)] = row
        else:
            df = pd.DataFrame([row])
        df.to_csv(file_name, index=False, encoding="utf-8-sig")


class StoreData:
    def __init__(self, base_output_path: Path, base_input_path: Path, date_source: str = "first"):
        self.base_output_path = base_output_path
        self.base_input_path = base_input_path
        self.date_source = date_source
        
        if self.date_source not in ["first", "last"]:
            raise ValueError("date_source must be either 'first' or 'last'")
        
    def fit(self, i_values: list[int]):
        raw_data = RawDataReader(raw_data_dir=self.base_input_path)
        loader = DataLoader(data=raw_data)
        express = CombineData()
        
        total_processed = 0
        total_skipped = 0
        
        for i in i_values:
            j = 1
            consecutive_missing = 0
            max_consecutive_missing = 5  # Stop after 5 consecutive missing files
            
            while consecutive_missing < max_consecutive_missing:
                try:
                    loader.fit(filename_number=f"{i}_{j}")
                    express.fit(loader=loader)  
                    self.save_combined_data(express.compressed_data, i, j)
                    self.save_hami_data(
                        express.compressed_data, 
                        i, 
                        j,
                        express.subject,
                        express.reference_code,
                        express.major,
                        express.student_info
                    )
                    total_processed += 1
                    consecutive_missing = 0  # Reset counter on success
                    j += 1
                except FileNotFoundError as e:
                    # Check if it's specifically the file_*.txt that's missing
                    if f"file_{i}_{j}.txt" in str(e):
                        # file_*.txt is missing, skip this entry
                        if j == 1:
                            break
                        else:
                            consecutive_missing += 1
                            total_skipped += 1
                            j += 1
                    # If only workflow_*.txt is missing, the fit() method will handle it
                    # and processing will continue (this shouldn't raise FileNotFoundError anymore)
                    else:
                        # Some other file is missing
                        if j == 1:
                            break
                        else:
                            consecutive_missing += 1
                            total_skipped += 1
                            j += 1
                except Exception as e:
                    # Log other errors but continue
                    print(f"Error processing {i}_{j}: {str(e)}")
                    consecutive_missing += 1
                    total_skipped += 1
                    j += 1
        
        print(f"\nProcessing complete:")
        print(f"  - Successfully processed: {total_processed} files")
        print(f"  - Skipped (missing/errors): {total_skipped} files")
        print(f"  - Total attempted: {total_processed + total_skipped} files")
    
    def _get_reference_date(self, combined_data: pd.DataFrame) -> jdatetime.datetime:
        # Filter out dummy dates (year 1500)
        valid_dates = combined_data[combined_data['date'].apply(lambda x: x.year != 1500)]['date']
        
        if len(valid_dates) == 0:
            raise ValueError("No valid dates found in combined data (all dates are dummy dates)")
        
        if self.date_source == "first":
            return valid_dates.iloc[0]
        else:  # "last"
            return valid_dates.iloc[-1]
    
    def _get_year_month_folder(self, date: jdatetime.datetime) -> str:
        return f"{date.year:04d}-{date.month:02d}"
    
    def save_combined_data(self, combined_data: pd.DataFrame, i: int, j: int) -> Path:
        reference_date = self._get_reference_date(combined_data)
        year_month_folder = self._get_year_month_folder(reference_date)
        
        # Create the full path: base_output_path/year-month/combined_output/
        output_dir = self.base_output_path / self.date_source / year_month_folder / "combined_output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the file
        file_path = output_dir / f"combined_{i}_{j}.csv"
        combined_data.to_csv(file_path, index=False, encoding="utf-8-sig")
        
        return file_path
    
    def save_hami_data(self, combined_data: pd.DataFrame, i: int, j: int, 
                      subject: str, reference_code: str, major: str, student_info: dict) -> Path:
        reference_date = self._get_reference_date(combined_data)
        year_month_folder = self._get_year_month_folder(reference_date)
        
        # Create the full path: base_output_path/year-month/hami_output/
        output_dir = self.base_output_path/ self.date_source / year_month_folder / "hami_output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create the row with Excel-safe formatting for numeric-looking strings
        row = {
            'number': j,
            'subject': subject,
            'reference_code': f'="{reference_code}"' if reference_code else '',
            'major': major,
            'name': student_info['name'],
            'national_id': f'="{student_info["national_id"]}"' if student_info['national_id'] != '<empty>' else '<empty>',
            'student_id': f'="{student_info["student_id"]}"' if student_info['student_id'] != '<empty>' else '<empty>',
            'field': student_info['field']
        }
        
        # File path for this specific i value
        file_path = output_dir / f"hami_{i}.csv"
        
        # Append or create the file
        if file_path.exists():
            df = pd.read_csv(file_path, dtype={'reference_code': str, 'national_id': str, 'student_id': str})
            df.loc[len(df)] = row
        else:
            df = pd.DataFrame([row])
        
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        
        return file_path
    
    def sort_files_by_date(self, date_source, specific_year_month: str = None, order: str = "ascending"):
        """
        Sort and rename files in each year-month folder based on their reference dates.
        Files will be renamed with sequential j numbers (1, 2, 3, ...) in chronological order.
        
        Args:
            specific_year_month: Optional specific year-month folder to process (e.g., "1404-05").
                                If None, processes all year-month folders.
            order: Sort order - either "ascending" or "descending". Defaults to "ascending".
        """
        if order not in ["ascending", "descending"]:
            raise ValueError("order must be either 'ascending' or 'descending'")
        base_path = self.base_output_path / date_source
        
        # Determine which year-month folders to process
        if specific_year_month:
            year_month_folders = [base_path / specific_year_month]
        else:
            # Get all year-month folders
            year_month_folders = [f for f in base_path.iterdir() if f.is_dir()]
        
        for year_month_folder in year_month_folders:
            if not year_month_folder.exists():
                print(f"Folder {year_month_folder} does not exist, skipping...")
                continue
                
            combined_dir = year_month_folder / "combined_output"
            hami_dir = year_month_folder / "hami_output"
            
            if not combined_dir.exists():
                print(f"No combined_output folder in {year_month_folder.name}, skipping...")
                continue
            
            # Get all combined files and extract their dates
            file_info = []
            
            for combined_file in combined_dir.glob("combined_*.csv"):
                try:
                    # Read the combined data to get reference date
                    df = pd.read_csv(combined_file)
                    
                    # Convert date column to datetime objects if they're strings
                    if df['date'].dtype == 'object':
                        df['date'] = df['date'].apply(lambda x: jdatetime.datetime.fromisoformat(x) if isinstance(x, str) else x)
                    
                    # Get reference date
                    valid_dates = df[df['date'].apply(lambda x: x.year != 1500)]['date']
                    
                    if len(valid_dates) == 0:
                        print(f"Warning: No valid dates in {combined_file.name}, skipping...")
                        continue
                    
                    if self.date_source == "first":
                        ref_date = valid_dates.iloc[0]
                    else:
                        ref_date = valid_dates.iloc[-1]
                    
                    # Extract i and j from filename: combined_i_j.csv
                    parts = combined_file.stem.split('_')
                    i_value = int(parts[1])
                    j_value = int(parts[2])
                    
                    file_info.append({
                        'combined_file': combined_file,
                        'i': i_value,
                        'j': j_value,
                        'ref_date': ref_date,
                        'data': df
                    })
                    
                except Exception as e:
                    print(f"Error processing {combined_file.name}: {str(e)}")
                    continue
            
            if not file_info:
                print(f"No valid files to sort in {year_month_folder.name}")
                continue
            
            # Group by i value
            from collections import defaultdict
            grouped_files = defaultdict(list)
            for info in file_info:
                grouped_files[info['i']].append(info)
            
            # Process each i group
            for i_value, files in grouped_files.items():
                # Sort files by reference date
                files.sort(key=lambda x: x['ref_date'], reverse=(order == "descending"))
                
                # Create temporary directory for renaming
                temp_dir = year_month_folder / "temp_rename"
                temp_dir.mkdir(exist_ok=True)
                
                # Build mapping of old_j to new_j for hami file updates
                j_mapping = {}
                
                # First, save all combined files to temp directory with new names
                for new_j, file_info_item in enumerate(files, start=1):
                    old_combined_file = file_info_item['combined_file']
                    old_j = file_info_item['j']
                    
                    # Track the mapping
                    j_mapping[old_j] = new_j
                    
                    # New filenames
                    new_combined_name = f"combined_{i_value}_{new_j}.csv"
                    temp_combined_file = temp_dir / new_combined_name
                    
                    # Copy combined file to temp with new name
                    file_info_item['data'].to_csv(temp_combined_file, index=False, encoding="utf-8-sig")
                
                # Update hami file entries (but don't rename the hami file itself)
                hami_file = hami_dir / f"hami_{i_value}.csv"
                if hami_file.exists():
                    # Read hami file
                    hami_df = pd.read_csv(hami_file, dtype={'reference_code': str, 'national_id': str, 'student_id': str})
                    
                    # Update all numbers according to the mapping
                    for old_j, new_j in j_mapping.items():
                        mask = hami_df['number'] == old_j
                        if mask.any():
                            hami_df.loc[mask, 'number'] = new_j
                    
                    # Save updated hami file back to its original location
                    hami_df.to_csv(hami_file, index=False, encoding="utf-8-sig")
                
                # Delete original combined files for this i value
                for file_info_item in files:
                    file_info_item['combined_file'].unlink()
                
                # Move renamed combined files from temp to actual directory
                for temp_file in temp_dir.glob("combined_*.csv"):
                    dest_file = combined_dir / temp_file.name
                    temp_file.rename(dest_file)
                
                # Clean up temp directory
                if temp_dir.exists():
                    temp_dir.rmdir()
                
                print(f"Sorted and renamed {len(files)} files for i={i_value} in {year_month_folder.name}")
            
            print(f"Finished processing {year_month_folder.name}")


class DuplicateDetector:
    """
    Detects and manages duplicate records based on reference_code across the database.
    """
    
    def __init__(self, base_path: Path, date_source: str = "first"):
        self.base_path = base_path
        self.date_source = date_source
        if self.date_source not in ["first", "last"]:
            raise ValueError("date_source must be either 'first' or 'last'")
    
    def find_duplicates_by_reference(self) -> Dict[str, List[Dict]]:
        """
        Find all duplicate records grouped by reference_code.
        A duplicate is when the SAME reference_code appears in DIFFERENT records (different hami_id/number/month combinations).
        
        Returns:
            Dictionary with reference_code as key and list of file info as value.
            Each file info contains: reference_code, hami_id, number, month, date_source
        """
        all_records = {}  # reference_code -> list of records
        date_source_path = self.base_path / self.date_source
        
        if not date_source_path.exists():
            # Database path does not exist
            return {}
        
        # Iterate through all year-month folders and collect all records
        total_records_scanned = 0
        for month_folder in sorted(date_source_path.iterdir()):
            if not month_folder.is_dir():
                continue
            
            hami_dir = month_folder / "hami_output"
            if not hami_dir.exists():
                continue
            
            # Read all hami files in this month
            for hami_file in sorted(hami_dir.glob("hami_*.csv")):
                try:
                    df = pd.read_csv(hami_file, dtype={'reference_code': str, 'national_id': str, 'student_id': str})
                    
                    # Check if reference_code column exists
                    if 'reference_code' not in df.columns:
                        continue
                    
                    hami_id = hami_file.stem.replace("hami_", "")
                    for idx, row in df.iterrows():
                        # Strip Excel formula format if present
                        ref_code = strip_excel_formula(row['reference_code'])
                        
                        # Skip empty or NaN reference codes
                        if not ref_code or ref_code.lower() == 'nan' or ref_code.strip() == '':
                            continue
                        
                        total_records_scanned += 1
                        
                        if ref_code not in all_records:
                            all_records[ref_code] = []
                        
                        record_info = {
                            'reference_code': ref_code,
                            'hami_id': str(hami_id),
                            'number': int(row['number']),
                            'month': month_folder.name,
                            'date_source': self.date_source,
                            'row_index': int(idx),  # Track the row index in CSV
                            'subject': str(row.get('subject', '')),
                            'name': str(row.get('name', '')),
                            'major': str(row.get('major', '')),
                            'student_id': strip_excel_formula(row.get('student_id', '')),
                            'national_id': strip_excel_formula(row.get('national_id', ''))
                        }
                        
                        all_records[ref_code].append(record_info)
                        
                except Exception as e:
                    # Skip files that can't be processed
                    continue
        
        # Find duplicates: reference_codes that appear in MULTIPLE locations OR multiple times in same file
        # A true duplicate is when the SAME reference_code appears more than once
        duplicates = {}
        for ref_code, records in all_records.items():
            if len(records) > 1:
                # Check if these are in different locations or same location
                unique_locations = set((r['hami_id'], r['month']) for r in records)
                
                # Any reference_code appearing more than once is a duplicate
                # (either from different months/hami_ids OR from same file with duplicate rows)
                duplicates[ref_code] = records
                # Removed print statements that cause BlockingIOError in WSGI environment
        
        return duplicates
    
    def get_duplicate_summary(self) -> Dict:
        """
        Get a summary of duplicates with count and details.
        
        Returns:
            Dictionary with total_duplicates count and grouped_duplicates list
        """
        duplicates = self.find_duplicates_by_reference()
        
        grouped = []
        for ref_code, records in duplicates.items():
            grouped.append({
                'reference_code': ref_code,
                'count': len(records),
                'records': records
            })
        
        return {
            'total_duplicate_groups': len(grouped),
            'total_duplicates': sum(len(rec['records']) for rec in grouped),
            'grouped_duplicates': grouped
        }
    
    def _remove_duplicate_rows_from_same_file(self, hami_id: str, month: str, reference_code: str, 
                                               number: int, keep_count: int = 1) -> bool:
        """
        Remove duplicate rows from a hami file, keeping only a specified number of copies.
        This is for identical duplicates (same reference_code) in the same file.
        
        Args:
            hami_id: The Hami ID
            month: The year-month folder
            reference_code: The reference code to deduplicate
            number: The record number (for combined file deletion)
            keep_count: How many copies to keep (default 1)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            hami_id = str(hami_id)
            hami_file = self.base_path / self.date_source / month / "hami_output" / f"hami_{hami_id}.csv"
            combined_file = self.base_path / self.date_source / month / "combined_output" / f"combined_{hami_id}_{number}.csv"
            
            # Remove combined file once
            if combined_file.exists():
                combined_file.unlink()
                print(f"    ✓ Deleted combined file")
            
            # Remove duplicate rows from hami file
            if hami_file.exists():
                df = pd.read_csv(hami_file, dtype={'reference_code': str, 'national_id': str, 'student_id': str})
                initial_count = len(df)
                
                # Find all rows with this reference_code (strip Excel formula format for comparison)
                matching_mask = df['reference_code'].apply(strip_excel_formula) == strip_excel_formula(reference_code)
                matching_count = matching_mask.sum()
                
                if matching_count <= keep_count:
                    print(f"    ⚠️  Only {matching_count} rows found, nothing to remove")
                    return True
                
                # Get indices of matching rows
                matching_indices = df[matching_mask].index.tolist()
                
                # Remove all but the last 'keep_count' rows (for keep_newer)
                # or all but the first 'keep_count' rows (for keep_older)
                # Since sorting was done externally, we just keep the last occurrence
                indices_to_remove = matching_indices[:-keep_count] if keep_count > 0 else matching_indices
                
                # Remove rows
                df = df.drop(index=indices_to_remove).reset_index(drop=True)
                
                final_count = len(df)
                removed_count = initial_count - final_count
                
                if removed_count > 0:
                    df.to_csv(hami_file, index=False, encoding="utf-8-sig")
                    print(f"    ✓ Updated hami file ({initial_count} → {final_count} records, removed {removed_count})")
                    return True
                else:
                    print(f"    ✗ No records removed from hami file")
                    return False
            else:
                print(f"    ✗ Hami file does not exist")
                return False
        except Exception as e:
            print(f"    ✗ Error in duplicate removal: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def remove_record(self, hami_id: str, number: int, month: str, row_index: int = None) -> bool:
        """
        Remove a specific record from the database.
        
        Args:
            hami_id: The Hami ID
            number: The record number
            month: The year-month folder (e.g., "1404-05")
            row_index: Optional row index to remove specific duplicate row (if None, removes ALL with this number)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            hami_id = str(hami_id)
            number = int(number)
            
            hami_file = self.base_path / self.date_source / month / "hami_output" / f"hami_{hami_id}.csv"
            combined_file = self.base_path / self.date_source / month / "combined_output" / f"combined_{hami_id}_{number}.csv"
            
            print(f"\n  → Removing: hami_id={hami_id}, number={number}, month={month}" + (f", row_index={row_index}" if row_index is not None else ""))
            print(f"    Combined file path: {combined_file}")
            print(f"    Combined file exists: {combined_file.exists()}")
            
            # Remove combined file FIRST (this is the actual request data)
            # Note: If multiple duplicate rows exist in hami, the first removal deletes this file,
            # subsequent removals will just skip it with a warning
            if combined_file.exists():
                combined_file.unlink()
                print(f"    ✓ Successfully deleted combined file")
            else:
                print(f"    ⚠️  Combined file does not exist (may have been deleted already)")
            
            # Remove from hami file (this is the metadata)
            if hami_file.exists():
                df = pd.read_csv(hami_file, dtype={'reference_code': str, 'national_id': str, 'student_id': str})
                initial_count = len(df)
                
                # Make sure we're comparing the same types
                df['number'] = df['number'].astype(int)
                
                if row_index is not None:
                    # Remove ONE occurrence of matching record by number
                    # We can't use row_index directly as it becomes invalid after first deletion
                    # Instead, remove the first occurrence with this number
                    matching_indices = df[df['number'] == number].index
                    if len(matching_indices) > 0:
                        # Remove only the first matching row
                        df = df.drop(index=matching_indices[0]).reset_index(drop=True)
                else:
                    # Remove ALL records with this number
                    df = df[df['number'] != number]
                
                final_count = len(df)
                
                if final_count < initial_count:
                    df.to_csv(hami_file, index=False, encoding="utf-8-sig")
                    print(f"    ✓ Updated hami file ({initial_count} → {final_count} records)")
                    return True
                else:
                    print(f"    ✗ No records removed from hami file")
                    return False
            else:
                print(f"    ✗ Hami file does not exist")
                return False
        except Exception as e:
            print(f"    ✗ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def keep_older(self, duplicates: Dict[str, List[Dict]]) -> Dict:
        """
        For each duplicate group, keep only the oldest record (by month and then by number).
        Always keeps at least one record per duplicate group.
        When records are identical (same hami_id, number, month), uses row_index to distinguish them.
        
        Returns:
            Dictionary with removed records info
        """
        removed = []
        kept = []
        
        for ref_code, records in duplicates.items():
            if len(records) <= 1:
                # Only one record, nothing to do
                continue
            
            # Sort by month (ascending) then by number (ascending) then by row_index
            # This ensures deterministic ordering: oldest month, then lowest number, then oldest row
            sorted_records = sorted(
                records, 
                key=lambda x: (
                    x['month'], 
                    x['number'], 
                    x['hami_id'],
                    x.get('row_index', 0)
                )
            )
            
            # Always keep the first (oldest) record
            record_to_keep = sorted_records[0]
            kept.append(record_to_keep)
            print(f"\n=== Processing Duplicate Group: {ref_code} ===")
            print(f"Total records: {len(sorted_records)}")
            print(f"KEEPING: {record_to_keep['hami_id']}_{record_to_keep['number']} (Month: {record_to_keep['month']}, Row: {record_to_keep.get('row_index', 'N/A')})")
            
            # Check if all records are in the same file (same hami_id and month)
            all_same_file = all(
                r['hami_id'] == record_to_keep['hami_id'] and r['month'] == record_to_keep['month'] 
                for r in sorted_records
            )
            
            if all_same_file:
                # All duplicates are in the same file - keep first occurrence, remove rest
                # We need to manually handle this to keep the FIRST one (oldest)
                print(f"REMOVING {len(sorted_records) - 1} duplicate(s) from {record_to_keep['hami_id']} in {record_to_keep['month']} (keeping oldest)")
                
                # For keep_older, we want to keep the FIRST occurrence
                # So we remove all matching rows except the first one
                hami_id = str(record_to_keep['hami_id'])
                hami_file = self.base_path / self.date_source / record_to_keep['month'] / "hami_output" / f"hami_{hami_id}.csv"
                combined_file = self.base_path / self.date_source / record_to_keep['month'] / "combined_output" / f"combined_{hami_id}_{record_to_keep['number']}.csv"
                
                try:
                    # Remove combined file
                    if combined_file.exists():
                        combined_file.unlink()
                        print(f"    ✓ Deleted combined file")
                    
                    # Remove duplicate rows, keeping only the first
                    if hami_file.exists():
                        df = pd.read_csv(hami_file, dtype={'reference_code': str, 'national_id': str, 'student_id': str})
                        initial_count = len(df)
                        
                        # Find all rows with this reference_code (strip Excel formula format for comparison)
                        matching_mask = df['reference_code'].apply(strip_excel_formula) == strip_excel_formula(ref_code)
                        matching_indices = df[matching_mask].index.tolist()
                        
                        # Keep only the first occurrence, remove the rest
                        if len(matching_indices) > 1:
                            indices_to_remove = matching_indices[1:]  # Remove all except first
                            df = df.drop(index=indices_to_remove).reset_index(drop=True)
                            
                            final_count = len(df)
                            df.to_csv(hami_file, index=False, encoding="utf-8-sig")
                            print(f"    ✓ Updated hami file ({initial_count} → {final_count} records)")
                            removed.extend(sorted_records[1:])
                        else:
                            print(f"    ⚠️  Only {len(matching_indices)} row found, nothing to remove")
                    else:
                        print(f"    ✗ Hami file does not exist")
                except Exception as e:
                    print(f"    ✗ Error: {str(e)}")
            else:
                # Duplicates are in different files - remove file by file
                for idx, record_to_remove in enumerate(sorted_records[1:], 1):
                    print(f"REMOVING #{idx}: {record_to_remove['hami_id']}_{record_to_remove['number']} (Month: {record_to_remove['month']})")
                    if self.remove_record(
                        record_to_remove['hami_id'],
                        record_to_remove['number'],
                        record_to_remove['month'],
                        row_index=None  # Remove all with this number
                    ):
                        removed.append(record_to_remove)
                    else:
                        print(f"FAILED to remove: {record_to_remove['hami_id']}_{record_to_remove['number']}")
        
        print(f"\n=== SUMMARY ===")
        print(f"Total duplicate groups processed: {len([r for r in duplicates.values() if len(r) > 1])}")
        print(f"Records kept: {len(kept)}")
        print(f"Records removed: {len(removed)}")
        
        return {
            'action': 'keep_older',
            'removed_count': len(removed),
            'removed_records': removed,
            'kept_records': kept
        }
    
    def keep_newer(self, duplicates: Dict[str, List[Dict]]) -> Dict:
        """
        For each duplicate group, keep only the newest record (by month and then by number).
        Always keeps at least one record per duplicate group.
        When records are identical (same hami_id, number, month), uses row_index to distinguish them.
        
        Returns:
            Dictionary with removed records info
        """
        removed = []
        kept = []
        
        for ref_code, records in duplicates.items():
            if len(records) <= 1:
                # Only one record, nothing to do
                continue
            
            # Sort by month (ascending) then by number (ascending) then by row_index
            # This ensures deterministic ordering: newest month, then highest number, then newest row
            sorted_records = sorted(
                records, 
                key=lambda x: (
                    x['month'], 
                    x['number'], 
                    x['hami_id'],
                    x.get('row_index', 0)
                )
            )
            
            # Always keep the last (newest) record
            record_to_keep = sorted_records[-1]
            kept.append(record_to_keep)
            print(f"\n=== Processing Duplicate Group: {ref_code} ===")
            print(f"Total records: {len(sorted_records)}")
            print(f"KEEPING: {record_to_keep['hami_id']}_{record_to_keep['number']} (Month: {record_to_keep['month']}, Row: {record_to_keep.get('row_index', 'N/A')})")
            
            # Check if all records are in the same file (same hami_id and month)
            all_same_file = all(
                r['hami_id'] == record_to_keep['hami_id'] and r['month'] == record_to_keep['month'] 
                for r in sorted_records
            )
            
            if all_same_file:
                # All duplicates are in the same file - use reference_code-based removal
                # This avoids row_index issues after DataFrame modifications
                print(f"REMOVING {len(sorted_records) - 1} duplicate(s) from {record_to_keep['hami_id']} in {record_to_keep['month']}")
                success = self._remove_duplicate_rows_from_same_file(
                    record_to_keep['hami_id'],
                    record_to_keep['month'],
                    ref_code,
                    record_to_keep['number'],
                    keep_count=1  # Keep only 1 copy (the newest/last one)
                )
                if success:
                    removed.extend(sorted_records[:-1])
                else:
                    print(f"FAILED to remove duplicates from {record_to_keep['hami_id']}")
            else:
                # Duplicates are in different files - remove file by file
                for idx, record_to_remove in enumerate(sorted_records[:-1], 1):
                    print(f"REMOVING #{idx}: {record_to_remove['hami_id']}_{record_to_remove['number']} (Month: {record_to_remove['month']})")
                    if self.remove_record(
                        record_to_remove['hami_id'],
                        record_to_remove['number'],
                        record_to_remove['month'],
                        row_index=None  # Remove all with this number
                    ):
                        removed.append(record_to_remove)
                    else:
                        print(f"FAILED to remove: {record_to_remove['hami_id']}_{record_to_remove['number']}")
        
        print(f"\n=== SUMMARY ===")
        print(f"Total duplicate groups processed: {len([r for r in duplicates.values() if len(r) > 1])}")
        print(f"Records kept: {len(kept)}")
        print(f"Records removed: {len(removed)}")
        
        return {
            'action': 'keep_newer',
            'removed_count': len(removed),
            'removed_records': removed,
            'kept_records': kept
        }
    
    def handle_manual_removal(self, records_to_remove: List[Dict]) -> Dict:
        """
        Remove specified records from the database.
        
        Args:
            records_to_remove: List of records to remove with hami_id, number, and month
        
        Returns:
            Dictionary with removed records info
        """
        removed = []
        
        for record in records_to_remove:
            if self.remove_record(
                record['hami_id'],
                record['number'],
                record['month']
            ):
                removed.append(record)
        
        return {
            'action': 'manual_removal',
            'removed_count': len(removed),
            'removed_records': removed
        }

