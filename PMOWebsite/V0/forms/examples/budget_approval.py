"""
Budget Approval Request Form

Allows project managers to request budget approvals.
"""

from forms.base_form import BaseForm


class BudgetApprovalForm(BaseForm):
    """Form for requesting budget approval."""
    
    form_id = "budget_approval"
    
    title = {
        "en": "Budget Approval Request",
        "fa": "درخواست تایید بودجه"
    }
    
    description = {
        "en": "Submit a budget approval request for your project",
        "fa": "ارسال درخواست تایید بودجه برای پروژه شما"
    }
    
    icon = "💰"
    
    roles = ["admin", "employee"]  # Regular employees can request, admins approve
    requires_project = True
    
    fields = [
        {
            "name": "request_type",
            "type": "radio",
            "label": {
                "en": "Request Type",
                "fa": "نوع درخواست"
            },
            "required": True,
            "options": [
                {"value": "initial", "label": {"en": "Initial Budget", "fa": "بودجه اولیه"}},
                {"value": "additional", "label": {"en": "Additional Funds", "fa": "بودجه اضافی"}},
                {"value": "reallocation", "label": {"en": "Budget Reallocation", "fa": "تخصیص مجدد بودجه"}}
            ]
        },
        {
            "name": "requested_amount",
            "type": "number",
            "label": {
                "en": "Requested Amount (USD)",
                "fa": "مبلغ درخواستی (دلار)"
            },
            "placeholder": {
                "en": "Enter amount",
                "fa": "مبلغ را وارد کنید"
            },
            "required": True,
            "min": 100,
            "step": 100
        },
        {
            "name": "currency",
            "type": "select",
            "label": {
                "en": "Currency",
                "fa": "واحد پول"
            },
            "required": True,
            "options": [
                {"value": "USD", "label": {"en": "US Dollar (USD)", "fa": "دلار آمریکا (USD)"}},
                {"value": "EUR", "label": {"en": "Euro (EUR)", "fa": "یورو (EUR)"}},
                {"value": "GBP", "label": {"en": "British Pound (GBP)", "fa": "پوند بریتانیا (GBP)"}},
                {"value": "IRR", "label": {"en": "Iranian Rial (IRR)", "fa": "ریال ایران (IRR)"}}
            ]
        },
        {
            "name": "category",
            "type": "select",
            "label": {
                "en": "Budget Category",
                "fa": "دسته بودجه"
            },
            "required": True,
            "options": [
                {"value": "personnel", "label": {"en": "Personnel", "fa": "پرسنل"}},
                {"value": "equipment", "label": {"en": "Equipment", "fa": "تجهیزات"}},
                {"value": "software", "label": {"en": "Software/Licenses", "fa": "نرم‌افزار/مجوزها"}},
                {"value": "infrastructure", "label": {"en": "Infrastructure", "fa": "زیرساخت"}},
                {"value": "training", "label": {"en": "Training", "fa": "آموزش"}},
                {"value": "consulting", "label": {"en": "Consulting", "fa": "مشاوره"}},
                {"value": "travel", "label": {"en": "Travel", "fa": "سفر"}},
                {"value": "other", "label": {"en": "Other", "fa": "سایر"}}
            ]
        },
        {
            "name": "justification",
            "type": "textarea",
            "label": {
                "en": "Justification",
                "fa": "توجیه"
            },
            "placeholder": {
                "en": "Explain why this budget is needed",
                "fa": "توضیح دهید چرا این بودجه مورد نیاز است"
            },
            "help": {
                "en": "Provide detailed reasoning for the budget request",
                "fa": "استدلال دقیق برای درخواست بودجه ارائه دهید"
            },
            "required": True,
            "min": 50,
            "max": 1500
        },
        {
            "name": "expected_benefit",
            "type": "textarea",
            "label": {
                "en": "Expected Benefits",
                "fa": "مزایای مورد انتظار"
            },
            "placeholder": {
                "en": "What benefits will this expenditure bring?",
                "fa": "این هزینه چه مزایایی خواهد داشت؟"
            },
            "help": {
                "en": "Describe the return on investment and project impact",
                "fa": "بازگشت سرمایه و تاثیر پروژه را توضیح دهید"
            },
            "required": True,
            "min": 30,
            "max": 1000
        },
        {
            "name": "urgency",
            "type": "radio",
            "label": {
                "en": "Urgency Level",
                "fa": "سطح فوریت"
            },
            "required": True,
            "options": [
                {"value": "low", "label": {"en": "Low - Can wait", "fa": "پایین - می‌تواند صبر کند"}},
                {"value": "medium", "label": {"en": "Medium - Within 30 days", "fa": "متوسط - ظرف ۳۰ روز"}},
                {"value": "high", "label": {"en": "High - Within 14 days", "fa": "بالا - ظرف ۱۴ روز"}},
                {"value": "critical", "label": {"en": "Critical - Immediate", "fa": "بحرانی - فوری"}}
            ]
        },
        {
            "name": "urgency_reason",
            "type": "textarea",
            "label": {
                "en": "Urgency Reason",
                "fa": "دلیل فوریت"
            },
            "placeholder": {
                "en": "Explain the urgency if high or critical",
                "fa": "در صورت فوریت بالا یا بحرانی توضیح دهید"
            },
            "required": False,
            "max": 500
        },
        {
            "name": "alternatives_considered",
            "type": "textarea",
            "label": {
                "en": "Alternatives Considered",
                "fa": "جایگزین‌های در نظر گرفته شده"
            },
            "placeholder": {
                "en": "What other options were evaluated?",
                "fa": "چه گزینه‌های دیگری بررسی شد؟"
            },
            "help": {
                "en": "List alternative solutions and why they were not chosen",
                "fa": "راه‌حل‌های جایگزین و دلیل انتخاب نشدن آنها را لیست کنید"
            },
            "required": False,
            "max": 800
        },
        {
            "name": "vendor_quotes",
            "type": "checkbox",
            "label": {
                "en": "Vendor Quotes Attached",
                "fa": "پیشنهادات فروشنده پیوست شده"
            },
            "help": {
                "en": "Check if you have attached vendor quotes/proposals",
                "fa": "در صورت پیوست کردن پیشنهادات فروشنده علامت بزنید"
            },
            "required": False
        },
        {
            "name": "competitive_bids",
            "type": "number",
            "label": {
                "en": "Number of Competitive Bids",
                "fa": "تعداد پیشنهادات رقابتی"
            },
            "placeholder": {
                "en": "How many vendors were consulted?",
                "fa": "با چند فروشنده مشورت شد؟"
            },
            "help": {
                "en": "Number of vendor quotes obtained for comparison",
                "fa": "تعداد پیشنهادات فروشنده که برای مقایسه دریافت شده"
            },
            "required": False,
            "min": 0,
            "max": 20
        },
        {
            "name": "payment_schedule",
            "type": "select",
            "label": {
                "en": "Preferred Payment Schedule",
                "fa": "برنامه پرداخت ترجیحی"
            },
            "required": True,
            "options": [
                {"value": "lump_sum", "label": {"en": "Lump Sum", "fa": "یکجا"}},
                {"value": "milestones", "label": {"en": "Milestone-Based", "fa": "بر اساس نقاط عطف"}},
                {"value": "monthly", "label": {"en": "Monthly Installments", "fa": "اقساط ماهانه"}},
                {"value": "quarterly", "label": {"en": "Quarterly", "fa": "فصلی"}}
            ]
        },
        {
            "name": "supporting_docs",
            "type": "file",
            "label": {
                "en": "Supporting Documents",
                "fa": "اسناد پشتیبان"
            },
            "help": {
                "en": "Upload quotes, proposals, or other supporting documents",
                "fa": "پیشنهادات، طرح‌ها یا سایر اسناد پشتیبان را آپلود کنید"
            },
            "required": False,
            "accept": ".pdf,.doc,.docx,.xls,.xlsx",
            "multiple": True
        }
    ]
    
    def custom_validation(self, data):
        """Custom validation for budget approval requests."""
        errors = []
        
        # Validate urgency reason for high/critical urgency
        urgency = data.get('urgency', '')
        urgency_reason = data.get('urgency_reason', '').strip()
        
        if urgency in ['high', 'critical'] and not urgency_reason:
            errors.append("Urgency reason is required for high or critical urgency levels")
        
        # Validate competitive bids for large amounts
        amount = float(data.get('requested_amount', 0))
        competitive_bids = int(data.get('competitive_bids', 0)) if data.get('competitive_bids') else 0
        
        if amount > 10000 and competitive_bids < 2:
            errors.append("For amounts over $10,000, at least 2 competitive bids are recommended")
        
        # Warn if no vendor quotes for equipment/software
        category = data.get('category', '')
        vendor_quotes = data.get('vendor_quotes', False)
        
        if category in ['equipment', 'software'] and amount > 5000 and not vendor_quotes:
            errors.append("Vendor quotes are strongly recommended for equipment/software over $5,000")
        
        return errors
    
    def process_submission(self, data, user_id, project_id=None):
        """Process the budget approval request."""
        processed_data = {
            **data,
            'status': 'pending_approval',
            'requested_by': user_id,
            'project_id': project_id,
            'request_date': 'now',  # Would use actual timestamp
            'approval_level_required': 'manager' if float(data.get('requested_amount', 0)) < 50000 else 'director'
        }
        
        # In a real application, you might:
        # 1. Route to appropriate approval authority based on amount
        # 2. Send notification emails to approvers
        # 3. Create approval workflow
        # 4. Log in audit trail
        # 5. Update project budget tracking
        
        return processed_data
