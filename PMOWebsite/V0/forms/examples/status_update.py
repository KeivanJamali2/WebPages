"""
Project Status Update Form

Allows team members to submit status updates for their projects.
"""

from forms.base_form import BaseForm


class StatusUpdateForm(BaseForm):
    """Form for submitting project status updates."""
    
    form_id = "status_update"
    
    title = {
        "en": "Project Status Update",
        "fa": "به‌روزرسانی وضعیت پروژه"
    }
    
    description = {
        "en": "Submit a status update for your project",
        "fa": "ارسال به‌روزرسانی وضعیت برای پروژه شما"
    }
    
    icon = "📊"
    
    roles = ["admin", "employee"]
    requires_project = True  # Must select a project
    
    fields = [
        {
            "name": "update_type",
            "type": "select",
            "label": {
                "en": "Update Type",
                "fa": "نوع به‌روزرسانی"
            },
            "required": True,
            "options": [
                {"value": "weekly", "label": {"en": "Weekly Update", "fa": "به‌روزرسانی هفتگی"}},
                {"value": "milestone", "label": {"en": "Milestone Completion", "fa": "تکمیل نقطه عطف"}},
                {"value": "issue", "label": {"en": "Issue/Blocker", "fa": "مشکل/مانع"}},
                {"value": "general", "label": {"en": "General Update", "fa": "به‌روزرسانی عمومی"}}
            ]
        },
        {
            "name": "overall_status",
            "type": "radio",
            "label": {
                "en": "Overall Status",
                "fa": "وضعیت کلی"
            },
            "required": True,
            "options": [
                {"value": "on_track", "label": {"en": "On Track", "fa": "در مسیر"}},
                {"value": "at_risk", "label": {"en": "At Risk", "fa": "در معرض خطر"}},
                {"value": "delayed", "label": {"en": "Delayed", "fa": "تاخیر"}},
                {"value": "blocked", "label": {"en": "Blocked", "fa": "مسدود شده"}}
            ]
        },
        {
            "name": "progress_percentage",
            "type": "number",
            "label": {
                "en": "Progress (%)",
                "fa": "پیشرفت (%)"
            },
            "placeholder": {
                "en": "0-100",
                "fa": "۰-۱۰۰"
            },
            "required": True,
            "min": 0,
            "max": 100,
            "step": 5
        },
        {
            "name": "accomplishments",
            "type": "textarea",
            "label": {
                "en": "Accomplishments This Period",
                "fa": "دستاوردهای این دوره"
            },
            "placeholder": {
                "en": "What was completed?",
                "fa": "چه چیزی تکمیل شد؟"
            },
            "help": {
                "en": "List key tasks and milestones completed",
                "fa": "وظایف و نقاط عطف کلیدی تکمیل شده را لیست کنید"
            },
            "required": True,
            "min": 20,
            "max": 1000
        },
        {
            "name": "planned_next",
            "type": "textarea",
            "label": {
                "en": "Planned for Next Period",
                "fa": "برنامه‌ریزی شده برای دوره بعد"
            },
            "placeholder": {
                "en": "What will be done next?",
                "fa": "چه کاری بعداً انجام خواهد شد؟"
            },
            "help": {
                "en": "Outline upcoming tasks and goals",
                "fa": "وظایف و اهداف پیش رو را شرح دهید"
            },
            "required": True,
            "min": 20,
            "max": 1000
        },
        {
            "name": "issues",
            "type": "textarea",
            "label": {
                "en": "Issues & Blockers",
                "fa": "مشکلات و موانع"
            },
            "placeholder": {
                "en": "Any problems or blockers?",
                "fa": "هیچ مشکل یا مانعی وجود دارد؟"
            },
            "help": {
                "en": "Describe any issues requiring attention or support",
                "fa": "هر مشکلی که نیاز به توجه یا پشتیبانی دارد را توضیح دهید"
            },
            "required": False,
            "max": 800
        },
        {
            "name": "budget_status",
            "type": "select",
            "label": {
                "en": "Budget Status",
                "fa": "وضعیت بودجه"
            },
            "required": True,
            "options": [
                {"value": "under", "label": {"en": "Under Budget", "fa": "زیر بودجه"}},
                {"value": "on_budget", "label": {"en": "On Budget", "fa": "در بودجه"}},
                {"value": "over", "label": {"en": "Over Budget", "fa": "بالاتر از بودجه"}},
                {"value": "na", "label": {"en": "N/A", "fa": "نامشخص"}}
            ]
        },
        {
            "name": "budget_notes",
            "type": "textarea",
            "label": {
                "en": "Budget Notes",
                "fa": "یادداشت‌های بودجه"
            },
            "placeholder": {
                "en": "Any budget-related comments",
                "fa": "هر نظر مرتبط با بودجه"
            },
            "required": False,
            "max": 500
        },
        {
            "name": "team_morale",
            "type": "radio",
            "label": {
                "en": "Team Morale",
                "fa": "روحیه تیم"
            },
            "required": False,
            "options": [
                {"value": "excellent", "label": {"en": "Excellent", "fa": "عالی"}},
                {"value": "good", "label": {"en": "Good", "fa": "خوب"}},
                {"value": "fair", "label": {"en": "Fair", "fa": "متوسط"}},
                {"value": "poor", "label": {"en": "Poor", "fa": "ضعیف"}}
            ]
        },
        {
            "name": "additional_notes",
            "type": "textarea",
            "label": {
                "en": "Additional Notes",
                "fa": "یادداشت‌های اضافی"
            },
            "placeholder": {
                "en": "Any other information to share",
                "fa": "هر اطلاعات دیگری که باید به اشتراک گذاشته شود"
            },
            "required": False,
            "max": 500
        }
    ]
    
    def custom_validation(self, data):
        """Custom validation for status updates."""
        errors = []
        
        # If status is blocked or at risk, issues field should be filled
        overall_status = data.get('overall_status', '')
        issues = data.get('issues', '').strip()
        
        if overall_status in ['blocked', 'at_risk'] and not issues:
            errors.append("Please describe the issues causing 'At Risk' or 'Blocked' status")
        
        # If over budget, budget notes should be provided
        budget_status = data.get('budget_status', '')
        budget_notes = data.get('budget_notes', '').strip()
        
        if budget_status == 'over' and not budget_notes:
            errors.append("Please provide budget notes explaining why the project is over budget")
        
        return errors
    
    def process_submission(self, data, user_id, project_id=None):
        """Process the status update submission."""
        processed_data = {
            **data,
            'submitted_by': user_id,
            'project_id': project_id,
            'submission_date': 'now'  # Would use actual timestamp
        }
        
        # In a real application, you might:
        # 1. Update project status in database
        # 2. Send notifications if status is at-risk or blocked
        # 3. Log the update in project history
        # 4. Generate charts/visualizations from the data
        
        return processed_data
