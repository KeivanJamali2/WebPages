from pathlib import Path
from datetime import datetime
import pandas as pd
import jdatetime
import time
from typing import List, Dict, Tuple, Optional
import re
import logging

from database import HamiDatabase, get_database

logger = logging.getLogger(__name__)


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


# Latin and Persian/Arabic-Indic digits, since entry years appear in both forms.
_PLACE_YEAR_PATTERN = re.compile(r'^[\d\u06f0-\u06f9\u0660-\u0669]{2,4}$')

# Placeholder hami for excel-only rows, which don't say who handled the ticket.
UNKNOWN_HAMI_ID = 'unknown'


def extract_city_from_place(place, known_cities: List[str] = None) -> Optional[str]:
    """
    Infer the city from a "place" string.

    Both data sources carry the same identifier: the scraper's 'رشته محل' field
    and the excel export's 'خوشه' column, formatted as
    '<educational level>_<field>_<city>_<entry year>'. The field name itself may
    contain underscores, so the city is located relative to the trailing year
    rather than by a fixed index.

    Some scraped rows are free text typed by the student and don't follow the
    format at all; for those, fall back to looking for a city name we have
    already seen in well-formed rows.

    Returns None when no city can be determined.
    """
    if place is None or (isinstance(place, float) and pd.isna(place)):
        return None
    text = str(place).strip()
    if not text or text == '<empty>':
        return None

    parts = [part.strip() for part in text.split('_')]
    if len(parts) >= 3 and _PLACE_YEAR_PATTERN.match(parts[-1]) and parts[-2]:
        return parts[-2]

    # Longest first, so 'واحد یزد - ...' wins over the plain 'یزد' inside it.
    for city in sorted(known_cities or [], key=len, reverse=True):
        if city and city in text:
            return city
    return None


