# Creating New Forms - Quick Guide

## Overview
The PMO Website uses a **super simple file-based form system**. Each form is just a Python file with a class that inherits from `BaseForm`. No database changes, no template editing - just create a new `.py` file!

## Quick Start - Create a Form in 3 Minutes

### Step 1: Create a New Python File
Create a new file in `forms/examples/` directory:
```
forms/examples/my_new_form.py
```

### Step 2: Copy This Template
```python
"""
My New Form

Description of what this form does.
"""

from forms.base_form import BaseForm


class MyNewForm(BaseForm):
    """Short description of the form."""
    
    # === REQUIRED CONFIGURATION ===
    form_id = "my_new_form"  # Unique ID (lowercase, underscores only)
    
    title = {
        "en": "My New Form Title",
        "fa": "عنوان فرم جدید من"
    }
    
    description = {
        "en": "Brief description in English",
        "fa": "توضیح مختصر به فارسی"
    }
    
    # === OPTIONAL CONFIGURATION ===
    icon = "📋"  # Emoji icon for the form card
    roles = ["admin", "employee"]  # Who can access: ["admin"], ["employee"], or both
    requires_project = True  # Does form need a project selected?
    
    # === FORM FIELDS ===
    fields = [
        {
            "name": "field_name",  # Unique field identifier
            "type": "text",  # Field type (see types below)
            "label": {
                "en": "Field Label",
                "fa": "برچسب فیلد"
            },
            "placeholder": {  # Optional
                "en": "Enter value...",
                "fa": "مقدار را وارد کنید..."
            },
            "help": {  # Optional help text
                "en": "Helpful instructions",
                "fa": "دستورالعمل‌های مفید"
            },
            "required": True,  # Is field mandatory?
            "min": 10,  # Optional: min length/value
            "max": 100  # Optional: max length/value
        },
        # Add more fields here...
    ]
```

### Step 3: That's It!
Restart the Flask app and your form will automatically appear in the Forms list! ✨

## Field Types Reference

### Text Fields

**Simple Text Input:**
```python
{
    "name": "full_name",
    "type": "text",
    "label": {"en": "Full Name", "fa": "نام کامل"},
    "required": True,
    "min": 3,  # Minimum characters
    "max": 100  # Maximum characters
}
```

**Email:**
```python
{
    "name": "email_address",
    "type": "email",
    "label": {"en": "Email", "fa": "ایمیل"},
    "required": True
}
```

**Phone:**
```python
{
    "name": "phone",
    "type": "tel",
    "label": {"en": "Phone Number", "fa": "شماره تلفن"},
    "placeholder": {"en": "+1234567890", "fa": "۰۹۱۲۳۴۵۶۷۸۹"}
}
```

**Number:**
```python
{
    "name": "budget",
    "type": "number",
    "label": {"en": "Budget Amount", "fa": "مبلغ بودجه"},
    "required": True,
    "min": 0,
    "max": 1000000,
    "step": 100  # Increment step
}
```

**Long Text (Textarea):**
```python
{
    "name": "description",
    "type": "textarea",
    "label": {"en": "Description", "fa": "توضیحات"},
    "required": True,
    "min": 50,  # Minimum characters
    "max": 2000  # Maximum characters
}
```

### Dates

**Date Picker:**
```python
{
    "name": "start_date",
    "type": "date",
    "label": {"en": "Start Date", "fa": "تاریخ شروع"},
    "required": True
}
```

**Date & Time:**
```python
{
    "name": "meeting_time",
    "type": "datetime-local",
    "label": {"en": "Meeting Date & Time", "fa": "تاریخ و زمان جلسه"},
    "required": True
}
```

### Selection Fields

**Dropdown (Select):**
```python
{
    "name": "priority",
    "type": "select",
    "label": {"en": "Priority", "fa": "اولویت"},
    "required": True,
    "options": [
        {"value": "low", "label": {"en": "Low", "fa": "پایین"}},
        {"value": "medium", "label": {"en": "Medium", "fa": "متوسط"}},
        {"value": "high", "label": {"en": "High", "fa": "بالا"}}
    ]
}
```

