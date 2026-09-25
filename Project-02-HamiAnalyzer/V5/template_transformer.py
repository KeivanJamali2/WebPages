"""
Template Transformer Module
Converts raw/uncleaned template data into the correct workflow format
without modifying any existing methods or system logic.
"""

import re
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class TemplateTransformer:
    """
    Transforms raw template data into standardized workflow format.
    
    Raw format (uncleaned):
        name1
        email1
        date1
        major_info
        recipient_email
        مشاهده محتوای ایمیل
        mail
        date2
        name2
        email2
        [more entries...]
    
    Output format (standardized):
        parent_id: None/1/2/...
        id: 1/2/3/...
        date: [persian date]
        name: [person name]
        email: [person email]
        --------------------------------------------------
    """
    
    # Lines to ignore (noise)
    IGNORE_LINES = {
        'مشاهده محتوای ایمیل',
        'mail',
        'mail_',
        'مشاهده محتوای ایمیل ',
        'mail '
    }
    
    def __init__(self):
        self.entries = []
        self.errors = []
    
    def transform(self, raw_text: str) -> Dict:
        """
        Main transformation method.
        
        Args:
            raw_text: Raw template text with uncleaned data
            
        Returns:
            Dict with:
                - 'success': bool
                - 'formatted_text': str (ready to use)
                - 'entries': List[Dict] (parsed entries)
                - 'errors': List[str] (parsing errors, if any)
        """
        self.entries = []
        self.errors = []
        
        # Clean and split lines
        lines = self._clean_lines(raw_text)
        
        if not lines:
            return {
                'success': False,
                'formatted_text': '',
                'entries': [],
                'errors': ['No valid lines found in template']
            }
        
        # Extract entries (skip first 2 lines)
        if len(lines) > 2:
            lines = lines[2:]
        
        # Remove noise lines and group remaining lines into triples
        filtered_lines = self._filter_noise_lines(lines)
        
        # Parse triples: date, name, email
        parsed_entries = self._parse_triples(filtered_lines)
        
        if not parsed_entries:
            return {
                'success': False,
                'formatted_text': '',
                'entries': [],
                'errors': self.errors if self.errors else ['Could not parse any valid entries']
            }
        
        # Validate entries
        valid_entries = self._validate_entries(parsed_entries)
        
        if not valid_entries:
            return {
                'success': False,
                'formatted_text': '',
                'entries': [],
                'errors': self.errors if self.errors else ['All entries failed validation']
            }
        
        # Assign IDs and create parent-child chain
        workflow_entries = self._assign_ids(valid_entries)
        
        # Format to standard workflow text
        formatted_text = self._format_workflow_text(workflow_entries)
        
        return {
            'success': True,
            'formatted_text': formatted_text,
            'entries': workflow_entries,
            'errors': self.errors if self.errors else []
        }
    
    def _clean_lines(self, text: str) -> List[str]:
        """Remove empty lines and strip whitespace."""
        lines = []
        for line in text.split('\n'):
            stripped = line.strip()
            if stripped:  # Only keep non-empty lines
                lines.append(stripped)
        return lines
    
    def _filter_noise_lines(self, lines: List[str]) -> List[str]:
        """Remove known noise lines like 'مشاهده محتوای ایمیل' and 'mail'."""
        filtered = []
        for line in lines:
            # Check if line is in ignore list (exact match or startswith)
            is_noise = False
            for ignore_pattern in self.IGNORE_LINES:
                if line == ignore_pattern or line.startswith(ignore_pattern):
                    is_noise = True
                    break
            
            if not is_noise:
                filtered.append(line)
        
        return filtered
    
    def _parse_triples(self, lines: List[str]) -> List[Dict]:
        """
        Parse lines into triples: (date, name, email)
        
        Pattern: after filtering noise, every 3 consecutive lines form an entry:
        Line 0: DATE (Persian date format)
        Line 1: NAME (person name - can be in Persian or English)
        Line 2: EMAIL (email address)
        """
        triples = []
        
        # Process in groups of 3
        for i in range(0, len(lines), 3):
            if i + 2 >= len(lines):
                # Not enough lines for a complete triple
                if i < len(lines):
                    remaining = len(lines) - i
                    self.errors.append(
                        f"Incomplete entry at line {i}: expected 3 lines, got {remaining}"
                    )
                break
            
            date_line = lines[i]
            name_line = lines[i + 1]
            email_line = lines[i + 2]
            
            # Validate date format (Persian date)
            if not self._is_valid_date(date_line):
                self.errors.append(
                    f"Invalid date format at position {i}: '{date_line}'"
                )
                continue
            
            # Validate email format
            if not self._is_valid_email(email_line):
                self.errors.append(
                    f"Invalid email format at position {i+2}: '{email_line}'"
                )
                continue
            
            triples.append({
                'date': date_line,
                'name': name_line,
                'email': email_line
            })
        
        return triples
    
    def _is_valid_date(self, date_str: str) -> bool:
        """
        Check if string looks like a Persian date.
        Pattern: [day name], [day] [month name] [year] [time]
        Example: دوشنبه، 7 اردیبهشت 1405 10:26
        """
        # Basic check: contains Persian digits or Persian text + numbers + colon
        has_persian = any('\u0600' <= c <= '\u06FF' for c in date_str)
        has_time = ':' in date_str
        has_numbers = any(c.isdigit() for c in date_str)
        
        return has_persian and has_time and has_numbers
    
    def _is_valid_email(self, email_str: str) -> bool:
        """Check if string looks like an email."""
        # Simple regex for email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email_str) is not None
    
    def _validate_entries(self, entries: List[Dict]) -> List[Dict]:
        """Validate all entries and filter out invalid ones."""
        valid = []
        
        for i, entry in enumerate(entries):
            # All required fields must be present and non-empty
            if (entry.get('date') and 
                entry.get('name') and 
                entry.get('email')):
                valid.append(entry)
            else:
                self.errors.append(
                    f"Entry {i+1} missing required fields: {entry}"
                )
        
        return valid
    
    def _assign_ids(self, entries: List[Dict]) -> List[Dict]:
        """
        Assign sequential IDs and create parent-child chain.
        ID 1 has parent_id: None
        ID 2 has parent_id: 1
        ID 3 has parent_id: 2, etc.
        """
        result = []
        
        for idx, entry in enumerate(entries, start=1):
            parent_id = None if idx == 1 else idx - 1
            
            result.append({
                'parent_id': parent_id,
                'id': idx,
                'date': entry['date'],
                'name': entry['name'],
                'email': entry['email']
            })
        
        return result
    
    def _format_workflow_text(self, entries: List[Dict]) -> str:
        """Format entries into standard workflow text format."""
        lines = []
        
        for entry in entries:
            parent_id_str = "None" if entry['parent_id'] is None else str(entry['parent_id'])
            
            lines.append(f"parent_id: {parent_id_str}")
            lines.append(f"id: {entry['id']}")
            lines.append(f"date: {entry['date']}")
            lines.append(f"name: {entry['name']}")
            lines.append(f"email: {entry['email']}")
            lines.append("-" * 50)
        
        return "\n".join(lines)


def transform_raw_template(raw_text: str) -> Dict:
    """
    Convenience function to transform raw template data.
    
    Usage:
        result = transform_raw_template(raw_template_text)
        if result['success']:
            formatted_workflow = result['formatted_text']
            # Pass to existing parse_workflow_text() function
        else:
            print(result['errors'])
    
    Args:
        raw_text: Raw template data
        
    Returns:
        Dict with 'success', 'formatted_text', 'entries', 'errors'
    """
    transformer = TemplateTransformer()
    return transformer.transform(raw_text)