class RawDataReader:
    def __init__(self, raw_data_dir: Path):
        self.raw_data_dir = raw_data_dir
        self._file_cache = {}  # Cache file locations
        self._build_file_cache()
    
    def _build_file_cache(self):
        """Build a cache of file locations (handles nested folders from zip extraction)"""
        for file_path in self.raw_data_dir.rglob('*.txt'):
            self._file_cache[file_path.name] = file_path
    
    def read_data(self, filename: str) -> list:
        # First check the cache
        if filename in self._file_cache:
            file_path = self._file_cache[filename]
        else:
            # Fallback to direct path
            file_path = self.raw_data_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filename} in {self.raw_data_dir}")
        
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
    """
    Processes raw data files and stores them in SQLite database.
    """
    def __init__(self, base_output_path: Path, base_input_path: Path, date_source: str = "first",
                 db: HamiDatabase = None, fallback_city: str = None):
        self.base_output_path = base_output_path
        self.base_input_path = base_input_path
        self.date_source = date_source
        self.fallback_city = fallback_city
        self._known_cities = []

        if self.date_source not in ["first", "last"]:
            raise ValueError("date_source must be either 'first' or 'last'")
        
        # Initialize database
        if db is None:
            db_path = base_output_path / 'hami.db'
            self.db = HamiDatabase(db_path)
        else:
            self.db = db
        
    def fit(self, i_values: list[int]):
        """Process all files for the given hami IDs."""
        raw_data = RawDataReader(raw_data_dir=self.base_input_path)
        loader = DataLoader(data=raw_data)
        express = CombineData()
        self._known_cities = self.db.get_distinct_cities()

        total_new = 0
        total_replaced = 0
        total_enriched = 0
        total_skipped = 0
        
        for i in i_values:
            j = 1
            consecutive_missing = 0
            max_consecutive_missing = 5  # Stop after 5 consecutive missing files
            
            while consecutive_missing < max_consecutive_missing:
                try:
                    loader.fit(filename_number=f"{i}_{j}")
                    express.fit(loader=loader)  
                    
                    # Store in database (replaces if already exists)
                    result = self._store_data(
                        hami_id=str(i),
                        number=j,
                        combined_data=express.compressed_data,
                        subject=express.subject,
                        reference_code=express.reference_code,
                        major=express.major,
                        student_info=express.student_info
                    )
                    
                    if result == 'replaced':
                        total_replaced += 1
                        logger.info(f"Replaced existing data: {i}_{j}")
                    elif result == 'enriched':
                        total_enriched += 1
                        logger.info(f"Filled in excel-only record: {i}_{j}")
                    elif result == 'success':
                        total_new += 1
                        logger.info(f"Added new data: {i}_{j}")
                        
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
                    logger.error(f"Error processing {i}_{j}: {str(e)}")
                    consecutive_missing += 1
                    total_skipped += 1
                    j += 1
        
        print(f"\nProcessing complete:")
        print(f"  - New records added: {total_new} files")
        print(f"  - Excel-only records completed: {total_enriched} files")
        print(f"  - Existing records replaced: {total_replaced} files")
        print(f"  - Skipped (missing/errors): {total_skipped} files")
        print(f"  - Total attempted: {total_new + total_enriched + total_replaced + total_skipped} files")

        return {
            'processed': total_new,
            'replaced': total_replaced,
            'enriched': total_enriched,
            'duplicates': 0,  # Keep for backwards compatibility
            'skipped': total_skipped
        }
    
    def _get_reference_date(self, combined_data: pd.DataFrame) -> jdatetime.datetime:
        """Get the reference date from combined data based on date_source setting."""
        # Filter out dummy dates (year 1500)
        valid_dates = combined_data[combined_data['date'].apply(lambda x: x.year != 1500)]['date']
        
        if len(valid_dates) == 0:
            raise ValueError("No valid dates found in combined data (all dates are dummy dates)")
        
        if self.date_source == "first":
            return valid_dates.iloc[0]
        else:  # "last"
            return valid_dates.iloc[-1]
    
    def _store_data(self, hami_id: str, number: int, combined_data: pd.DataFrame,
                   subject: str, reference_code: str, major: str, student_info: dict) -> str:
        """
        Store request and messages in the database.
        If the data already exists (same reference_code), it will be replaced.

        Returns:
            'success' if stored as new, 'enriched' if an excel-only placeholder was
            claimed by this scrape, 'replaced' if existing scraped data was replaced
        """
        # Get first and last dates
        valid_dates = combined_data[combined_data['date'].apply(lambda x: x.year != 1500)]['date']
        
        first_date = None
        last_date = None
        if len(valid_dates) > 0:
            first_date = str(valid_dates.iloc[0])
            last_date = str(valid_dates.iloc[-1])
        
        city = extract_city_from_place(student_info['field'], self._known_cities)
        if city is None:
            city = self.fallback_city
            logger.warning(
                f"Could not infer city for {hami_id}_{number} from place "
                f"{student_info['field']!r}; using {city!r}"
            )
        elif city not in self._known_cities:
            self._known_cities.append(city)

        # Check if request already exists by reference_code
        existing_request = self.db.get_request_by_reference(reference_code)
        is_replacement = existing_request is not None
        
        if is_replacement:
            # Update existing request
            request_id = existing_request['id']
            self.db.update_request(
                request_id=request_id,
                subject=subject,
                major=major,
                name=student_info['name'],
                national_id=student_info['national_id'],
                student_id=student_info['student_id'],
                field=student_info['field'],
                first_date=first_date,
                last_date=last_date,
                city=city
            )

            # An excel-only row is a metadata placeholder with no hami and no messages;
            # this scrape is the first time we learn who handled it, so claim it instead
            # of leaving the request stranded under the 'unknown' sentinel.
            was_excel_only = (existing_request['source'] == 'excel'
                              and existing_request['hami_id'] == UNKNOWN_HAMI_ID)
            if was_excel_only:
                self.db.update_request_hami_id(request_id, hami_id)
                self.db.update_request_source(request_id, source='both')
                logger.info(f"Claimed excel-only request {reference_code} for hami {hami_id}")

            # Delete existing messages to replace with new ones
            self.db.delete_messages_for_request(request_id)
            logger.info(f"Replacing existing data for reference_code={reference_code}")
        else:
            was_excel_only = False
            # Insert new request
            request_id = self.db.insert_request(
                hami_id=hami_id,
                number=number,
                subject=subject,
                reference_code=reference_code,
                major=major,
                name=student_info['name'],
                national_id=student_info['national_id'],
                student_id=student_info['student_id'],
                field=student_info['field'],
                first_date=first_date,
                last_date=last_date,
                source='scraper',
                city=city
            )
            
            if request_id is None:
                # This shouldn't happen now, but handle gracefully
                logger.error(f"Failed to insert request for reference_code={reference_code}")
                return 'error'
        
        # Prepare messages for bulk insert
        messages = []
        for _, row in combined_data.iterrows():
            messages.append({
                'date': str(row['date']),
                'message': row['message'],
                'from_name': row['from'],
                'to_name': row['to'],
                'to_email': row['to_email'],
                'from_id': row['from_id'],
                'to_id': row['to_id'],
                'matched': bool(row['matched'])
            })
        
        # Bulk insert messages
        self.db.insert_messages_bulk(request_id, messages)

        if was_excel_only:
            return 'enriched'
        return 'replaced' if is_replacement else 'success'