**Radio Buttons:**
```python
{
    "name": "approval_status",
    "type": "radio",
    "label": {"en": "Status", "fa": "وضعیت"},
    "required": True,
    "options": [
        {"value": "approved", "label": {"en": "Approved", "fa": "تایید شده"}},
        {"value": "rejected", "label": {"en": "Rejected", "fa": "رد شده"}},
        {"value": "pending", "label": {"en": "Pending", "fa": "در انتظار"}}
    ]
}
```

**Checkbox:**
```python
{
    "name": "agree_terms",
    "type": "checkbox",
    "label": {"en": "I agree to the terms", "fa": "با شرایط موافقم"},
    "required": False
}
```

### File Upload

**Single File:**
```python
{
    "name": "document",
    "type": "file",
    "label": {"en": "Upload Document", "fa": "آپلود سند"},
    "accept": ".pdf,.doc,.docx",  # Allowed file types
    "required": False
}
```

**Multiple Files:**
```python
{
    "name": "attachments",
    "type": "file",
    "label": {"en": "Attachments", "fa": "پیوست‌ها"},
    "accept": ".pdf,.jpg,.png",
    "multiple": True,
    "required": False
}
```

## Advanced: Custom Validation

Override `custom_validation()` to add your own validation logic:

```python
def custom_validation(self, data):
    """Add custom validation rules."""
    errors = []
    
    # Example: Check if budget is reasonable for duration
    budget = float(data.get('budget', 0))
    duration = int(data.get('duration_days', 0))
    
    if duration > 365 and budget < 10000:
        errors.append("Long projects (>365 days) require minimum budget of $10,000")
    
    # Example: Require field X if field Y has specific value
    project_type = data.get('project_type', '')
    if project_type == 'development' and not data.get('tech_stack'):
        errors.append("Technology stack is required for development projects")
    
    return errors
```

## Advanced: Custom Processing

Override `process_submission()` to add custom processing after form submission:

```python
def process_submission(self, data, user_id, project_id=None):
    """Process form data after validation."""
    
    # Add computed fields
    processed_data = {
        **data,
        'submitted_by': user_id,
        'project_id': project_id,
        'submission_date': datetime.now().isoformat(),
        'status': 'pending_review'
    }
    
    # You could also:
    # - Send email notifications
    # - Create tasks in project management system
    # - Update related records
    # - Generate reports
    # - Log to audit trail
    
    return processed_data
```

## Complete Real-World Example

Here's a complete "Leave Request" form:

