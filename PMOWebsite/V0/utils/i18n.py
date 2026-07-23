"""
Translation and Internationalization Utilities

Handles language switching between Persian (FA) and English (EN).
"""

from flask import session, request
from functools import wraps
import jdatetime
from datetime import datetime


# Supported languages
LANGUAGES = {
    'en': 'English',
    'fa': 'فارسی'
}

DEFAULT_LANGUAGE = 'en'


def get_locale():
    """
    Get current language from session or browser.
    
    Returns:
        Language code ('en' or 'fa')
    """
    # Check if language is in session
    if 'language' in session:
        lang = session['language']
        if lang in LANGUAGES:
            return lang
    
    # Check browser's Accept-Language header
    browser_lang = request.accept_languages.best_match(LANGUAGES.keys())
    if browser_lang:
        return browser_lang
    
    # Return default
    return DEFAULT_LANGUAGE


def set_locale(language):
    """
    Set the current language in session.
    
    Args:
        language: Language code ('en' or 'fa')
    """
    if language in LANGUAGES:
        session['language'] = language
        return True
    return False


def get_current_language():
    """Get the current active language code."""
    return get_locale()


def get_direction():
    """
    Get text direction based on current language.
    
    Returns:
        'rtl' for Persian, 'ltr' for English
    """
    lang = get_locale()
    return 'rtl' if lang == 'fa' else 'ltr'


def is_rtl():
    """Check if current language is RTL."""
    return get_direction() == 'rtl'