class DuplicateDetector:
    """
    Detects and manages duplicate records based on reference_code in the SQLite database.
    
    NOTE: With SQLite and proper UNIQUE constraints, duplicates should not occur
    during normal operation. This class is kept for manual duplicate management
    and migration from CSV files.
    """
    
    def __init__(self, base_path: Path, date_source: str = "first", db: HamiDatabase = None):
        self.base_path = base_path
        self.date_source = date_source
        if self.date_source not in ["first", "last"]:
            raise ValueError("date_source must be either 'first' or 'last'")
        
        # Initialize database
        if db is None:
            db_path = base_path / 'hami.db'
            self.db = HamiDatabase(db_path)
        else:
            self.db = db
    
    def find_duplicates_by_reference(self) -> Dict[str, List[Dict]]:
        """
        Find all duplicate records grouped by reference_code.
        
        Returns:
            Dictionary with reference_code as key and list of file info as value.
        """
        return self.db.find_duplicates_by_reference()
    
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
    
    def remove_record(self, request_id: int) -> bool:
        """
        Remove a specific record from the database.
        
        Args:
            request_id: The request ID to remove
        
        Returns:
            True if successful, False otherwise
        """
        return self.db.delete_request(request_id)
    
    def keep_older(self, duplicates: Dict[str, List[Dict]] = None) -> Dict:
        """
        For each duplicate group, keep only the oldest record.
        
        Returns:
            Dictionary with removed records info
        """
        if duplicates is None:
            duplicates = self.find_duplicates_by_reference()
        
        removed_count = self.db.remove_duplicate_keep_older()
        
        return {
            'action': 'keep_older',
            'removed_count': removed_count,
        }
    
    def keep_newer(self, duplicates: Dict[str, List[Dict]] = None) -> Dict:
        """
        For each duplicate group, keep only the newest record.
        
        Returns:
            Dictionary with removed records info
        """
        if duplicates is None:
            duplicates = self.find_duplicates_by_reference()
        
        removed_count = self.db.remove_duplicate_keep_newer()
        
        return {
            'action': 'keep_newer',
            'removed_count': removed_count,
        }
    
    def handle_manual_removal(self, records_to_remove: List[Dict]) -> Dict:
        """
        Remove specified records from the database.
        
        Args:
            records_to_remove: List of records to remove with 'id' key
        
        Returns:
            Dictionary with removed records info
        """
        removed = []
        
        for record in records_to_remove:
            request_id = record.get('id') or record.get('request_id')
            if request_id and self.db.delete_request(request_id):
                removed.append(record)
        
        return {
            'action': 'manual_removal',
            'removed_count': len(removed),
            'removed_records': removed
        }



