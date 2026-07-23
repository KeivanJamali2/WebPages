"""
Jalali (Persian/Shamsi) date utilities.
Uses jdatetime for Persian calendar support.
"""
import jdatetime
from datetime import datetime, date

# Persian weekday names
PERSIAN_WEEKDAYS = {
    0: 'شنبه',
    1: 'یکشنبه',
    2: 'دوشنبه',
    3: 'سه‌شنبه',
    4: 'چهارشنبه',
    5: 'پنج‌شنبه',
    6: 'جمعه'
}

ENGLISH_WEEKDAYS = {
    0: 'Saturday',
    1: 'Sunday',
    2: 'Monday',
    3: 'Tuesday',
    4: 'Wednesday',
    5: 'Thursday',
    6: 'Friday'
}

# Persian month names
PERSIAN_MONTHS = {
    1: 'فروردین',
    2: 'اردیبهشت',
    3: 'خرداد',
    4: 'تیر',
    5: 'مرداد',
    6: 'شهریور',
    7: 'مهر',
    8: 'آبان',
    9: 'آذر',
    10: 'دی',
    11: 'بهمن',
    12: 'اسفند'
}


def gregorian_to_jalali(g_date):
    """
    Convert Gregorian date to Jalali date.
    
    Args:
        g_date: datetime.date or datetime.datetime object
        
    Returns:
        jdatetime.date object
    """
    if g_date is None:
        return None
    
    if isinstance(g_date, datetime):
        g_date = g_date.date()
    
    return jdatetime.date.fromgregorian(date=g_date)


def jalali_to_gregorian(j_date):
    """
    Convert Jalali date to Gregorian date.
    
    Args:
        j_date: jdatetime.date object or string in format 'YYYY-MM-DD'
        
    Returns:
        datetime.date object
    """
    if j_date is None:
        return None
    
    if isinstance(j_date, str):
        parts = j_date.split('-')
        j_date = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
    
    return j_date.togregorian()


def get_today_jalali():
    """Get today's date in Jalali calendar."""
    return jdatetime.date.today()


def get_now_jalali():
    """Get current datetime in Jalali calendar."""
    return jdatetime.datetime.now()


def format_jalali_date(g_date, format_str='%Y/%m/%d'):
    """
    Format a Gregorian date as Jalali string.
    
    Args:
        g_date: datetime.date or datetime.datetime object
        format_str: strftime format string (default: YYYY/MM/DD)
        
    Returns:
        Formatted Jalali date string
    """
    if g_date is None:
        return ''
    
    j_date = gregorian_to_jalali(g_date)
    return j_date.strftime(format_str)


def format_jalali_datetime(g_datetime, format_str='%Y/%m/%d %H:%M'):
    """
    Format a Gregorian datetime as Jalali string with time.
    
    Args:
        g_datetime: datetime.datetime object
        format_str: strftime format string
        
    Returns:
        Formatted Jalali datetime string
    """
    if g_datetime is None:
        return ''
    
    j_datetime = jdatetime.datetime.fromgregorian(datetime=g_datetime)
    return j_datetime.strftime(format_str)


def get_jalali_weekday(g_date, lang='fa'):
    """
    Get weekday name for a date.
    
    Args:
        g_date: datetime.date object
        lang: 'fa' for Persian, 'en' for English
        
    Returns:
        Weekday name string
    """
    if g_date is None:
        return ''
    
    j_date = gregorian_to_jalali(g_date)
    weekday_num = j_date.weekday()  # 0=Saturday in jdatetime
    
    if lang == 'fa':
        return PERSIAN_WEEKDAYS.get(weekday_num, '')
    return ENGLISH_WEEKDAYS.get(weekday_num, '')


def get_jalali_month_name(month_num):
    """Get Persian name of a Jalali month."""
    return PERSIAN_MONTHS.get(month_num, '')


def parse_jalali_date(date_str):
    """
    Parse a Jalali date string to jdatetime.date.
    
    Args:
        date_str: String in format 'YYYY-MM-DD' or 'YYYY/MM/DD'
        
    Returns:
        jdatetime.date object
    """
    if not date_str:
        return None
    
    # Handle both separators
    date_str = date_str.replace('/', '-')
    parts = date_str.split('-')
    
    if len(parts) != 3:
        raise ValueError(f"Invalid date format: {date_str}")
    
    return jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))


def jalali_date_to_string(j_date, separator='-'):
    """
    Convert jdatetime.date to string.
    
    Args:
        j_date: jdatetime.date object
        separator: Date separator (default: '-')
        
    Returns:
        String in format 'YYYY-MM-DD'
    """
    if j_date is None:
        return ''
    
    return f"{j_date.year:04d}{separator}{j_date.month:02d}{separator}{j_date.day:02d}"


def get_jalali_date_range(days_ago=30):
    """
    Get a date range for filtering (last N days).
    
    Args:
        days_ago: Number of days to go back
        
    Returns:
        Tuple of (from_date, to_date) as Gregorian dates
    """
    today = date.today()
    from_date = today - jdatetime.timedelta(days=days_ago)
    return (from_date, today)


def format_relative_time(g_datetime, lang='fa'):
    """
    Format datetime as relative time (e.g., "2 hours ago").
    
    Args:
        g_datetime: datetime.datetime object
        lang: 'fa' for Persian, 'en' for English
        
    Returns:
        Relative time string
    """
    if g_datetime is None:
        return ''
    
    now = datetime.utcnow()
    diff = now - g_datetime
    
    seconds = diff.total_seconds()
    
    if lang == 'fa':
        if seconds < 60:
            return 'همین الان'
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f'{minutes} دقیقه پیش'
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f'{hours} ساعت پیش'
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f'{days} روز پیش'
        else:
            return format_jalali_datetime(g_datetime, '%Y/%m/%d')
    else:
        if seconds < 60:
            return 'just now'
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f'{hours} hour{"s" if hours > 1 else ""} ago'
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f'{days} day{"s" if days > 1 else ""} ago'
        else:
            return format_jalali_datetime(g_datetime, '%Y/%m/%d')


# Jinja2 filters for templates
def register_jalali_filters(app):
    """Register Jalali date filters with Flask app."""
    
    @app.template_filter('jalali')
    def jalali_filter(g_date, format_str='%Y/%m/%d'):
        """Convert date to Jalali format in templates."""
        return format_jalali_date(g_date, format_str)
    
    @app.template_filter('jalali_datetime')
    def jalali_datetime_filter(g_datetime, format_str='%Y/%m/%d %H:%M'):
        """Convert datetime to Jalali format in templates."""
        return format_jalali_datetime(g_datetime, format_str)
    
    @app.template_filter('jalali_weekday')
    def jalali_weekday_filter(g_date, lang='fa'):
        """Get weekday name in templates."""
        return get_jalali_weekday(g_date, lang)
    
    @app.template_filter('relative_time')
    def relative_time_filter(g_datetime, lang='fa'):
        """Format as relative time in templates."""
        return format_relative_time(g_datetime, lang)
    
    @app.template_global('today_jalali')
    def today_jalali_global():
        """Get today's Jalali date as string."""
        return jalali_date_to_string(get_today_jalali())
    
    @app.template_global('now_jalali')
    def now_jalali_global():
        """Get current Jalali datetime."""
        return get_now_jalali()