# Translation dictionary
TRANSLATIONS = {
    'en': {
        # Navigation
        'nav.dashboard': 'Dashboard',
        'nav.admin': 'Admin',
        'nav.settings': 'Settings',
        'nav.logout': 'Logout',
        'nav.projects': 'Projects',
        'nav.forms': 'Forms',
        
        # Login page
        'login.welcome': 'Welcome',
        'login.subtitle': 'Sign in to your PMO account',
        'login.identifier': 'Email or National ID',
        'login.identifier_placeholder': 'admin@company.com or 1234567890',
        'login.password': 'Password',
        'login.password_placeholder': 'Enter your password',
        'login.signin': 'Sign In',
        'login.help': 'Need help?',
        'login.help_text': 'Contact your system administrator.',
        
        # Dashboard
        'dashboard.welcome': 'Welcome back',
        'dashboard.overview': "Here's your dashboard overview",
        'dashboard.my_submissions': 'My Submissions',
        'dashboard.total_projects': 'Total Projects',
        'dashboard.active_projects': 'Active Projects',
        'dashboard.recent_submissions': 'Recent Submissions',
        'dashboard.no_projects': 'No projects available yet.',
        'dashboard.no_submissions': "You haven't submitted any forms yet.",
        'dashboard.start_form': 'Start by selecting a form from the menu.',
        
        # Admin Dashboard
        'admin.title': 'Admin Dashboard',
        'admin.subtitle': 'System overview and analytics',
        'admin.total_users': 'Total Users',
        'admin.total_projects': 'Total Projects',
        'admin.active_projects': 'Active Projects',
        'admin.total_submissions': 'Total Submissions',
        'admin.db_stats': 'Database Statistics',
        'admin.total_nodes': 'Total Nodes',
        'admin.total_edges': 'Total Edges',
        'admin.user_nodes': 'User Nodes',
        'admin.project_nodes': 'Project Nodes',
        'admin.submission_nodes': 'Submission Nodes',
        'admin.recent_submissions': 'Recent Submissions',
        'admin.system_users': 'System Users',
        'admin.analytics': 'Analytics & Visualizations',
        'admin.analytics_placeholder': 'Data visualizations will appear here',
        'admin.analytics_desc': 'Charts and graphs for form submissions, project progress, and user activity',
        'admin.no_submissions': 'No submissions yet.',
        
        # Settings
        'settings.title': 'Settings',
        'settings.subtitle': 'Manage your profile and preferences',
        'settings.profile': 'Profile Information',
        'settings.name': 'Name',
        'settings.email': 'Email',
        'settings.national_id': 'National ID',
        'settings.phone': 'Phone',
        'settings.role': 'Role',
        'settings.change_password': 'Change Password',
        'settings.current_password': 'Current Password',
        'settings.new_password': 'New Password',
        'settings.confirm_password': 'Confirm New Password',
        'settings.update_password': 'Update Password',
        'settings.submission_history': 'My Submission History',
        'settings.no_submissions': 'No submissions yet.',
        
        # Errors
        'error.403.title': 'Access Denied',
        'error.403.message': "You don't have permission to access this page.",
        'error.404.title': 'Page Not Found',
        'error.404.message': "The page you're looking for doesn't exist.",
        'error.500.title': 'Internal Server Error',
        'error.500.message': 'Something went wrong on our end. Please try again later.',
        'error.go_dashboard': 'Go to Dashboard',
        'error.go_login': 'Go to Login',
        
        # Common
        'common.role.admin': 'Admin',
        'common.role.employee': 'Employee',
        'common.status.active': 'Active',
        'common.status.completed': 'Completed',
        'common.status.on-hold': 'On Hold',
        'common.status.cancelled': 'Cancelled',
        'common.submitted': 'Submitted',
        'common.project': 'Project',
        'common.form_type': 'Form Type',
        'common.timestamp': 'Timestamp',
        'common.user': 'User',
        
        # Flash messages
        'flash.login_required': 'Please log in to access this page.',
        'flash.welcome': 'Welcome back',
        'flash.goodbye': 'Goodbye',
        'flash.logout': 'You have been logged out.',
        'flash.invalid_credentials': 'Invalid credentials. Please try again.',
        'flash.password_changed': 'Password updated successfully!',
        'flash.password_change_failed': 'Failed to update password. Please try again.',
        'flash.fields_required': 'All fields are required.',
        'flash.passwords_mismatch': 'New passwords do not match.',
        'flash.wrong_password': 'Current password is incorrect.',
        'flash.access_denied': 'Access denied. This page requires',
        'flash.user_not_found': 'User not found.',
        
        # Forms
        'forms.title': 'Forms',
        'forms.available': 'Available Forms',
        'forms.my_submissions': 'My Submissions',
        'forms.select_project': 'Select Project',
        'forms.submit': 'Submit Form',
        'forms.cancel': 'Cancel',
        'forms.required_field': 'Required',
        'forms.optional_field': 'Optional',
        'forms.no_forms': 'No forms available.',
        'forms.choose_file': 'Choose File',
        'forms.files_selected': 'file(s) selected',
        
        # Messages
        'messages.provide_credentials': 'Please provide both email/national ID and password.',
        'messages.welcome_back': 'Welcome back, {name}!',
        'messages.invalid_credentials': 'Invalid credentials. Please try again.',
        'messages.goodbye': 'Goodbye, {name}! You have been logged out.',
        'messages.user_not_found': 'User not found.',
        'messages.all_fields_required': 'All fields are required.',
        'messages.passwords_not_match': 'New passwords do not match.',
        'messages.current_password_incorrect': 'Current password is incorrect.',
        'messages.password_updated': 'Password updated successfully!',
        'messages.password_update_failed': 'Failed to update password. Please try again.',
        'messages.form_not_found': 'Form not found.',
        'messages.form_access_denied': 'You do not have permission to access this form.',
        'messages.project_required': 'Please select a project.',
        'messages.form_submitted_success': 'Form submitted successfully!',
        'messages.form_submit_failed': 'Failed to submit form. Please try again.',
        
        # Footer
        'footer.copyright': 'All rights reserved.',
    },
    'fa': {
        # Navigation
        'nav.dashboard': 'داشبورد',
        'nav.admin': 'مدیریت',
        'nav.settings': 'تنظیمات',
        'nav.logout': 'خروج',
        'nav.projects': 'پروژه‌ها',
        'nav.forms': 'فرم‌ها',
        
        # Login page
        'login.welcome': 'خوش آمدید',
        'login.subtitle': 'ورود به حساب کاربری PMO',
        'login.identifier': 'ایمیل یا کد ملی',
        'login.identifier_placeholder': 'admin@company.com یا ۱۲۳۴۵۶۷۸۹۰',
        'login.password': 'رمز عبور',
        'login.password_placeholder': 'رمز عبور خود را وارد کنید',
        'login.signin': 'ورود',
        'login.help': 'نیاز به کمک دارید؟',
        'login.help_text': 'با مدیر سیستم تماس بگیرید.',
        
        # Dashboard
        'dashboard.welcome': 'خوش آمدید',
        'dashboard.overview': 'نمای کلی داشبورد شما',
        'dashboard.my_submissions': 'ارسال‌های من',
        'dashboard.total_projects': 'کل پروژه‌ها',
        'dashboard.active_projects': 'پروژه‌های فعال',
        'dashboard.recent_submissions': 'ارسال‌های اخیر',
        'dashboard.no_projects': 'هنوز پروژه‌ای موجود نیست.',
        'dashboard.no_submissions': 'هنوز فرمی ارسال نکرده‌اید.',
        'dashboard.start_form': 'با انتخاب یک فرم از منو شروع کنید.',
        
        # Admin Dashboard
        'admin.title': 'داشبورد مدیریت',
        'admin.subtitle': 'نمای کلی سیستم و تحلیل‌ها',
        'admin.total_users': 'کل کاربران',
        'admin.total_projects': 'کل پروژه‌ها',
        'admin.active_projects': 'پروژه‌های فعال',
        'admin.total_submissions': 'کل ارسال‌ها',
        'admin.db_stats': 'آمار پایگاه داده',
        'admin.total_nodes': 'کل گره‌ها',
        'admin.total_edges': 'کل یال‌ها',
        'admin.user_nodes': 'گره‌های کاربر',
        'admin.project_nodes': 'گره‌های پروژه',
        'admin.submission_nodes': 'گره‌های ارسال',
        'admin.recent_submissions': 'ارسال‌های اخیر',
        'admin.system_users': 'کاربران سیستم',
        'admin.analytics': 'تحلیل‌ها و نمودارها',
        'admin.analytics_placeholder': 'نمودارهای داده در اینجا نمایش داده می‌شوند',
        'admin.analytics_desc': 'نمودارها و گراف‌ها برای ارسال فرم‌ها، پیشرفت پروژه‌ها و فعالیت کاربران',
        'admin.no_submissions': 'هنوز ارسالی وجود ندارد.',
        
        # Settings
        'settings.title': 'تنظیمات',
        'settings.subtitle': 'مدیریت پروفایل و تنظیمات شما',
        'settings.profile': 'اطلاعات پروفایل',
        'settings.name': 'نام',
        'settings.email': 'ایمیل',
        'settings.national_id': 'کد ملی',
        'settings.phone': 'تلفن',
        'settings.role': 'نقش',
        'settings.change_password': 'تغییر رمز عبور',
        'settings.current_password': 'رمز عبور فعلی',
        'settings.new_password': 'رمز عبور جدید',
        'settings.confirm_password': 'تکرار رمز عبور جدید',
        'settings.update_password': 'به‌روزرسانی رمز عبور',
        'settings.submission_history': 'تاریخچه ارسال‌های من',
        'settings.no_submissions': 'هنوز ارسالی وجود ندارد.',
        
        # Errors
        'error.403.title': 'دسترسی رد شد',
        'error.403.message': 'شما اجازه دسترسی به این صفحه را ندارید.',
        'error.404.title': 'صفحه یافت نشد',
        'error.404.message': 'صفحه‌ای که به دنبال آن هستید وجود ندارد.',
        'error.500.title': 'خطای سرور',
        'error.500.message': 'مشکلی از سمت ما پیش آمده است. لطفاً بعداً دوباره تلاش کنید.',
        'error.go_dashboard': 'برو به داشبورد',
        'error.go_login': 'برو به صفحه ورود',
        
        # Common
        'common.role.admin': 'مدیر',
        'common.role.employee': 'کارمند',
        'common.status.active': 'فعال',
        'common.status.completed': 'تکمیل شده',
        'common.status.on-hold': 'در انتظار',
        'common.status.cancelled': 'لغو شده',
        'common.submitted': 'ارسال شده',
        'common.project': 'پروژه',
        'common.form_type': 'نوع فرم',
        'common.timestamp': 'زمان',
        'common.user': 'کاربر',
        
        # Flash messages
        'flash.login_required': 'لطفاً برای دسترسی به این صفحه وارد شوید.',
        'flash.welcome': 'خوش آمدید',
        'flash.goodbye': 'خداحافظ',
        'flash.logout': 'شما از سیستم خارج شدید.',
        'flash.invalid_credentials': 'اطلاعات ورود نامعتبر است. لطفاً دوباره تلاش کنید.',
        'flash.password_changed': 'رمز عبور با موفقیت به‌روزرسانی شد!',
        'flash.password_change_failed': 'به‌روزرسانی رمز عبور انجام نشد. لطفاً دوباره تلاش کنید.',
        'flash.fields_required': 'تمام فیلدها الزامی هستند.',
        'flash.passwords_mismatch': 'رمزهای عبور جدید مطابقت ندارند.',
        'flash.wrong_password': 'رمز عبور فعلی اشتباه است.',
        'flash.access_denied': 'دسترسی رد شد. این صفحه نیاز به نقش',
        'flash.user_not_found': 'کاربر یافت نشد.',
        
        # Forms
        'forms.title': 'فرم‌ها',
        'forms.available': 'فرم‌های موجود',
        'forms.my_submissions': 'ارسال‌های من',
        'forms.select_project': 'انتخاب پروژه',
        'forms.submit': 'ارسال فرم',
        'forms.cancel': 'لغو',
        'forms.required_field': 'الزامی',
        'forms.optional_field': 'اختیاری',
        'forms.no_forms': 'فرمی موجود نیست.',
        'forms.choose_file': 'انتخاب فایل',
        'forms.files_selected': 'فایل انتخاب شده',
        
        # Messages
        'messages.provide_credentials': 'لطفاً ایمیل/کد ملی و رمز عبور را وارد کنید.',
        'messages.welcome_back': 'خوش آمدید، {name}!',
        'messages.invalid_credentials': 'اطلاعات ورود نامعتبر است. لطفاً دوباره تلاش کنید.',
        'messages.goodbye': 'خداحافظ، {name}! شما از سیستم خارج شدید.',
        'messages.user_not_found': 'کاربر یافت نشد.',
        'messages.all_fields_required': 'تمام فیلدها الزامی هستند.',
        'messages.passwords_not_match': 'رمزهای عبور جدید مطابقت ندارند.',
        'messages.current_password_incorrect': 'رمز عبور فعلی اشتباه است.',
        'messages.password_updated': 'رمز عبور با موفقیت به‌روزرسانی شد!',
        'messages.password_update_failed': 'به‌روزرسانی رمز عبور انجام نشد. لطفاً دوباره تلاش کنید.',
        'messages.form_not_found': 'فرم یافت نشد.',
        'messages.form_access_denied': 'شما اجازه دسترسی به این فرم را ندارید.',
        'messages.project_required': 'لطفاً یک پروژه انتخاب کنید.',
        'messages.form_submitted_success': 'فرم با موفقیت ارسال شد!',
        'messages.form_submit_failed': 'ارسال فرم انجام نشد. لطفاً دوباره تلاش کنید.',
        
        # Footer
        'footer.copyright': 'تمامی حقوق محفوظ است.',
    }
}