class ExcelTaskListLoader:
    """
    Parses the newer "task list" Excel export - a different data source from
    the email scraper, obtained from another website that lists Hami support
    tickets. Unlike the scraper, this format has no message/workflow content,
    only one summary row per ticket.

    Rows are matched against existing requests by reference_code (the excel's
    'کد پیگیری' column, confirmed to be the same identifier as
    requests.reference_code). Matched rows only get empty fields backfilled
    and their source tag upgraded to 'both' - the scraped data stays
    authoritative. Rows with no match are inserted as metadata-only requests
    (hami_id='unknown', since this source doesn't say which Hami staff member
    handled the ticket, and no messages, since none are available).
    """

    COLUMN_NAME = 'نام دانشجو'
    COLUMN_CLUSTER = 'خوشه'
    COLUMN_NATIONAL_ID = 'کد ملی'
    COLUMN_STUDENT_ID = 'شماره دانشجویی'
    COLUMN_SUBJECT = 'موضوع'
    COLUMN_DATE = 'تاریخ ایجاد'
    COLUMN_REFERENCE = 'کد پیگیری'

    UNKNOWN_HAMI_ID = UNKNOWN_HAMI_ID

    def __init__(self, base_output_path: Path = None, db: HamiDatabase = None):
        if db is None:
            db_path = base_output_path / 'hami.db'
            self.db = HamiDatabase(db_path)
        else:
            self.db = db


    @staticmethod
    def _format_id_value(value) -> str:
        """Excel stores these as numbers, so cast through int() to drop any
        trailing '.0' before stringifying. Returns '<empty>' for missing values,
        matching the sentinel used throughout this codebase."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return '<empty>'
        if isinstance(value, float):
            return str(int(value))
        return str(value).strip()

    @classmethod
    def _format_national_id(cls, value) -> str:
        """Iranian national IDs are always 10 digits, but Excel's numeric
        storage silently drops leading zeros - zero-pad back to 10 digits."""
        formatted = cls._format_id_value(value)
        if formatted == '<empty>':
            return formatted
        return formatted.zfill(10)

    @staticmethod
    def _format_reference_code(value) -> str:
        if isinstance(value, float):
            return str(int(value))
        return str(value).strip()

    @staticmethod
    def _convert_date(value) -> Optional[str]:
        """Convert the excel's Gregorian date (confirmed to represent the
        request's last activity date) to the Jalali 'YYYY-MM-DD 00:00:00'
        string format used for first_date/last_date elsewhere in this DB."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        if isinstance(value, str):
            g_date = datetime.strptime(value.strip(), '%Y/%m/%d').date()
        elif hasattr(value, 'date') and callable(getattr(value, 'date')):
            g_date = value.date()
        else:
            g_date = value
        j_date = jdatetime.date.fromgregorian(date=g_date)
        return f"{j_date.strftime('%Y-%m-%d')} 00:00:00"

    def fit(self, file_path: Path) -> dict:
        """Read the excel file and merge it into the database."""
        df = pd.read_excel(file_path, sheet_name=0)
        known_cities = self.db.get_distinct_cities()

        stats = {'matched': 0, 'backfilled': 0, 'new_inserted': 0, 'errors': 0, 'error_details': []}

        for idx, row in df.iterrows():
            try:
                reference_code = self._format_reference_code(row[self.COLUMN_REFERENCE])
                national_id = self._format_national_id(row.get(self.COLUMN_NATIONAL_ID))
                student_id = self._format_id_value(row.get(self.COLUMN_STUDENT_ID))
                cluster = row.get(self.COLUMN_CLUSTER)
                subject = self._format_id_value(row.get(self.COLUMN_SUBJECT))
                name = self._format_id_value(row.get(self.COLUMN_NAME))
                city = extract_city_from_place(cluster, known_cities)
                converted_date = self._convert_date(row.get(self.COLUMN_DATE))

                existing = self.db.get_request_by_reference(reference_code)

                if existing:
                    stats['matched'] += 1
                    changed = self.db.backfill_empty_fields(
                        request_id=existing['id'],
                        national_id=national_id if national_id != '<empty>' else None,
                        student_id=student_id if student_id != '<empty>' else None
                    )
                    if changed:
                        stats['backfilled'] += 1
                    self.db.update_request_source(existing['id'], source='both')
                else:
                    major_field = self._format_id_value(cluster)
                    self.db.insert_request(
                        hami_id=self.UNKNOWN_HAMI_ID,
                        number=0,  # ignored by insert_request, which auto-assigns it
                        subject=subject,
                        reference_code=reference_code,
                        major=major_field,
                        name=name,
                        national_id=national_id,
                        student_id=student_id,
                        field=major_field,
                        first_date=converted_date,
                        last_date=converted_date,
                        source='excel',
                        city=city
                    )
                    stats['new_inserted'] += 1
            except Exception as e:
                logger.error(f"Error processing excel row {idx}: {e}")
                stats['errors'] += 1
                stats['error_details'].append(f"Row {idx}: {e}")

        return stats


