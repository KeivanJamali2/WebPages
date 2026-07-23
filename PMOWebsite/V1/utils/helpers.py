"""
Helper utilities for the application.
"""
from datetime import datetime, date, timedelta
from flask import session
import jdatetime


def get_current_user():
    """Get current logged-in user from session."""
    return session.get('user', None)


def get_jalali_date(gregorian_date=None):
    """Convert Gregorian date to Jalali (Persian) date."""
    if gregorian_date is None:
        gregorian_date = date.today()
    elif isinstance(gregorian_date, str):
        gregorian_date = datetime.strptime(gregorian_date, '%Y-%m-%d').date()
    
    jalali = jdatetime.date.fromgregorian(date=gregorian_date)
    return jalali.strftime('%Y-%m-%d')


def get_jalali_datetime(gregorian_datetime=None):
    """Convert Gregorian datetime to Jalali datetime."""
    if gregorian_datetime is None:
        gregorian_datetime = datetime.now()
    
    jalali = jdatetime.datetime.fromgregorian(datetime=gregorian_datetime)
    return jalali.strftime('%Y-%m-%d %H:%M')


def format_date(date_obj, lang='en'):
    """Format date based on language - always show Jalali."""
    if date_obj is None:
        return ''
    
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        except ValueError:
            return date_obj
    
    # Always return Jalali date since company is in Iran
    return get_jalali_date(date_obj)


def format_datetime(datetime_obj, lang='en'):
    """Format datetime based on language - always show Jalali."""
    if datetime_obj is None:
        return ''
    
    if isinstance(datetime_obj, str):
        try:
            datetime_obj = datetime.strptime(datetime_obj, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return datetime_obj
    
    # Always return Jalali datetime since company is in Iran
    return get_jalali_datetime(datetime_obj)


def get_day_of_week(date_obj=None, lang='fa'):
    """Get day of week name (Persian by default)."""
    if date_obj is None:
        date_obj = date.today()
    
    # Persian weekday based on jdatetime (Saturday=0)
    jalali_date = jdatetime.date.fromgregorian(date=date_obj)
    weekday = jalali_date.weekday()
    
    days_fa = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']
    days_en = ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    if lang == 'fa':
        return days_fa[weekday]
    return days_en[weekday]


def generate_document_code(project_code, date_obj, sequence=1):
    """Generate a unique document code for forms using Jalali date."""
    if isinstance(date_obj, str):
        # Assume it's already a date string
        date_str = date_obj.replace('-', '')
    else:
        # Convert to Jalali and format
        jalali_date = jdatetime.date.fromgregorian(date=date_obj)
        date_str = jalali_date.strftime('%Y%m%d')
    
    return f"{project_code}-{date_str}-{sequence:03d}"


def parse_jalali_date(jalali_str):
    """Parse Jalali date string to Gregorian date."""
    try:
        # Handle both '-' and '/' separators
        jalali_str = jalali_str.replace('/', '-')
        parts = jalali_str.split('-')
        if len(parts) == 3:
            jalali_date = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
            return jalali_date.togregorian()
    except:
        pass
    return None


def get_today_jalali():
    """Get today's date as Jalali string."""
    return jdatetime.date.today().strftime('%Y-%m-%d')


def get_week_range(date_obj=None):
    """Get start and end of week for a given date (Saturday-based)."""
    if date_obj is None:
        date_obj = date.today()
    
    # Week starts on Saturday (Persian calendar)
    days_since_saturday = (date_obj.weekday() + 2) % 7
    week_start = date_obj - timedelta(days=days_since_saturday)
    week_end = week_start + timedelta(days=6)
    
    return week_start, week_end


def get_month_range(date_obj=None):
    """Get start and end of month for a given date."""
    if date_obj is None:
        date_obj = date.today()
    
    month_start = date_obj.replace(day=1)
    
    # Get last day of month
    if date_obj.month == 12:
        month_end = date_obj.replace(day=31)
    else:
        next_month = date_obj.replace(month=date_obj.month + 1, day=1)
        month_end = next_month - timedelta(days=1)
    
    return month_start, month_end


def safe_int(value, default=0):
    """Safely convert value to int."""
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """Safely convert value to float."""
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default


def paginate(query, page, per_page=20):
    """Paginate a SQLAlchemy query."""
    return query.paginate(page=page, per_page=per_page, error_out=False)
