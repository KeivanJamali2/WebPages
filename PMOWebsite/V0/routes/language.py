"""
Language Routes

Handles language switching between Persian and English.
"""

from flask import Blueprint, redirect, request, url_for
from utils.i18n import set_locale

# Create blueprint
language_bp = Blueprint('language', __name__, url_prefix='/language')


@language_bp.route('/switch/<lang>')
def switch_language(lang):
    """
    Switch the current language.
    
    Args:
        lang: Language code ('en' or 'fa')
    """
    set_locale(lang)
    
    # Redirect back to referring page or dashboard
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    else:
        return redirect(url_for('dashboard.home'))