# Legacy CSV-based DuplicateDetector for migration purposes
class LegacyCSVMigrator:
    """
    Legacy CSV-based data migrator.
    Used only for migrating old CSV data to SQLite database.
    """
    
    def __init__(self, base_path: Path, date_source: str = "first"):
        self.base_path = base_path
        self.date_source = date_source
        if self.date_source not in ["first", "last"]:
            raise ValueError("date_source must be either 'first' or 'last'")
    
    def migrate_to_sqlite(self, db: HamiDatabase) -> Dict:
        """
        Migrate all CSV data to SQLite database.
        
        Returns:
            Dictionary with migration statistics
        """
        date_source_path = self.base_path / self.date_source
        
        if not date_source_path.exists():
            return {'error': 'Database path does not exist', 'migrated': 0}
        
        total_requests = 0
        total_messages = 0
        skipped_duplicates = 0
        errors = []
        
        # Iterate through all year-month folders
        for month_folder in sorted(date_source_path.iterdir()):
            if not month_folder.is_dir():
                continue
            
            hami_dir = month_folder / "hami_output"
            combined_dir = month_folder / "combined_output"
            
            if not hami_dir.exists():
                continue
            
            # Read all hami files in this month
            for hami_file in sorted(hami_dir.glob("hami_*.csv")):
                try:
                    df = pd.read_csv(hami_file, dtype={'reference_code': str, 'national_id': str, 'student_id': str})
                    hami_id = hami_file.stem.replace("hami_", "")
                    
                    for idx, row in df.iterrows():
                        # Strip Excel formula format
                        ref_code = strip_excel_formula(row.get('reference_code', ''))
                        national_id = strip_excel_formula(row.get('national_id', ''))
                        student_id = strip_excel_formula(row.get('student_id', ''))
                        
                        number = int(row['number'])
                        
                        # Try to get combined file for dates
                        combined_file = combined_dir / f"combined_{hami_id}_{number}.csv"
                        first_date = None
                        last_date = None
                        messages = []
                        
                        if combined_file.exists():
                            try:
                                combined_df = pd.read_csv(combined_file)
                                # Parse dates and filter out dummy dates
                                valid_dates = combined_df[~combined_df['date'].astype(str).str.startswith('1500')]['date']
                                if len(valid_dates) > 0:
                                    first_date = str(valid_dates.iloc[0])
                                    last_date = str(valid_dates.iloc[-1])
                                
                                # Prepare messages
                                for _, msg_row in combined_df.iterrows():
                                    messages.append({
                                        'date': str(msg_row['date']),
                                        'message': str(msg_row.get('message', '')),
                                        'from_name': str(msg_row.get('from', '')),
                                        'to_name': str(msg_row.get('to', '')),
                                        'to_email': str(msg_row.get('to_email', '')),
                                        'from_id': str(msg_row.get('from_id', '')),
                                        'to_id': str(msg_row.get('to_id', '')),
                                        'matched': bool(msg_row.get('matched', False))
                                    })
                            except Exception as e:
                                errors.append(f"Error reading combined file {combined_file}: {e}")
                        
                        # Insert request
                        request_id = db.insert_request(
                            hami_id=str(hami_id),
                            number=number,
                            subject=str(row.get('subject', '')),
                            reference_code=ref_code,
                            major=str(row.get('major', '')),
                            name=str(row.get('name', '')),
                            national_id=national_id,
                            student_id=student_id,
                            field=str(row.get('field', '')),
                            first_date=first_date,
                            last_date=last_date
                        )
                        
                        if request_id:
                            total_requests += 1
                            # Insert messages
                            if messages:
                                count = db.insert_messages_bulk(request_id, messages)
                                total_messages += count
                        else:
                            skipped_duplicates += 1
                        
                except Exception as e:
                    errors.append(f"Error processing {hami_file}: {e}")
                    continue
        
        return {
            'migrated_requests': total_requests,
            'migrated_messages': total_messages,
            'skipped_duplicates': skipped_duplicates,
            'errors': errors
        }
    
    def find_all_csv_records(self) -> List[Dict]:
        """
        Find all records in CSV files for inspection.
        
        Returns:
            List of all records found
        """
        all_records = []
        date_source_path = self.base_path / self.date_source
        
        if not date_source_path.exists():
            return all_records
        
        for month_folder in sorted(date_source_path.iterdir()):
            if not month_folder.is_dir():
                continue
            
            hami_dir = month_folder / "hami_output"
            if not hami_dir.exists():
                continue
            
            for hami_file in sorted(hami_dir.glob("hami_*.csv")):
                try:
                    df = pd.read_csv(hami_file, dtype={'reference_code': str, 'national_id': str, 'student_id': str})
                    hami_id = hami_file.stem.replace("hami_", "")
                    
                    for idx, row in df.iterrows():
                        ref_code = strip_excel_formula(row.get('reference_code', ''))
                        
                        record_info = {
                            'reference_code': ref_code,
                            'hami_id': str(hami_id),
                            'number': int(row['number']),
                            'month': month_folder.name,
                            'subject': str(row.get('subject', '')),
                            'name': str(row.get('name', '')),
                            'major': str(row.get('major', '')),
                            'student_id': strip_excel_formula(row.get('student_id', '')),
                            'national_id': strip_excel_formula(row.get('national_id', ''))
                        }
                        all_records.append(record_info)
                        
                except Exception:
                    continue
        
        return all_records
