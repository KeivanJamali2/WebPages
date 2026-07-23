"""
Forms Package

Provides a simple, declarative form system for the PMO Website.
"""

from forms.base_form import BaseForm
from forms.registry import FormRegistry, get_registry, reload_registry

__all__ = [
    'BaseForm',
    'FormRegistry',
    'get_registry',
    'reload_registry',
]
