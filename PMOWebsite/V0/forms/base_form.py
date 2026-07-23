"""
Base Form System

Provides a simple, declarative way to create forms with minimal code.
Each form is a Python class with field definitions.

Example Usage:
    class MyForm(BaseForm):
        form_id = "my_form"
        title = {"en": "My Form", "fa": "فرم من"}
        description = {"en": "A simple form", "fa": "یک فرم ساده"}
        
        fields = [
            {
                "name": "full_name",
                "type": "text",
                "label": {"en": "Full Name", "fa": "نام کامل"},
                "required": True
            },
            {
                "name": "age",
                "type": "number",
                "label": {"en": "Age", "fa": "سن"},
                "required": False
            }
        ]
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseForm(ABC):
    """
    Abstract base class for all forms.
    
    Subclasses must define:
    - form_id: Unique identifier for the form
    - title: Dict with 'en' and 'fa' translations
    - description: Dict with 'en' and 'fa' translations
    - fields: List of field definitions
    """
    
    # Form metadata (must be overridden)
    form_id: str = None
    title: Dict[str, str] = None
    description: Dict[str, str] = None
    icon: str = "📝"  # Optional emoji icon
    
    # Access control
    roles: List[str] = ["admin", "employee"]  # Roles that can access this form
    requires_project: bool = True  # Whether form requires project selection
    
    # Form fields (must be overridden)
    fields: List[Dict[str, Any]] = []
    
    def __init__(self):
        """Initialize form and validate configuration."""
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Ensure form is properly configured."""
        if not self.form_id:
            raise ValueError(f"Form {self.__class__.__name__} must define 'form_id'")
        
        if not self.title or 'en' not in self.title or 'fa' not in self.title:
            raise ValueError(f"Form {self.form_id} must define bilingual 'title' with 'en' and 'fa' keys")
        
        if not self.description or 'en' not in self.description or 'fa' not in self.description:
            raise ValueError(f"Form {self.form_id} must define bilingual 'description' with 'en' and 'fa' keys")
        
        if not self.fields:
            raise ValueError(f"Form {self.form_id} must define at least one field")
        
        # Validate each field
        for field in self.fields:
            self._validate_field(field)
    
    def _validate_field(self, field: Dict[str, Any]):
        """Validate a single field definition."""
        required_keys = ['name', 'type', 'label']
        
        for key in required_keys:
            if key not in field:
                raise ValueError(f"Field missing required key '{key}': {field}")
        
        # Validate label is bilingual
        if not isinstance(field['label'], dict) or 'en' not in field['label'] or 'fa' not in field['label']:
            raise ValueError(f"Field '{field['name']}' must have bilingual label with 'en' and 'fa' keys")
        
        # Validate field type
        valid_types = ['text', 'email', 'number', 'tel', 'date', 'datetime-local', 
                      'textarea', 'select', 'radio', 'checkbox', 'file']
        
        if field['type'] not in valid_types:
            raise ValueError(f"Field '{field['name']}' has invalid type '{field['type']}'. Must be one of: {valid_types}")
        
        # Validate select/radio options
        if field['type'] in ['select', 'radio']:
            if 'options' not in field:
                raise ValueError(f"Field '{field['name']}' of type '{field['type']}' must define 'options'")
    
    def get_title(self, locale: str = 'en') -> str:
        """Get form title in specified language."""
        return self.title.get(locale, self.title['en'])
    
    def get_description(self, locale: str = 'en') -> str:
        """Get form description in specified language."""
        return self.description.get(locale, self.description['en'])
    
    def get_field_label(self, field: Dict[str, Any], locale: str = 'en') -> str:
        """Get field label in specified language."""
        return field['label'].get(locale, field['label']['en'])
    
    def get_field_placeholder(self, field: Dict[str, Any], locale: str = 'en') -> Optional[str]:
        """Get field placeholder in specified language."""
        if 'placeholder' not in field:
            return None
        
        if isinstance(field['placeholder'], dict):
            return field['placeholder'].get(locale, field['placeholder'].get('en', ''))
        
        return field['placeholder']
    
    def get_field_help(self, field: Dict[str, Any], locale: str = 'en') -> Optional[str]:
        """Get field help text in specified language."""
        if 'help' not in field:
            return None
        
        if isinstance(field['help'], dict):
            return field['help'].get(locale, field['help'].get('en', ''))
        
        return field['help']
    
    def validate_submission(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate form submission data.
        
        Args:
            data: Dictionary of form data {field_name: value}
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        for field in self.fields:
            field_name = field['name']
            is_required = field.get('required', False)
            
            if is_required and (field_name not in data or not data[field_name]):
                label = self.get_field_label(field, 'en')
                errors.append(f"{label} is required")
        
        # Type-specific validation
        for field in self.fields:
            field_name = field['name']
            
            if field_name not in data or not data[field_name]:
                continue
            
            value = data[field_name]
            field_type = field['type']
            
            # Email validation
            if field_type == 'email':
                if '@' not in value or '.' not in value:
                    errors.append(f"{self.get_field_label(field, 'en')} must be a valid email")
            
            # Number validation
            elif field_type == 'number':
                try:
                    float(value)
                except ValueError:
                    errors.append(f"{self.get_field_label(field, 'en')} must be a number")
            
            # Min/Max validation
            if 'min' in field:
                try:
                    if field_type == 'number' and float(value) < field['min']:
                        errors.append(f"{self.get_field_label(field, 'en')} must be at least {field['min']}")
                    elif field_type == 'text' and len(value) < field['min']:
                        errors.append(f"{self.get_field_label(field, 'en')} must be at least {field['min']} characters")
                except (ValueError, TypeError):
                    pass
            
            if 'max' in field:
                try:
                    if field_type == 'number' and float(value) > field['max']:
                        errors.append(f"{self.get_field_label(field, 'en')} cannot exceed {field['max']}")
                    elif field_type == 'text' and len(value) > field['max']:
                        errors.append(f"{self.get_field_label(field, 'en')} cannot exceed {field['max']} characters")
                except (ValueError, TypeError):
                    pass
        
        # Call custom validation if defined
        custom_errors = self.custom_validation(data)
        if custom_errors:
            errors.extend(custom_errors)
        
        return (len(errors) == 0, errors)
    
    def custom_validation(self, data: Dict[str, Any]) -> List[str]:
        """
        Override this method to add custom validation logic.
        
        Args:
            data: Dictionary of form data
        
        Returns:
            List of error messages (empty if valid)
        """
        return []
    
    def process_submission(self, data: Dict[str, Any], user_id: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process form submission after validation.
        Override this method to add custom processing logic.
        
        Args:
            data: Validated form data
            user_id: ID of user submitting the form
            project_id: Optional project ID
        
        Returns:
            Dictionary with processed data or result
        """
        # Default behavior: return data as-is
        return data
    
    def to_dict(self, locale: str = 'en') -> Dict[str, Any]:
        """
        Convert form to dictionary representation.
        
        Args:
            locale: Language for translations
        
        Returns:
            Dictionary with form metadata and fields
        """
        return {
            'form_id': self.form_id,
            'title': self.get_title(locale),
            'description': self.get_description(locale),
            'icon': self.icon,
            'roles': self.roles,
            'requires_project': self.requires_project,
            'fields': [
                {
                    'name': field['name'],
                    'type': field['type'],
                    'label': self.get_field_label(field, locale),
                    'placeholder': self.get_field_placeholder(field, locale),
                    'help': self.get_field_help(field, locale),
                    'required': field.get('required', False),
                    'options': field.get('options', []),
                    'min': field.get('min'),
                    'max': field.get('max'),
                    'step': field.get('step'),
                    'multiple': field.get('multiple', False),
                    'accept': field.get('accept'),  # For file inputs
                }
                for field in self.fields
            ]
        }
    
    @classmethod
    def get_form_id(cls) -> str:
        """Get form ID without instantiation."""
        return cls.form_id
    
    @classmethod
    def get_form_title(cls, locale: str = 'en') -> str:
        """Get form title without instantiation."""
        return cls.title.get(locale, cls.title['en']) if cls.title else cls.__name__
    
    @classmethod
    def can_access(cls, user_role: str) -> bool:
        """Check if user role can access this form."""
        return user_role in cls.roles