```python
"""
Leave Request Form

Employees can request time off.
"""

from forms.base_form import BaseForm
from datetime import datetime


class LeaveRequestForm(BaseForm):
    """Form for requesting leave/time off."""
    
    form_id = "leave_request"
    
    title = {
        "en": "Leave Request",
        "fa": "درخواست مرخصی"
    }
    
    description = {
        "en": "Request time off from work",
        "fa": "درخواست زمان استراحت از کار"
    }
    
    icon = "🏖️"
    roles = ["employee", "admin"]
    requires_project = False
    
    fields = [
        {
            "name": "leave_type",
            "type": "select",
            "label": {"en": "Leave Type", "fa": "نوع مرخصی"},
            "required": True,
            "options": [
                {"value": "vacation", "label": {"en": "Vacation", "fa": "تعطیلات"}},
                {"value": "sick", "label": {"en": "Sick Leave", "fa": "مرخصی استعلاجی"}},
                {"value": "personal", "label": {"en": "Personal", "fa": "شخصی"}},
                {"value": "emergency", "label": {"en": "Emergency", "fa": "اضطراری"}}
            ]
        },
        {
            "name": "start_date",
            "type": "date",
            "label": {"en": "Start Date", "fa": "تاریخ شروع"},
            "required": True
        },
        {
            "name": "end_date",
            "type": "date",
            "label": {"en": "End Date", "fa": "تاریخ پایان"},
            "required": True
        },
        {
            "name": "days_count",
            "type": "number",
            "label": {"en": "Number of Days", "fa": "تعداد روزها"},
            "required": True,
            "min": 0.5,
            "max": 30,
            "step": 0.5
        },
        {
            "name": "reason",
            "type": "textarea",
            "label": {"en": "Reason", "fa": "دلیل"},
            "placeholder": {
                "en": "Explain your reason for leave",
                "fa": "دلیل مرخصی خود را توضیح دهید"
            },
            "required": True,
            "min": 10,
            "max": 500
        },
        {
            "name": "contact_during_leave",
            "type": "tel",
            "label": {"en": "Emergency Contact", "fa": "تماس اضطراری"},
            "help": {"en": "Phone number where you can be reached", "fa": "شماره تلفنی که می‌توان با شما تماس گرفت"},
            "required": False
        },
        {
            "name": "medical_certificate",
            "type": "file",
            "label": {"en": "Medical Certificate", "fa": "گواهی پزشکی"},
            "help": {"en": "Required for sick leave > 3 days", "fa": "برای مرخصی استعلاجی بیش از ۳ روز الزامی است"},
            "accept": ".pdf,.jpg,.jpeg,.png",
            "required": False
        }
    ]
    
    def custom_validation(self, data):
        """Custom validation for leave requests."""
        errors = []
        
        # Sick leave > 3 days requires medical certificate
        leave_type = data.get('leave_type', '')
        days = float(data.get('days_count', 0))
        medical_cert = data.get('medical_certificate', [])
        
        if leave_type == 'sick' and days > 3 and not medical_cert:
            errors.append("Medical certificate is required for sick leave longer than 3 days")
        
        # Emergency leave requires contact number
        contact = data.get('contact_during_leave', '').strip()
        if leave_type == 'emergency' and not contact:
            errors.append("Emergency contact number is required for emergency leave")
        
        return errors
    
    def process_submission(self, data, user_id, project_id=None):
        """Process leave request."""
        return {
            **data,
            'status': 'pending_approval',
            'requested_by': user_id,
            'request_date': datetime.now().isoformat(),
            'approver': 'manager'  # Could be determined based on leave type
        }
```

Save this as `forms/examples/leave_request.py` and restart - done! 🎉

## Tips & Best Practices

### ✅ DO:
- Use descriptive `form_id` values (e.g., "expense_report" not "form1")
- Always provide both EN and FA translations
- Use appropriate field types (email for emails, number for numbers)
- Add helpful `help` text for complex fields
- Use `min`/`max` for validation
- Override `custom_validation()` for complex rules

### ❌ DON'T:
- Don't use spaces or special characters in `form_id` or `field names`
- Don't forget to mark required fields
- Don't make all fields required - use sensibly
- Don't skip translations (both en and fa are required)

## Troubleshooting

**Form doesn't appear in list:**
- Check file is in `forms/examples/` directory
- Check class inherits from `BaseForm`
- Check no syntax errors in Python file
- Restart Flask application

**Validation not working:**
- Check field has `required: True`
- Check `min`/`max` values are reasonable
- Check custom_validation() returns list of strings

**File uploads not working:**
- Form must have `enctype="multipart/form-data"` (already set in template)
- Field type must be `"file"`
- Check `accept` attribute has correct file extensions

## Form Discovery Process

The system automatically:
1. Scans `forms/examples/` directory
2. Finds all `.py` files
3. Imports each module
4. Looks for classes inheriting from `BaseForm`
5. Validates configuration
6. Registers the form

**No manual registration needed!** Just create the file and restart.

## Next Steps

1. Look at the 3 example forms in `forms/examples/`:
   - `project_request.py` - Complex form with validation
   - `status_update.py` - Form with conditional logic
   - `budget_approval.py` - Form with file uploads

2. Copy one that's similar to what you need

3. Modify the fields

4. Save and restart!

---

**Happy Form Building!** 🚀
