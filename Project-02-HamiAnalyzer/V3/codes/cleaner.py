from pathlib import Path
import pandas as pd
import jdatetime
import time

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
        self.data_workflow: list[str] = self.data.read_data("workflow_" + filename_number + ".txt")
        
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
            'reference_code': self.reference_code,
            'major': self.major,
            'name': self.student_info['name'],
            'national_id': str(self.student_info['national_id']),
            'student_id': str(self.student_info['student_id']),
            'field': self.student_info['field']
        }
        if file_name.exists():
            df = pd.read_csv(file_name)
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
        
        for i in i_values:
            j = 1
            while True:
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
                    j += 1
                except FileNotFoundError:
                    break
    
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
        
        # Create the row
        row = {
            'number': j,
            'subject': subject,
            'reference_code': reference_code,
            'major': major,
            'name': student_info['name'],
            'national_id': str(student_info['national_id']),
            'student_id': str(student_info['student_id']),
            'field': student_info['field']
        }
        
        # File path for this specific i value
        file_path = output_dir / f"hami_{i}.csv"
        
        # Append or create the file
        if file_path.exists():
            df = pd.read_csv(file_path)
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
                    hami_df = pd.read_csv(hami_file)
                    
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

