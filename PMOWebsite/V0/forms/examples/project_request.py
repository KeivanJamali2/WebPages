"""
Project Request Form

Allows employees to request new projects.
"""

from forms.base_form import BaseForm


class ProjectRequestForm(BaseForm):
    """Form for requesting a new project."""
    
    form_id = "project_request"
    
    title = {
        "en": "New Project Request",
        "fa": "درخواست پروژه جدید"
    }
    
    description = {
        "en": "Submit a request to initiate a new project",
        "fa": "ارسال درخواست برای شروع یک پروژه جدید"
    }
    
    icon = "🚀"
    
    roles = ["admin", "employee"]
    requires_project = False  # This form creates a project, doesn't need one
    
    fields = [
        {
            "name": "project_name",
            "type": "text",
            "label": {
                "en": "Project Name",
                "fa": "نام پروژه"
            },
            "placeholder": {
                "en": "Enter project name",
                "fa": "نام پروژه را وارد کنید"
            },
            "required": True,
            "min": 3,
            "max": 100
        },
        {
            "name": "project_type",
            "type": "select",
            "label": {
                "en": "Project Type",
                "fa": "نوع پروژه"
            },
            "required": True,
            "options": [
                {"value": "development", "label": {"en": "Development", "fa": "توسعه"}},
                {"value": "design", "label": {"en": "Design", "fa": "طراحی"}},
                {"value": "research", "label": {"en": "Research", "fa": "تحقیق"}},
                {"value": "infrastructure", "label": {"en": "Infrastructure", "fa": "زیرساخت"}},
                {"value": "training", "label": {"en": "Training", "fa": "آموزش"}},
                {"value": "other", "label": {"en": "Other", "fa": "سایر"}}
            ]
        },
        {
            "name": "priority",
            "type": "radio",
            "label": {
                "en": "Priority Level",
                "fa": "سطح اولویت"
            },
            "required": True,
            "options": [
                {"value": "low", "label": {"en": "Low", "fa": "پایین"}},
                {"value": "medium", "label": {"en": "Medium", "fa": "متوسط"}},
                {"value": "high", "label": {"en": "High", "fa": "بالا"}},
                {"value": "critical", "label": {"en": "Critical", "fa": "بحرانی"}}
            ]
        },
        {
            "name": "estimated_budget",
            "type": "number",
            "label": {
                "en": "Estimated Budget (USD)",
                "fa": "بودجه تخمینی (دلار)"
            },
            "placeholder": {
                "en": "Enter amount",
                "fa": "مبلغ را وارد کنید"
            },
            "required": True,
            "min": 0,
            "step": 100
        },
        {
            "name": "estimated_duration",
            "type": "number",
            "label": {
                "en": "Estimated Duration (days)",
                "fa": "مدت زمان تخمینی (روز)"
            },
            "placeholder": {
                "en": "Number of days",
                "fa": "تعداد روز"
            },
            "required": True,
            "min": 1,
            "max": 365
        },
        {
            "name": "start_date",
            "type": "date",
            "label": {
                "en": "Proposed Start Date",
                "fa": "تاریخ شروع پیشنهادی"
            },
            "required": True
        },
        {
            "name": "business_justification",
            "type": "textarea",
            "label": {
                "en": "Business Justification",
                "fa": "توجیه کسب‌وکار"
            },
            "placeholder": {
                "en": "Explain why this project is needed",
                "fa": "توضیح دهید چرا این پروژه مورد نیاز است"
            },
            "help": {
                "en": "Describe the business value and expected benefits",
                "fa": "ارزش کسب‌وکار و مزایای مورد انتظار را توضیح دهید"
            },
            "required": True,
            "min": 50,
            "max": 1000
        },
        {
            "name": "stakeholders",
            "type": "text",
            "label": {
                "en": "Key Stakeholders",
                "fa": "ذینفعان کلیدی"
            },
            "placeholder": {
                "en": "Comma-separated list of stakeholder names",
                "fa": "لیست نام ذینفعان با جداکننده کاما"
            },
            "help": {
                "en": "List all key stakeholders who will be involved",
                "fa": "تمام ذینفعان کلیدی که درگیر خواهند بود را لیست کنید"
            },
            "required": False
        },
        {
            "name": "risks",
            "type": "textarea",
            "label": {
                "en": "Potential Risks",
                "fa": "ریسک‌های احتمالی"
            },
            "placeholder": {
                "en": "Identify any potential risks",
                "fa": "هر ریسک احتمالی را شناسایی کنید"
            },
            "help": {
                "en": "List technical, financial, or operational risks",
                "fa": "ریسک‌های فنی، مالی یا عملیاتی را لیست کنید"
            },
            "required": False,
            "max": 500
        },
        {
            "name": "attachments",
            "type": "file",
            "label": {
                "en": "Supporting Documents",
                "fa": "اسناد پشتیبان"
            },
            "help": {
                "en": "Upload any supporting documents (PDFs, spreadsheets, etc.)",
                "fa": "هر سند پشتیبان را آپلود کنید (PDF، صفحه گسترده و غیره)"
            },
            "required": False,
            "accept": ".pdf,.doc,.docx,.xls,.xlsx",
            "multiple": True
        }
    ]
    
    def custom_validation(self, data):
        """Custom validation for project request."""
        errors = []
        
        # Validate budget range
        budget = float(data.get('estimated_budget', 0))
        if budget > 1000000:
            errors.append("Budget exceeds maximum allowed amount ($1,000,000)")
        
        # Validate duration vs budget correlation
        duration = int(data.get('estimated_duration', 0))
        if budget < 1000 and duration > 30:
            errors.append("Duration seems too long for the estimated budget")
        
        return errors
    
    def process_submission(self, data, user_id, project_id=None):
        """Process the project request submission."""
        # In a real application, you might:
        # 1. Generate a unique project ID
        # 2. Send notifications to PMO admins
        # 3. Create initial project entry in database
        # 4. Log the request for audit trail
        
        processed_data = {
            **data,
            'status': 'pending_approval',
            'requested_by': user_id,
            'request_date': 'now'  # Would use actual timestamp
        }
        
        return processed_data
