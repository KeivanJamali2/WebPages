"""
Database module for HamiAnalyzer
Uses SQLite for data storage with proper integrity constraints
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class HamiDatabase:
    """
    SQLite database manager for HamiAnalyzer.
    
    Tables:
    - requests: Main table storing request metadata (formerly hami_output)
    - messages: Table storing individual messages (formerly combined_output)
    """
    
    def __init__(self, db_path: Path):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create requests table (formerly hami_output data)
            # UNIQUE constraint on reference_code only - it's the true unique identifier
            # number is auto-generated per hami_id for display purposes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hami_id TEXT NOT NULL,
                    number INTEGER NOT NULL,
                    subject TEXT,
                    reference_code TEXT UNIQUE,
                    major TEXT,
                    name TEXT,
                    national_id TEXT,
                    student_id TEXT,
                    field TEXT,
                    first_date TEXT,
                    last_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create messages table (formerly combined_output data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    message TEXT,
                    from_name TEXT,
                    to_name TEXT,
                    to_email TEXT,
                    from_id TEXT,
                    to_id TEXT,
                    matched BOOLEAN DEFAULT 0,
                    FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_requests_hami_id 
                ON requests(hami_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_requests_reference_code 
                ON requests(reference_code)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_requests_name 
                ON requests(name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_request_id 
                ON messages(request_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_date 
                ON messages(date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_from_name 
                ON messages(from_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_to_name 
                ON messages(to_name)
            """)
            
            logger.info(f"Database initialized at {self.db_path}")
    
    # ==================== REQUEST OPERATIONS ====================
    
    def insert_request(self, hami_id: str, number: int, subject: str, 
                      reference_code: str, major: str, name: str,
                      national_id: str, student_id: str, field: str,
                      first_date: str = None, last_date: str = None) -> Optional[int]:
        """
        Insert a new request. Returns the request ID or None if duplicate.
        
        The 'number' parameter from input is IGNORED - we auto-generate a unique
        sequential number for each hami_id to ensure uniqueness.
        
        Uses reference_code as the unique identifier to prevent duplicates.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # First check if this reference_code already exists
            cursor.execute(
                "SELECT id FROM requests WHERE reference_code = ?", 
                (reference_code,)
            )
            existing = cursor.fetchone()
            if existing:
                logger.info(f"Request with reference_code={reference_code} already exists (id={existing['id']})")
                return existing['id']
            
            # Auto-generate the next number for this hami_id
            cursor.execute(
                "SELECT COALESCE(MAX(number), 0) + 1 as next_num FROM requests WHERE hami_id = ?",
                (hami_id,)
            )
            auto_number = cursor.fetchone()['next_num']
            
            try:
                cursor.execute("""
                    INSERT INTO requests 
                    (hami_id, number, subject, reference_code, major, name, 
                     national_id, student_id, field, first_date, last_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (hami_id, auto_number, subject, reference_code, major, name,
                      national_id, student_id, field, first_date, last_date))
                return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                # Duplicate reference_code (race condition handling)
                logger.warning(f"Duplicate request: ref={reference_code}: {e}")
                cursor.execute(
                    "SELECT id FROM requests WHERE reference_code = ?",
                    (reference_code,)
                )
                row = cursor.fetchone()
                return row['id'] if row else None
    
    def get_request(self, request_id: int) -> Optional[Dict]:
        """Get a request by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_request_by_hami_number(self, hami_id: str, number: int) -> Optional[Dict]:
        """Get a request by hami_id and number. Now unique since number is auto-generated."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM requests 
                WHERE hami_id = ? AND number = ?
            """, (hami_id, number))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_request_by_reference(self, reference_code: str) -> Optional[Dict]:
        """Get a request by reference_code (the unique identifier)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM requests 
                WHERE reference_code = ?
            """, (reference_code,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_requests_by_hami(self, hami_id: str) -> List[Dict]:
        """Get all requests for a hami."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM requests 
                WHERE hami_id = ? 
                ORDER BY number
            """, (hami_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def search_requests_by_reference(self, reference_code: str) -> List[Dict]:
        """Search requests by reference code (exact match)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM requests 
                WHERE reference_code = ?
            """, (reference_code,))
            return [dict(row) for row in cursor.fetchall()]
    
    def search_requests_by_field(self, field_name: str, search_value: str) -> List[Dict]:
        """Search requests by a specific field (partial match)."""
        valid_fields = ['subject', 'name', 'major', 'field', 'student_id', 'national_id']
        if field_name not in valid_fields:
            raise ValueError(f"Invalid field: {field_name}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Use LIKE for partial matching
            cursor.execute(f"""
                SELECT * FROM requests 
                WHERE {field_name} LIKE ?
            """, (f'%{search_value}%',))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_requests(self) -> List[Dict]:
        """Get all requests."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM requests ORDER BY hami_id, number")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_unique_hami_ids(self) -> List[str]:
        """Get list of unique hami IDs."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT hami_id FROM requests ORDER BY hami_id")
            return [row['hami_id'] for row in cursor.fetchall()]
    
    def update_request_dates(self, request_id: int, first_date: str, last_date: str):
        """Update the first and last dates for a request."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE requests 
                SET first_date = ?, last_date = ?
                WHERE id = ?
            """, (first_date, last_date, request_id))
    
    def update_request(self, request_id: int, subject: str, major: str,
                       name: str, national_id: str, student_id: str, field: str,
                       first_date: str = None, last_date: str = None):
        """Update all fields of an existing request (except hami_id, number, and reference_code)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE requests 
                SET subject = ?, major = ?, name = ?, national_id = ?, 
                    student_id = ?, field = ?, first_date = ?, last_date = ?
                WHERE id = ?
            """, (subject, major, name, national_id, student_id, field, 
                  first_date, last_date, request_id))
            logger.info(f"Updated request {request_id}")
    
    def delete_request(self, request_id: int) -> bool:
        """Delete a request and its messages (cascade)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM requests WHERE id = ?", (request_id,))
            return cursor.rowcount > 0
    
    # ==================== MESSAGE OPERATIONS ====================
    
    def insert_message(self, request_id: int, date: str, message: str,
                      from_name: str, to_name: str, to_email: str,
                      from_id: str, to_id: str, matched: bool) -> int:
        """Insert a new message."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages 
                (request_id, date, message, from_name, to_name, to_email, 
                 from_id, to_id, matched)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (request_id, date, message, from_name, to_name, to_email,
                  from_id, to_id, matched))
            return cursor.lastrowid
    
    def insert_messages_bulk(self, request_id: int, messages: List[Dict]) -> int:
        """Insert multiple messages at once."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            data = [(
                request_id,
                msg['date'],
                msg['message'],
                msg['from_name'],
                msg['to_name'],
                msg['to_email'],
                msg['from_id'],
                msg['to_id'],
                msg['matched']
            ) for msg in messages]
            
            cursor.executemany("""
                INSERT INTO messages 
                (request_id, date, message, from_name, to_name, to_email, 
                 from_id, to_id, matched)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            return len(data)
    
    def get_messages_for_request(self, request_id: int) -> List[Dict]:
        """Get all messages for a request."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM messages 
                WHERE request_id = ? 
                ORDER BY date
            """, (request_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_messages_by_hami_number(self, hami_id: str, number: int) -> List[Dict]:
        """Get messages by hami_id and number."""
        request = self.get_request_by_hami_number(hami_id, number)
        if request:
            return self.get_messages_for_request(request['id'])
        return []
    
    def search_messages_by_person(self, person_name: str) -> List[Dict]:
        """Search messages by person name (in from_name or to_name)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.*, r.hami_id, r.number, r.subject, r.reference_code, r.name as student_name
                FROM messages m
                JOIN requests r ON m.request_id = r.id
                WHERE m.from_name LIKE ? OR m.to_name LIKE ?
                ORDER BY m.date
            """, (f'%{person_name}%', f'%{person_name}%'))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_messages(self) -> List[Dict]:
        """Get all messages with request info."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.*, r.hami_id, r.number, r.subject, r.reference_code
                FROM messages m
                JOIN requests r ON m.request_id = r.id
                ORDER BY r.hami_id, r.number, m.date
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== DATE RANGE QUERIES ====================
    
    def get_requests_by_date_range(self, start_date: str = None, 
                                   end_date: str = None,
                                   date_field: str = 'first_date') -> List[Dict]:
        """
        Get requests within a date range.
        
        Args:
            start_date: Start date in format 'YYYY-MM-DD'
            end_date: End date in format 'YYYY-MM-DD'
            date_field: Which date field to use ('first_date' or 'last_date')
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            conditions = []
            params = []
            
            if start_date:
                conditions.append(f"{date_field} >= ?")
                params.append(start_date)
            if end_date:
                conditions.append(f"{date_field} < ?")
                params.append(end_date)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            cursor.execute(f"""
                SELECT * FROM requests 
                WHERE {where_clause}
                ORDER BY {date_field}
            """, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_messages_by_date_range(self, start_date: str = None, 
                                   end_date: str = None) -> List[Dict]:
        """Get messages within a date range."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            conditions = ["date != '1500-01-01 00:00:00'"]  # Exclude dummy dates
            params = []
            
            if start_date:
                conditions.append("date >= ?")
                params.append(start_date)
            if end_date:
                conditions.append("date < ?")
                params.append(end_date)
            
            where_clause = " AND ".join(conditions)
            
            cursor.execute(f"""
                SELECT m.*, r.hami_id, r.number, r.subject, r.reference_code
                FROM messages m
                JOIN requests r ON m.request_id = r.id
                WHERE {where_clause}
                ORDER BY m.date
            """, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== STATISTICS ====================
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count unique hamis
            cursor.execute("SELECT COUNT(DISTINCT hami_id) FROM requests")
            unique_hamis = cursor.fetchone()[0]
            
            # Count total requests
            cursor.execute("SELECT COUNT(*) FROM requests")
            total_requests = cursor.fetchone()[0]
            
            # Count total messages
            cursor.execute("SELECT COUNT(*) FROM messages")
            total_messages = cursor.fetchone()[0]
            
            # Get date range
            cursor.execute("""
                SELECT MIN(first_date), MAX(last_date) 
                FROM requests 
                WHERE first_date IS NOT NULL
            """)
            date_range = cursor.fetchone()
            
            # Get requests per hami
            cursor.execute("""
                SELECT hami_id, COUNT(*) as count 
                FROM requests 
                GROUP BY hami_id 
                ORDER BY count DESC
            """)
            requests_per_hami = {row['hami_id']: row['count'] for row in cursor.fetchall()}
            
            return {
                'unique_hamis': unique_hamis,
                'total_requests': total_requests,
                'total_messages': total_messages,
                'date_range': {
                    'start': date_range[0] if date_range else None,
                    'end': date_range[1] if date_range else None
                },
                'requests_per_hami': requests_per_hami
            }
    
    def get_requests_count_by_hami(self) -> Dict[str, int]:
        """Get count of requests per hami ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT hami_id, COUNT(*) as count 
                FROM requests 
                GROUP BY hami_id 
                ORDER BY hami_id
            """)
            return {row['hami_id']: row['count'] for row in cursor.fetchall()}
    
    # ==================== DUPLICATE DETECTION ====================
    
    def find_duplicates_by_reference(self) -> Dict[str, List[Dict]]:
        """Find duplicate requests by reference code."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Find reference codes that appear more than once
            cursor.execute("""
                SELECT reference_code, COUNT(*) as count
                FROM requests
                WHERE reference_code IS NOT NULL AND reference_code != ''
                GROUP BY reference_code
                HAVING count > 1
            """)
            duplicate_refs = cursor.fetchall()
            
            duplicates = {}
            for row in duplicate_refs:
                ref_code = row['reference_code']
                cursor.execute("""
                    SELECT * FROM requests 
                    WHERE reference_code = ?
                    ORDER BY created_at
                """, (ref_code,))
                duplicates[ref_code] = [dict(r) for r in cursor.fetchall()]
            
            return duplicates
    
    def remove_duplicate_keep_newer(self) -> int:
        """Remove duplicate requests, keeping the newer one."""
        duplicates = self.find_duplicates_by_reference()
        removed_count = 0
        
        for ref_code, records in duplicates.items():
            if len(records) > 1:
                # Sort by created_at descending, keep the first (newest)
                sorted_records = sorted(records, key=lambda x: x['created_at'], reverse=True)
                for record in sorted_records[1:]:  # Skip the newest
                    self.delete_request(record['id'])
                    removed_count += 1
        
        return removed_count
    
    def remove_duplicate_keep_older(self) -> int:
        """Remove duplicate requests, keeping the older one."""
        duplicates = self.find_duplicates_by_reference()
        removed_count = 0
        
        for ref_code, records in duplicates.items():
            if len(records) > 1:
                # Sort by created_at ascending, keep the first (oldest)
                sorted_records = sorted(records, key=lambda x: x['created_at'])
                for record in sorted_records[1:]:  # Skip the oldest
                    self.delete_request(record['id'])
                    removed_count += 1
        
        return removed_count
    
    # ==================== NO WORKFLOW REQUESTS ====================
    
    def get_requests_with_no_workflow(self) -> List[Dict]:
        """
        Get all requests where ALL messages have 'Not in workflow' status.
        These are requests that have ZERO workflow data - completely missing workflow.
        Requests with at least one message with workflow data are excluded.
        
        Returns:
            List of request dictionaries with message count info
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Find requests where EVERY message is "Not in workflow"
            # by excluding requests that have ANY message with valid workflow
            cursor.execute("""
                SELECT r.id, r.hami_id, r.number, r.reference_code, r.subject, r.name,
                       r.field, r.last_date,
                       COUNT(m.id) as total_messages
                FROM requests r
                JOIN messages m ON r.id = m.request_id
                WHERE r.id NOT IN (
                    SELECT DISTINCT request_id FROM messages 
                    WHERE from_name != 'Not in workflow' OR to_name != 'Not in workflow'
                )
                GROUP BY r.id
                ORDER BY r.last_date DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_no_workflow_count(self) -> Dict[str, int]:
        """
        Get count of requests that have NO workflow at all (all messages are 'Not in workflow').
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Count requests where ALL messages are "Not in workflow"
            cursor.execute("""
                SELECT COUNT(*) as request_count,
                       (SELECT COUNT(*) FROM messages m 
                        WHERE m.request_id IN (
                            SELECT r2.id FROM requests r2
                            WHERE r2.id NOT IN (
                                SELECT DISTINCT request_id FROM messages 
                                WHERE from_name != 'Not in workflow' OR to_name != 'Not in workflow'
                            )
                        )
                       ) as message_count
                FROM requests r
                WHERE r.id NOT IN (
                    SELECT DISTINCT request_id FROM messages 
                    WHERE from_name != 'Not in workflow' OR to_name != 'Not in workflow'
                )
            """)
            row = cursor.fetchone()
            return {
                'requests': row['request_count'] if row else 0,
                'messages': row['message_count'] if row else 0
            }
    
    def get_request_messages_detail(self, request_id: int) -> Dict:
        """
        Get detailed information about a request and its messages.
        Used for the workflow editor.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get request info
            cursor.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
            request = cursor.fetchone()
            if not request:
                return None
            
            # Get all messages
            cursor.execute("""
                SELECT * FROM messages 
                WHERE request_id = ? 
                ORDER BY date
            """, (request_id,))
            messages = [dict(row) for row in cursor.fetchall()]
            
            return {
                'request': dict(request),
                'messages': messages
            }
    
    def update_message_workflow(self, message_id: int, from_name: str, to_name: str, 
                                to_email: str, from_id: str, to_id: str) -> bool:
        """
        Update workflow information for a specific message.
        
        Args:
            message_id: ID of the message to update
            from_name: Sender name
            to_name: Receiver name
            to_email: Receiver email
            from_id: Sender workflow ID
            to_id: Receiver workflow ID
            
        Returns:
            True if update was successful
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE messages 
                SET from_name = ?, to_name = ?, to_email = ?, from_id = ?, to_id = ?, matched = 1
                WHERE id = ?
            """, (from_name, to_name, to_email, from_id, to_id, message_id))
            return cursor.rowcount > 0
    
    def bulk_update_messages_workflow(self, request_id: int, workflow_data: List[Dict]) -> int:
        """
        Bulk update workflow data for all messages in a request.
        
        Args:
            request_id: ID of the request
            workflow_data: List of dicts with keys: message_id, from_name, to_name, to_email, from_id, to_id
            
        Returns:
            Number of messages updated
        """
        updated = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for data in workflow_data:
                cursor.execute("""
                    UPDATE messages 
                    SET from_name = ?, to_name = ?, to_email = ?, from_id = ?, to_id = ?, matched = 1
                    WHERE id = ? AND request_id = ?
                """, (data['from_name'], data['to_name'], data['to_email'], 
                      data['from_id'], data['to_id'], data['message_id'], request_id))
                if cursor.rowcount > 0:
                    updated += 1
        return updated
    
    def delete_messages_for_request(self, request_id: int) -> int:
        """Delete all messages for a request (for re-importing workflow)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE request_id = ?", (request_id,))
            return cursor.rowcount
    
    def clear_workflow_for_request(self, request_id: int) -> int:
        """
        Clear workflow data for all messages in a request.
        Sets from_name, to_name, to_email to 'Not in workflow' and clears IDs.
        
        Returns:
            Number of messages updated
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE messages 
                SET from_name = 'Not in workflow', 
                    to_name = 'Not in workflow', 
                    to_email = 'Not in workflow',
                    from_id = '<empty>',
                    to_id = '<empty>',
                    matched = 0
                WHERE request_id = ?
            """, (request_id,))
            return cursor.rowcount
    
    def insert_workflow_messages(self, request_id: int, messages: List[Dict]) -> int:
        """
        Insert new workflow messages for a request.
        Used when user pastes workflow data manually.
        """
        return self.insert_messages_bulk(request_id, messages)
    
    def _convert_persian_date_to_db_format(self, persian_date: str) -> str:
        """
        Convert Persian date format to database format.
        Input: "دوشنبه، 27 مرداد 1404 18:23" 
        Output: "1404-05-27 18:23:00"
        
        Also handles database format input (returns as-is).
        """
        import re
        
        if not persian_date:
            return persian_date
        
        # Check if already in database format: "1404-02-10 11:20:00"
        if re.match(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}', persian_date):
            return persian_date
        
        persian_months = {
            'فروردین': 1, 'اردیبهشت': 2, 'خرداد': 3, 'تیر': 4,
            'مرداد': 5, 'شهریور': 6, 'مهر': 7, 'آبان': 8,
            'آذر': 9, 'دی': 10, 'بهمن': 11, 'اسفند': 12
        }
        
        try:
            # Format: "دوشنبه، 27 مرداد 1404 18:23"
            # Remove day name and comma
            parts = persian_date.split('،')
            if len(parts) < 2:
                return persian_date
            
            rest = parts[1].strip()
            # Split: "27 مرداد 1404 18:23"
            tokens = rest.split()
            if len(tokens) < 4:
                return persian_date
            
            day = int(tokens[0])
            month_name = tokens[1]
            year = int(tokens[2])
            time_str = tokens[3] if len(tokens) > 3 else "00:00"
            
            month = persian_months.get(month_name, 1)
            
            # Format time
            if ':' in time_str:
                time_parts = time_str.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            else:
                hour, minute = 0, 0
            
            return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:00"
        except Exception as e:
            logger.warning(f"Could not convert date '{persian_date}': {e}")
            return persian_date
    
    def apply_workflow_text(self, request_id: int, workflow_entries: List[Dict]) -> Dict:
        """
        Apply parsed workflow entries to a request.
        Matches by date or creates new messages if date doesn't exist.
        
        Args:
            request_id: ID of the request
            workflow_entries: List of dicts with keys: parent_id, id, date, name, email, uuid
            
        Returns:
            Dict with 'updated', 'created', 'errors' counts
        """
        import uuid as uuid_module
        
        result = {'updated': 0, 'created': 0, 'errors': [], 'details': []}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get existing messages for this request
            cursor.execute("""
                SELECT id, date FROM messages 
                WHERE request_id = ? 
                ORDER BY date
            """, (request_id,))
            existing_messages = {row['date']: row['id'] for row in cursor.fetchall()}
            
            # Build UUID mapping (simple id -> generated UUID)
            id_to_uuid = {}
            for entry in workflow_entries:
                simple_id = str(entry.get('id', ''))
                if simple_id and simple_id not in id_to_uuid:
                    id_to_uuid[simple_id] = str(uuid_module.uuid4())
            
            # Process each workflow entry
            for i, entry in enumerate(workflow_entries):
                try:
                    # Convert date to database format
                    entry_date_raw = entry.get('date', '')
                    entry_date = self._convert_persian_date_to_db_format(entry_date_raw)
                    
                    entry_name = entry.get('name', '')
                    entry_email = entry.get('email', '')
                    simple_id = str(entry.get('id', ''))
                    simple_parent_id = str(entry.get('parent_id', ''))
                    
                    # Get UUIDs
                    entry_uuid = id_to_uuid.get(simple_id, str(uuid_module.uuid4()))
                    parent_uuid = id_to_uuid.get(simple_parent_id, '') if simple_parent_id and simple_parent_id.lower() != 'none' else ''
                    
                    # Determine from_name/to_name based on position
                    # In workflow: entry i sends to entry i+1
                    # So for message matching:
                    # - from_name = current entry name (sender)
                    # - to_name = next entry name (receiver)
                    
                    from_name = entry_name
                    from_id = entry_uuid
                    
                    # Get next entry info for to_name
                    if i + 1 < len(workflow_entries):
                        to_name = workflow_entries[i + 1].get('name', '')
                        to_email = workflow_entries[i + 1].get('email', '')
                        next_simple_id = str(workflow_entries[i + 1].get('id', ''))
                        to_id = id_to_uuid.get(next_simple_id, '')
                    else:
                        to_name = ''
                        to_email = ''
                        to_id = ''
                    
                    # Try to match by date
                    matched_msg_id = existing_messages.get(entry_date)
                    
                    if matched_msg_id:
                        # Update existing message
                        cursor.execute("""
                            UPDATE messages 
                            SET from_name = ?, to_name = ?, to_email = ?, from_id = ?, to_id = ?, matched = 1
                            WHERE id = ?
                        """, (from_name, to_name, to_email, from_id, to_id, matched_msg_id))
                        result['updated'] += 1
                        result['details'].append({
                            'action': 'updated',
                            'date': entry_date,
                            'from': from_name,
                            'to': to_name
                        })
                    else:
                        # Create new message
                        cursor.execute("""
                            INSERT INTO messages (request_id, date, from_name, to_name, to_email, from_id, to_id, matched)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                        """, (request_id, entry_date, from_name, to_name, to_email, from_id, to_id))
                        result['created'] += 1
                        result['details'].append({
                            'action': 'created',
                            'date': entry_date,
                            'from': from_name,
                            'to': to_name
                        })
                        # Add to existing messages map
                        existing_messages[entry_date] = cursor.lastrowid
                        
                except Exception as e:
                    result['errors'].append(f"Entry {i+1}: {str(e)}")
            
            conn.commit()
        
        return result
    
    def get_message_by_date(self, request_id: int, date: str) -> Dict:
        """Get a message by request_id and date."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM messages 
                WHERE request_id = ? AND date = ?
            """, (request_id, date))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ==================== DATABASE MANAGEMENT ====================
    
    def clear_database(self):
        """Clear all data from the database while keeping the schema intact."""
        # First ensure the schema exists
        self._init_database()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Delete data from tables (order matters due to foreign keys)
            cursor.execute("DELETE FROM messages")
            cursor.execute("DELETE FROM requests")
            # Reset autoincrement counters (sqlite_sequence may not exist if no inserts happened)
            try:
                cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('messages', 'requests')")
            except sqlite3.OperationalError:
                pass  # sqlite_sequence doesn't exist yet, which is fine
            logger.info("Database cleared - schema preserved, data removed")
    
    def vacuum(self):
        """Optimize database by reclaiming unused space."""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
    
    def get_database_size(self) -> str:
        """Get database file size."""
        if self.db_path.exists():
            size_bytes = self.db_path.stat().st_size
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.2f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.2f} MB"
        return "0 B"
    
    # ==================== ANALYTICS FUNCTIONS ====================
    
    def get_requests_count_per_hami(self, start_date: str = None, end_date: str = None) -> Dict[str, int]:
        """Get count of requests per hami_id - optimized SQL query."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT hami_id, COUNT(*) as count FROM requests WHERE 1=1"
            params = []
            if start_date:
                query += " AND first_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND first_date < ?"
                params.append(end_date)
            query += " GROUP BY hami_id ORDER BY count DESC"
            cursor.execute(query, params)
            return {row['hami_id']: row['count'] for row in cursor.fetchall()}
    
    def get_message_dates(self, start_date: str = None, end_date: str = None) -> List[str]:
        """Get all message dates (excluding dummy dates) - returns raw date strings."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT DISTINCT date FROM messages 
                WHERE date != '1500-01-01 00:00:00'
            """
            params = []
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date < ?"
                params.append(end_date)
            cursor.execute(query, params)
            return [row['date'] for row in cursor.fetchall()]
    
    def get_request_first_dates(self, start_date: str = None, end_date: str = None) -> List[str]:
        """Get first_date from all requests."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT first_date FROM requests WHERE first_date IS NOT NULL"
            params = []
            if start_date:
                query += " AND first_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND first_date < ?"
                params.append(end_date)
            cursor.execute(query, params)
            return [row['first_date'] for row in cursor.fetchall()]
    
    def get_message_count_by_date(self, group_by: str = 'month', start_date: str = None, end_date: str = None) -> Dict[str, int]:
        """
        Get message counts grouped by date.
        group_by: 'day' or 'month'
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            date_length = 10 if group_by == 'day' else 7
            query = f"SELECT SUBSTR(date, 1, {date_length}) as date_key, COUNT(*) as count FROM messages WHERE date != '1500-01-01 00:00:00'"
            params = []
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date < ?"
                params.append(end_date)
            query += " GROUP BY date_key ORDER BY date_key"
            cursor.execute(query, params)
            return {row['date_key']: row['count'] for row in cursor.fetchall()}
    
    def get_request_count_by_month(self, start_date: str = None, end_date: str = None) -> Dict[str, int]:
        """Get request counts grouped by month (using first_date)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT SUBSTR(first_date, 1, 7) as month_key, COUNT(*) as count FROM requests WHERE first_date IS NOT NULL"
            params = []
            if start_date:
                query += " AND first_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND first_date < ?"
                params.append(end_date)
            query += " GROUP BY month_key ORDER BY month_key"
            cursor.execute(query, params)
            return {row['month_key']: row['count'] for row in cursor.fetchall()}
    
    def get_communicator_stats(self, is_employee: bool = True, by_messages: bool = True, 
                                start_date: str = None, end_date: str = None) -> Tuple[Dict[str, int], Dict[str, int]]:
        """
        Get top communicators (senders and receivers).
        
        Args:
            is_employee: If True, get employees (non-student emails). If False, get students.
            by_messages: If True, count all messages. If False, count unique per request.
            start_date: Optional start date filter (YYYY-MM-DD format)
            end_date: Optional end date filter (YYYY-MM-DD format)
        
        Returns:
            Tuple of (senders_count, receivers_count) dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Pattern for student emails: 10 digits followed by @iau.ir
            if is_employee:
                email_condition = "NOT (to_email GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]@iau.ir')"
            else:
                email_condition = "to_email GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]@iau.ir'"
            
            valid_condition = "to_name NOT IN ('<empty>', 'Not in workflow') AND from_name NOT IN ('<empty>', 'Not in workflow')"
            
            # Build date condition
            date_condition = ""
            params = []
            if start_date:
                date_condition += " AND date >= ?"
                params.append(start_date)
            if end_date:
                date_condition += " AND date < ?"
                params.append(end_date)
            
            if by_messages:
                # Count all messages
                # Receivers
                cursor.execute(f"""
                    SELECT to_name, COUNT(*) as count
                    FROM messages
                    WHERE {email_condition} AND {valid_condition}{date_condition}
                    GROUP BY to_name
                    ORDER BY count DESC
                """, params)
                receivers = {row['to_name']: row['count'] for row in cursor.fetchall()}
                
                # Senders (who sent TO employees/students)
                cursor.execute(f"""
                    SELECT from_name, COUNT(*) as count
                    FROM messages m
                    WHERE {email_condition} AND {valid_condition}{date_condition}
                    GROUP BY from_name
                    ORDER BY count DESC
                """, params)
                senders = {row['from_name']: row['count'] for row in cursor.fetchall()}
            else:
                # Count unique per request
                cursor.execute(f"""
                    SELECT to_name, COUNT(DISTINCT request_id) as count
                    FROM messages
                    WHERE {email_condition} AND {valid_condition}{date_condition}
                    GROUP BY to_name
                    ORDER BY count DESC
                """, params)
                receivers = {row['to_name']: row['count'] for row in cursor.fetchall()}
                
                cursor.execute(f"""
                    SELECT from_name, COUNT(DISTINCT request_id) as count
                    FROM messages
                    WHERE {email_condition} AND {valid_condition}{date_condition}
                    GROUP BY from_name
                    ORDER BY count DESC
                """, params)
                senders = {row['from_name']: row['count'] for row in cursor.fetchall()}
            
            return senders, receivers
    
    def get_place_stats(self, by_messages: bool = True, start_date: str = None, end_date: str = None) -> Tuple[Dict[str, int], Dict[str, int]]:
        """
        Get top place communicators (places are names ending with 4 digits).
        
        Args:
            by_messages: If True, count all messages. If False, count unique per request.
            start_date: Optional start date filter (YYYY-MM-DD format)
            end_date: Optional end date filter (YYYY-MM-DD format)
        
        Returns:
            Tuple of (senders_count, receivers_count) dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Places end with 4 digits
            place_condition_to = "(to_name GLOB '*[0-9][0-9][0-9][0-9]')"
            place_condition_from = "(from_name GLOB '*[0-9][0-9][0-9][0-9]')"
            valid_condition = "to_name NOT IN ('<empty>', 'Not in workflow') AND from_name NOT IN ('<empty>', 'Not in workflow')"
            
            # Build date condition
            date_condition = ""
            params = []
            if start_date:
                date_condition += " AND date >= ?"
                params.append(start_date)
            if end_date:
                date_condition += " AND date < ?"
                params.append(end_date)
            
            if by_messages:
                cursor.execute(f"""
                    SELECT to_name, COUNT(*) as count
                    FROM messages
                    WHERE {place_condition_to} AND {valid_condition}{date_condition}
                    GROUP BY to_name
                    ORDER BY count DESC
                """, params)
                receivers = {row['to_name']: row['count'] for row in cursor.fetchall()}
                
                cursor.execute(f"""
                    SELECT from_name, COUNT(*) as count
                    FROM messages
                    WHERE {place_condition_from} AND {valid_condition}{date_condition}
                    GROUP BY from_name
                    ORDER BY count DESC
                """, params)
                senders = {row['from_name']: row['count'] for row in cursor.fetchall()}
            else:
                cursor.execute(f"""
                    SELECT to_name, COUNT(DISTINCT request_id) as count
                    FROM messages
                    WHERE {place_condition_to} AND {valid_condition}{date_condition}
                    GROUP BY to_name
                    ORDER BY count DESC
                """, params)
                receivers = {row['to_name']: row['count'] for row in cursor.fetchall()}
                
                cursor.execute(f"""
                    SELECT from_name, COUNT(DISTINCT request_id) as count
                    FROM messages
                    WHERE {place_condition_from} AND {valid_condition}{date_condition}
                    GROUP BY from_name
                    ORDER BY count DESC
                """, params)
                senders = {row['from_name']: row['count'] for row in cursor.fetchall()}
            
            return senders, receivers
    
    def get_communication_network(self, min_count: int = 1, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Get communication edges (from -> to) with counts.
        
        Args:
            min_count: Minimum count threshold
            start_date: Optional start date filter (YYYY-MM-DD format)
            end_date: Optional end date filter (YYYY-MM-DD format)
        
        Returns:
            List of dicts with from_name, to_name, count
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """SELECT from_name, to_name, COUNT(*) as count
                FROM messages
                WHERE from_name NOT IN ('<empty>', 'Not in workflow')
                AND to_name NOT IN ('<empty>', 'Not in workflow')"""
            params = []
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date < ?"
                params.append(end_date)
            query += " GROUP BY from_name, to_name HAVING count >= ? ORDER BY count DESC"
            params.append(min_count)
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_common_subjects(self, limit: int = None, start_date: str = None, end_date: str = None) -> Dict[str, int]:
        """Get most common subjects from requests.
        
        Args:
            limit: Maximum number of subjects to return
            start_date: Optional start date filter (YYYY-MM-DD format)
            end_date: Optional end date filter (YYYY-MM-DD format)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT subject, COUNT(*) as count FROM requests WHERE subject IS NOT NULL AND subject != '<empty>'"
            params = []
            if start_date:
                query += " AND first_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND first_date < ?"
                params.append(end_date)
            query += " GROUP BY subject ORDER BY count DESC"
            if limit:
                query += f" LIMIT {limit}"
            cursor.execute(query, params)
            return {row['subject']: row['count'] for row in cursor.fetchall()}
    
    def get_response_times_data(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Get data needed for response time calculation.
        Returns request_id with all message dates for that request.
        
        Args:
            start_date: Optional start date filter (YYYY-MM-DD format)
            end_date: Optional end date filter (YYYY-MM-DD format)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """SELECT r.hami_id, m.request_id, m.date
                FROM messages m
                JOIN requests r ON m.request_id = r.id
                WHERE m.date != '1500-01-01 00:00:00'"""
            params = []
            if start_date:
                query += " AND m.date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND m.date < ?"
                params.append(end_date)
            query += " ORDER BY m.request_id, m.date"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_students(self) -> List[str]:
        """Get all unique student names from requests table."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT name FROM requests
                WHERE name IS NOT NULL AND name != '<empty>'
            """)
            return [row['name'] for row in cursor.fetchall()]
    
    def get_all_places(self) -> List[str]:
        """Get all unique place names (ending with 4 digits)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT to_name as name FROM messages
                WHERE to_name GLOB '*[0-9][0-9][0-9][0-9]'
                AND to_name NOT IN ('<empty>', 'Not in workflow')
                UNION
                SELECT DISTINCT from_name as name FROM messages
                WHERE from_name GLOB '*[0-9][0-9][0-9][0-9]'
                AND from_name NOT IN ('<empty>', 'Not in workflow')
            """)
            return [row['name'] for row in cursor.fetchall()]
    
    def get_all_employees(self) -> List[str]:
        """Get all unique employee names (non-student emails, not places)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT to_name as name FROM messages
                WHERE NOT (to_email GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]@iau.ir')
                AND NOT (to_name GLOB '*[0-9][0-9][0-9][0-9]')
                AND to_name NOT IN ('<empty>', 'Not in workflow')
            """)
            return [row['name'] for row in cursor.fetchall()]
    
    def get_student_message_counts(self, start_date: str = None, end_date: str = None) -> Dict[str, Dict[str, int]]:
        """
        Get message counts per student (sent and received) based on REQUEST CONTEXT.
        Returns dict with 'sent' and 'received' sub-dicts.
        
        A message is counted as STUDENT SENT when:
        - from_name = request.name (the student is sending on their OWN request)
        
        A message is counted as STUDENT RECEIVED when:
        - to_email matches student pattern (10digits@iau.ir)
        
        Args:
            start_date: Optional start date filter (YYYY-MM-DD format)
            end_date: Optional end date filter (YYYY-MM-DD format)
        """
        places = set(self.get_all_places())
        
        # Build date condition
        date_condition = ""
        params = []
        if start_date:
            date_condition += " AND m.date >= ?"
            params.append(start_date)
        if end_date:
            date_condition += " AND m.date < ?"
            params.append(end_date)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Messages sent by students ON THEIR OWN REQUESTS
            cursor.execute(f"""
                SELECT m.from_name, COUNT(*) as count
                FROM messages m
                JOIN requests r ON m.request_id = r.id
                WHERE m.from_name = r.name
                AND m.from_name NOT IN ('<empty>', 'Not in workflow'){date_condition}
                GROUP BY m.from_name
            """, params)
            sent = {row['from_name']: row['count'] for row in cursor.fetchall() 
                   if row['from_name'] not in places}
            
            # Messages received by students (student email pattern)
            cursor.execute(f"""
                SELECT to_name, COUNT(*) as count
                FROM messages m
                WHERE to_email GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]@iau.ir'
                AND to_name NOT IN ('<empty>', 'Not in workflow'){date_condition}
                GROUP BY to_name
            """, params)
            received = {row['to_name']: row['count'] for row in cursor.fetchall()}
            
            return {'sent': sent, 'received': received}
    
    def get_student_stats_proper(self, by_messages: bool = True, start_date: str = None, end_date: str = None) -> Tuple[Dict[str, int], Dict[str, int]]:
        """
        Get proper student statistics based on REQUEST CONTEXT.
        
        A message is counted as STUDENT SENT when:
        - from_name = request.name (the student is sending on their OWN request)
        
        A message is counted as STUDENT RECEIVED when:
        - to_email matches student pattern (10digits@iau.ir)
        
        This handles the edge case where "حسن نظری" could be both a student 
        (when sending on their own request) and an employee (when sending on 
        other people's requests).
        
        Args:
            by_messages: If True, count messages. If False, count unique requests.
            start_date: Optional start date filter (YYYY-MM-DD format)
            end_date: Optional end date filter (YYYY-MM-DD format)
        
        Returns:
            Tuple of (senders_count, receivers_count) dictionaries
        """
        places = set(self.get_all_places())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            valid_condition = "m.from_name NOT IN ('<empty>', 'Not in workflow') AND m.to_name NOT IN ('<empty>', 'Not in workflow')"
            
            # Build date condition
            date_condition = ""
            params = []
            if start_date:
                date_condition += " AND m.date >= ?"
                params.append(start_date)
            if end_date:
                date_condition += " AND m.date < ?"
                params.append(end_date)
            
            if by_messages:
                # Student senders: from_name = request.name (sending on their OWN request)
                cursor.execute(f"""
                    SELECT m.from_name, COUNT(*) as count
                    FROM messages m
                    JOIN requests r ON m.request_id = r.id
                    WHERE m.from_name = r.name
                    AND {valid_condition}{date_condition}
                    GROUP BY m.from_name
                    ORDER BY count DESC
                """, params)
                senders = {}
                for row in cursor.fetchall():
                    if row['from_name'] not in places:
                        senders[row['from_name']] = row['count']
                
                # Student receivers: to_email matches student pattern
                cursor.execute(f"""
                    SELECT m.to_name, COUNT(*) as count
                    FROM messages m
                    WHERE m.to_email GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]@iau.ir'
                    AND {valid_condition}{date_condition}
                    GROUP BY m.to_name
                    ORDER BY count DESC
                """, params)
                receivers = {row['to_name']: row['count'] for row in cursor.fetchall()}
            else:
                # Count unique requests
                cursor.execute(f"""
                    SELECT m.from_name, COUNT(DISTINCT m.request_id) as count
                    FROM messages m
                    JOIN requests r ON m.request_id = r.id
                    WHERE m.from_name = r.name
                    AND {valid_condition}{date_condition}
                    GROUP BY m.from_name
                    ORDER BY count DESC
                """, params)
                senders = {}
                for row in cursor.fetchall():
                    if row['from_name'] not in places:
                        senders[row['from_name']] = row['count']
                
                cursor.execute(f"""
                    SELECT m.to_name, COUNT(DISTINCT m.request_id) as count
                    FROM messages m
                    WHERE m.to_email GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]@iau.ir'
                    AND {valid_condition}{date_condition}
                    GROUP BY m.to_name
                    ORDER BY count DESC
                """, params)
                receivers = {row['to_name']: row['count'] for row in cursor.fetchall()}
            
            return senders, receivers
    
    def get_employee_stats_proper(self, by_messages: bool = True, start_date: str = None, end_date: str = None) -> Tuple[Dict[str, int], Dict[str, int]]:
        """
        Get proper employee statistics based on REQUEST CONTEXT.
        
        A message is counted as EMPLOYEE SENT when:
        - from_name != request.name (sending on SOMEONE ELSE's request)
        - from_name is not a place (doesn't end with 4 digits)
        
        A message is counted as EMPLOYEE RECEIVED when:
        - to_email does NOT match student pattern
        - to_name is not a place
        
        Args:
            by_messages: If True, count messages. If False, count unique requests.
            start_date: Optional start date filter (YYYY-MM-DD format)
            end_date: Optional end date filter (YYYY-MM-DD format)
        
        Returns:
            Tuple of (senders_count, receivers_count) dictionaries
        """
        places = set(self.get_all_places())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            valid_condition = "m.from_name NOT IN ('<empty>', 'Not in workflow') AND m.to_name NOT IN ('<empty>', 'Not in workflow')"
            place_pattern = "NOT (m.from_name GLOB '*[0-9][0-9][0-9][0-9]')"
            place_pattern_to = "NOT (m.to_name GLOB '*[0-9][0-9][0-9][0-9]')"
            
            # Build date condition
            date_condition = ""
            params = []
            if start_date:
                date_condition += " AND m.date >= ?"
                params.append(start_date)
            if end_date:
                date_condition += " AND m.date < ?"
                params.append(end_date)
            
            if by_messages:
                # Employee senders: from_name != request.name (sending on OTHER's request)
                cursor.execute(f"""
                    SELECT m.from_name, COUNT(*) as count
                    FROM messages m
                    JOIN requests r ON m.request_id = r.id
                    WHERE m.from_name != r.name
                    AND {place_pattern}
                    AND {valid_condition}{date_condition}
                    GROUP BY m.from_name
                    ORDER BY count DESC
                """, params)
                senders = {row['from_name']: row['count'] for row in cursor.fetchall()}
                
                # Employee receivers: to_email does NOT match student pattern, not a place
                cursor.execute(f"""
                    SELECT m.to_name, COUNT(*) as count
                    FROM messages m
                    WHERE NOT (m.to_email GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]@iau.ir')
                    AND {place_pattern_to}
                    AND {valid_condition}{date_condition}
                    GROUP BY m.to_name
                    ORDER BY count DESC
                """, params)
                receivers = {row['to_name']: row['count'] for row in cursor.fetchall()}
            else:
                # Count unique requests
                cursor.execute(f"""
                    SELECT m.from_name, COUNT(DISTINCT m.request_id) as count
                    FROM messages m
                    JOIN requests r ON m.request_id = r.id
                    WHERE m.from_name != r.name
                    AND {place_pattern}
                    AND {valid_condition}{date_condition}
                    GROUP BY m.from_name
                    ORDER BY count DESC
                """, params)
                senders = {row['from_name']: row['count'] for row in cursor.fetchall()}
                
                cursor.execute(f"""
                    SELECT m.to_name, COUNT(DISTINCT m.request_id) as count
                    FROM messages m
                    WHERE NOT (m.to_email GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]@iau.ir')
                    AND {place_pattern_to}
                    AND {valid_condition}{date_condition}
                    GROUP BY m.to_name
                    ORDER BY count DESC
                """, params)
                receivers = {row['to_name']: row['count'] for row in cursor.fetchall()}
            
            return senders, receivers
    
    def get_place_request_details(self) -> List[Dict]:
        """Get place names with their associated request details (field, major, etc.)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT 
                    m.to_name as place_name,
                    r.field,
                    r.major,
                    COUNT(DISTINCT r.id) as request_count
                FROM messages m
                JOIN requests r ON m.request_id = r.id
                WHERE m.to_name GLOB '*[0-9][0-9][0-9][0-9]'
                AND m.to_name NOT IN ('<empty>', 'Not in workflow')
                GROUP BY m.to_name, r.field, r.major
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_requests_count_by_field(self, start_date: str = None, end_date: str = None) -> Dict[str, int]:
        """Get count of all requests grouped by field - uses requests table directly.
        
        Args:
            start_date: Optional start date filter (YYYY-MM-DD format)
            end_date: Optional end date filter (YYYY-MM-DD format)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT field, COUNT(*) as count FROM requests WHERE field IS NOT NULL AND field != '<empty>'"
            params = []
            if start_date:
                query += " AND first_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND first_date < ?"
                params.append(end_date)
            query += " GROUP BY field ORDER BY count DESC"
            cursor.execute(query, params)
            return {row['field']: row['count'] for row in cursor.fetchall()}
    
    def get_requests_count_by_year(self, start_date: str = None, end_date: str = None) -> Dict[str, int]:
        """
        Get count of all requests grouped by year (extracted from field).
        Year is the last 4 digits of the field name.
        
        Args:
            start_date: Optional start date filter (YYYY-MM-DD format)
            end_date: Optional end date filter (YYYY-MM-DD format)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    SUBSTR(field, -4) as year,
                    COUNT(*) as count
                FROM requests
                WHERE field IS NOT NULL 
                AND field != '<empty>'
                AND LENGTH(field) >= 4
                AND SUBSTR(field, -4) GLOB '[0-9][0-9][0-9][0-9]'
            """
            params = []
            if start_date:
                query += " AND first_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND first_date < ?"
                params.append(end_date)
            query += " GROUP BY year ORDER BY count DESC"
            cursor.execute(query, params)
            return {row['year']: row['count'] for row in cursor.fetchall()}
    
    def get_requests_count_by_education_level(self, start_date: str = None, end_date: str = None) -> Dict[str, int]:
        """
        Get count of all requests grouped by education level.
        Education level is extracted from the field name.
        
        Args:
            start_date: Optional start date filter (YYYY-MM-DD format)
            end_date: Optional end date filter (YYYY-MM-DD format)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    CASE 
                        WHEN field LIKE '%کارشناسی ارشد%' THEN 'کارشناسی ارشد'
                        WHEN field LIKE '%کارشناسی پیوسته%' THEN 'کارشناسی پیوسته'
                        WHEN field LIKE '%کارشناسی ناپیوسته%' THEN 'کارشناسی ناپیوسته'
                        WHEN field LIKE '%دکتری%' THEN 'دکتری'
                        WHEN field LIKE '%کاردانی%' THEN 'کاردانی'
                        ELSE 'Other'
                    END as edu_level,
                    COUNT(*) as count
                FROM requests
                WHERE field IS NOT NULL AND field != '<empty>'
            """
            params = []
            if start_date:
                query += " AND first_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND first_date < ?"
                params.append(end_date)
            query += " GROUP BY edu_level ORDER BY count DESC"
            cursor.execute(query, params)
            return {row['edu_level']: row['count'] for row in cursor.fetchall()}

    # ==================== EXPORT FUNCTIONS ====================
    
    def export_request_to_dict(self, request_id: int) -> Optional[Dict]:
        """Export a request and its messages as a dictionary."""
        request = self.get_request(request_id)
        if not request:
            return None
        
        messages = self.get_messages_for_request(request_id)
        return {
            'request': request,
            'messages': messages
        }
    
    def export_hami_to_csv_format(self, hami_id: str) -> List[Dict]:
        """Export hami data in the old CSV format."""
        requests = self.get_requests_by_hami(hami_id)
        return [{
            'number': r['number'],
            'subject': r['subject'],
            'reference_code': r['reference_code'],
            'major': r['major'],
            'name': r['name'],
            'national_id': r['national_id'],
            'student_id': r['student_id'],
            'field': r['field']
        } for r in requests]
    
    def export_combined_to_csv_format(self, hami_id: str, number: int) -> List[Dict]:
        """Export combined data in the old CSV format."""
        messages = self.get_messages_by_hami_number(hami_id, number)
        return [{
            'date': m['date'],
            'message': m['message'],
            'from': m['from_name'],
            'to': m['to_name'],
            'to_email': m['to_email'],
            'from_id': m['from_id'],
            'to_id': m['to_id'],
            'matched': m['matched']
        } for m in messages]


# Convenience function to get database instance
def get_database(db_path: Path = None) -> HamiDatabase:
    """Get a database instance."""
    if db_path is None:
        # Default path
        db_path = Path(__file__).parent / 'database' / 'hami.db'
    return HamiDatabase(db_path)
