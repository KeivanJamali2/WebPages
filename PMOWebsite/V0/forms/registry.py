"""
Form Registry

Automatically discovers and manages all available forms.
Forms are loaded from the forms/examples/ directory.
"""

import os
import importlib
import inspect
from typing import Dict, List, Optional, Type
from forms.base_form import BaseForm


class FormRegistry:
    """
    Registry for managing all available forms.
    Auto-discovers forms from the examples directory.
    """
    
    def __init__(self, forms_directory: str = None):
        """
        Initialize the form registry.
        
        Args:
            forms_directory: Path to directory containing form modules
        """
        self._forms: Dict[str, Type[BaseForm]] = {}
        self._forms_directory = forms_directory or self._get_default_directory()
        self._discover_forms()
    
    def _get_default_directory(self) -> str:
        """Get the default forms directory path."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, 'examples')
    
    def _discover_forms(self):
        """
        Automatically discover and register all forms in the examples directory.
        """
        if not os.path.exists(self._forms_directory):
            print(f"[FormRegistry] Warning: Forms directory not found: {self._forms_directory}")
            return
        
        # Get all Python files in the directory
        for filename in os.listdir(self._forms_directory):
            if filename.endswith('.py') and not filename.startswith('_'):
                module_name = filename[:-3]  # Remove .py extension
                self._load_form_module(module_name)
        
        print(f"[FormRegistry] Discovered {len(self._forms)} forms: {list(self._forms.keys())}")
    
    def _load_form_module(self, module_name: str):
        """
        Load a form module and register any BaseForm subclasses found.
        
        Args:
            module_name: Name of the module to load (without .py)
        """
        try:
            # Import the module
            module_path = f"forms.examples.{module_name}"
            module = importlib.import_module(module_path)
            
            # Find all BaseForm subclasses in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Check if it's a subclass of BaseForm (but not BaseForm itself)
                if issubclass(obj, BaseForm) and obj is not BaseForm:
                    try:
                        # Try to instantiate to validate configuration
                        form_instance = obj()
                        form_id = form_instance.form_id
                        
                        # Register the form class
                        self._forms[form_id] = obj
                        print(f"[FormRegistry] Registered form: {form_id} ({obj.__name__})")
                    
                    except Exception as e:
                        print(f"[FormRegistry] Warning: Failed to register form {name}: {e}")
        
        except ImportError as e:
            print(f"[FormRegistry] Warning: Failed to import module {module_name}: {e}")
        except Exception as e:
            print(f"[FormRegistry] Warning: Error loading module {module_name}: {e}")
    
    def register_form(self, form_class: Type[BaseForm]):
        """
        Manually register a form class.
        
        Args:
            form_class: Form class to register
        """
        try:
            form_instance = form_class()
            form_id = form_instance.form_id
            self._forms[form_id] = form_class
            print(f"[FormRegistry] Manually registered form: {form_id}")
        except Exception as e:
            print(f"[FormRegistry] Warning: Failed to register form {form_class.__name__}: {e}")
    
    def get_form(self, form_id: str) -> Optional[Type[BaseForm]]:
        """
        Get a form class by its ID.
        
        Args:
            form_id: Form identifier
        
        Returns:
            Form class or None if not found
        """
        return self._forms.get(form_id)
    
    def get_all_forms(self, user_role: str = None) -> List[Type[BaseForm]]:
        """
        Get all registered forms, optionally filtered by user role.
        
        Args:
            user_role: Optional role to filter forms by access
        
        Returns:
            List of form classes
        """
        if user_role:
            return [
                form_class for form_class in self._forms.values()
                if form_class.can_access(user_role)
            ]
        
        return list(self._forms.values())
    
    def get_form_list(self, user_role: str = None, locale: str = 'en') -> List[Dict]:
        """
        Get a list of form metadata for display.
        
        Args:
            user_role: Optional role to filter forms
            locale: Language for translations
        
        Returns:
            List of dictionaries with form metadata
        """
        forms = self.get_all_forms(user_role)
        
        return [
            {
                'form_id': form_class.form_id,
                'title': form_class.get_form_title(locale),
                'icon': form_class.icon,
                'requires_project': form_class.requires_project,
            }
            for form_class in forms
        ]
    
    def create_form_instance(self, form_id: str) -> Optional[BaseForm]:
        """
        Create an instance of a form by its ID.
        
        Args:
            form_id: Form identifier
        
        Returns:
            Form instance or None if not found
        """
        form_class = self.get_form(form_id)
        
        if form_class:
            try:
                return form_class()
            except Exception as e:
                print(f"[FormRegistry] Error creating form instance for {form_id}: {e}")
                return None
        
        return None
    
    def get_form_count(self) -> int:
        """Get the total number of registered forms."""
        return len(self._forms)
    
    def reload_forms(self):
        """Reload all forms from the directory."""
        self._forms.clear()
        self._discover_forms()


# Global form registry instance
_registry = None


def get_registry() -> FormRegistry:
    """
    Get the global form registry instance.
    Creates it if it doesn't exist.
    
    Returns:
        FormRegistry instance
    """
    global _registry
    
    if _registry is None:
        _registry = FormRegistry()
    
    return _registry


def reload_registry():
    """Reload the global form registry."""
    global _registry
    
    if _registry:
        _registry.reload_forms()
    else:
        _registry = FormRegistry()