def translate(key, **kwargs):
    """
    Translate a key to the current language.
    
    Args:
        key: Translation key (e.g., 'login.welcome')
        **kwargs: Optional format arguments
    
    Returns:
        Translated string
    """
    lang = get_locale()
    translations = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    text = translations.get(key, key)
    
    # Format if kwargs provided
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    
    return text


# Shorthand alias
_ = translate


def format_date(date_obj, include_time=False):
    """
    Format date according to current language.
    
    Args:
        date_obj: datetime object or ISO string
        include_time: Whether to include time
    
    Returns:
        Formatted date string
    """
    # Convert string to datetime if needed
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.fromisoformat(date_obj)
        except (ValueError, TypeError):
            return date_obj
    
    if not isinstance(date_obj, datetime):
        return str(date_obj)
    
    lang = get_locale()
    
    if lang == 'fa':
        # Convert to Jalali (Shamsi) calendar
        j_date = jdatetime.datetime.fromgregorian(datetime=date_obj)
        if include_time:
            return j_date.strftime('%Y/%m/%d %H:%M:%S')
        else:
            return j_date.strftime('%Y/%m/%d')
    else:
        # English (Gregorian)
        if include_time:
            return date_obj.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return date_obj.strftime('%Y-%m-%d')


def format_number(number):
    """
    Format number according to current language.
    
    Args:
        number: Number to format
    
    Returns:
        Formatted number string
    """
    lang = get_locale()
    
    if lang == 'fa':
        # Convert to Persian digits
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'
        trans_table = str.maketrans(english_digits, persian_digits)
        return str(number).translate(trans_table)
    else:
        return str(number)
