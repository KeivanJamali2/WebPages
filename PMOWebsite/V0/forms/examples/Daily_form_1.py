"""
Daily Project Report Form (گزارش روزانه پروژه)

Based on the Faragiti project daily report template.
This form captures comprehensive daily project information including:
- Project and contract information
- Human resources (personnel)
- Equipment and machinery status
- Materials and supplies
- Weather conditions
- Daily activities performed
- Issues and obstacles
"""

from forms.base_form import BaseForm
from datetime import datetime


class DailyReportForm(BaseForm):
    """Daily project report form for construction/engineering projects."""
    
    form_id = "daily_report_1"
    
    title = {
        "en": "Daily Project Report",
        "fa": "گزارش روزانه پروژه"
    }
    
    description = {
        "en": "Comprehensive daily report including personnel, equipment, activities, and issues",
        "fa": "گزارش روزانه جامع شامل پرسنل، تجهیزات، فعالیت‌ها و مشکلات"
    }
    
    icon = "📋"
    
    roles = ["admin", "employee"]
    requires_project = True  # Daily reports are tied to specific projects
    
    fields = [
        # ========== SECTION 1: BASIC INFORMATION ==========
        {
            "name": "report_number",
            "type": "text",
            "label": {
                "en": "Report Number",
                "fa": "شماره گزارش"
            },
            "placeholder": {
                "en": "e.g., 31",
                "fa": "مثال: 31"
            },
            "required": True,
            "min": 1,
            "max": 50
        },
        {
            "name": "report_date",
            "type": "date",
            "label": {
                "en": "Report Date",
                "fa": "تاریخ گزارش"
            },
            "required": True
        },
        {
            "name": "day_of_week",
            "type": "select",
            "label": {
                "en": "Day of Week",
                "fa": "روز هفته"
            },
            "required": True,
            "options": [
                {"value": "saturday", "label": {"en": "Saturday", "fa": "شنبه"}},
                {"value": "sunday", "label": {"en": "Sunday", "fa": "یکشنبه"}},
                {"value": "monday", "label": {"en": "Monday", "fa": "دوشنبه"}},
                {"value": "tuesday", "label": {"en": "Tuesday", "fa": "سه‌شنبه"}},
                {"value": "wednesday", "label": {"en": "Wednesday", "fa": "چهارشنبه"}},
                {"value": "thursday", "label": {"en": "Thursday", "fa": "پنج‌شنبه"}},
                {"value": "friday", "label": {"en": "Friday", "fa": "جمعه"}}
            ]
        },
        {
            "name": "project_name",
            "type": "text",
            "label": {
                "en": "Project Name",
                "fa": "نام پروژه"
            },
            "placeholder": {
                "en": "Full project name",
                "fa": "نام کامل پروژه"
            },
            "required": True,
            "max": 200
        },
        {
            "name": "employer",
            "type": "text",
            "label": {
                "en": "Employer/Client",
                "fa": "کارفرما"
            },
            "placeholder": {
                "en": "Employer company name",
                "fa": "نام شرکت کارفرما"
            },
            "required": True,
            "max": 200
        },
        {
            "name": "consultant",
            "type": "text",
            "label": {
                "en": "Consultant",
                "fa": "مشاور"
            },
            "placeholder": {
                "en": "Consulting firm name",
                "fa": "نام شرکت مشاور"
            },
            "required": True,
            "max": 200
        },
        {
            "name": "contractor",
            "type": "text",
            "label": {
                "en": "Contractor",
                "fa": "پیمانکار"
            },
            "placeholder": {
                "en": "Contractor company name",
                "fa": "نام شرکت پیمانکار"
            },
            "required": True,
            "max": 200
        },
        {
            "name": "contract_number",
            "type": "text",
            "label": {
                "en": "Contract Number",
                "fa": "شماره قرارداد"
            },
            "placeholder": {
                "en": "e.g., 1403/440/ح",
                "fa": "مثال: 1403/440/ح"
            },
            "required": False,
            "max": 100
        },
        {
            "name": "contract_date",
            "type": "date",
            "label": {
                "en": "Contract Date",
                "fa": "تاریخ قرارداد"
            },
            "required": False
        },
        
        # ========== SECTION 2: WEATHER CONDITIONS ==========
        {
            "name": "temperature",
            "type": "number",
            "label": {
                "en": "Temperature (°C)",
                "fa": "دمای هوا (درجه سانتی‌گراد)"
            },
            "placeholder": {
                "en": "e.g., 24.10",
                "fa": "مثال: 24.10"
            },
            "required": False,
            "min": -50,
            "max": 60,
            "step": 0.1
        },
        {
            "name": "humidity",
            "type": "number",
            "label": {
                "en": "Humidity (%)",
                "fa": "رطوبت هوا (%)"
            },
            "placeholder": {
                "en": "0-100",
                "fa": "0 تا 100"
            },
            "required": False,
            "min": 0,
            "max": 100,
            "step": 1
        },
        {
            "name": "weather_condition",
            "type": "select",
            "label": {
                "en": "Weather Condition",
                "fa": "وضعیت آب و هوا"
            },
            "required": True,
            "options": [
                {"value": "sunny", "label": {"en": "Sunny", "fa": "آفتابی"}},
                {"value": "rainy", "label": {"en": "Rainy", "fa": "بارانی"}},
                {"value": "cloudy", "label": {"en": "Cloudy/Partly Cloudy", "fa": "ابری و نیمه ابری"}},
                {"value": "stormy", "label": {"en": "Windy/Stormy", "fa": "باد و طوفان"}}
            ]
        },
        
        # ========== SECTION 3: HUMAN RESOURCES ==========
        {
            "name": "hr_project_manager_present",
            "type": "number",
            "label": {
                "en": "Project Manager - Present",
                "fa": "مدیر پروژه - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_project_manager_absent",
            "type": "number",
            "label": {
                "en": "Project Manager - Absent",
                "fa": "مدیر پروژه - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_site_supervisor_present",
            "type": "number",
            "label": {
                "en": "Site Supervisor - Present",
                "fa": "سرپرست کارگاه - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_site_supervisor_absent",
            "type": "number",
            "label": {
                "en": "Site Supervisor - Absent",
                "fa": "سرپرست کارگاه - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_execution_manager_present",
            "type": "number",
            "label": {
                "en": "Execution Manager - Present",
                "fa": "مسئول اجرا - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_execution_manager_absent",
            "type": "number",
            "label": {
                "en": "Execution Manager - Absent",
                "fa": "مسئول اجرا - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_hse_manager_present",
            "type": "number",
            "label": {
                "en": "HSE Manager - Present",
                "fa": "مسئول HSE - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_hse_manager_absent",
            "type": "number",
            "label": {
                "en": "HSE Manager - Absent",
                "fa": "مسئول HSE - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_surveyor_present",
            "type": "number",
            "label": {
                "en": "Surveyor - Present",
                "fa": "نقشه بردار - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_surveyor_absent",
            "type": "number",
            "label": {
                "en": "Surveyor - Absent",
                "fa": "نقشه بردار - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_surveyor_assistant_present",
            "type": "number",
            "label": {
                "en": "Surveyor Assistant - Present",
                "fa": "کمک نقشه بردار - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_surveyor_assistant_absent",
            "type": "number",
            "label": {
                "en": "Surveyor Assistant - Absent",
                "fa": "کمک نقشه بردار - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_project_controller_present",
            "type": "number",
            "label": {
                "en": "Project Controller - Present",
                "fa": "کنترل پروژه - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_project_controller_absent",
            "type": "number",
            "label": {
                "en": "Project Controller - Absent",
                "fa": "کنترل پروژه - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_accountant_present",
            "type": "number",
            "label": {
                "en": "Accountant - Present",
                "fa": "حسابدار - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_accountant_absent",
            "type": "number",
            "label": {
                "en": "Accountant - Absent",
                "fa": "حسابدار - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_procurement_present",
            "type": "number",
            "label": {
                "en": "Procurement - Present",
                "fa": "تدارکات - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_procurement_absent",
            "type": "number",
            "label": {
                "en": "Procurement - Absent",
                "fa": "تدارکات - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_laborers_present",
            "type": "number",
            "label": {
                "en": "Laborers - Present",
                "fa": "کارگر ساده - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 100,
            "step": 1
        },
        {
            "name": "hr_laborers_absent",
            "type": "number",
            "label": {
                "en": "Laborers - Absent",
                "fa": "کارگر ساده - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 100,
            "step": 1
        },
        {
            "name": "hr_masons_present",
            "type": "number",
            "label": {
                "en": "Masons - Present",
                "fa": "بنا - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "hr_masons_absent",
            "type": "number",
            "label": {
                "en": "Masons - Absent",
                "fa": "بنا - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "hr_concrete_workers_present",
            "type": "number",
            "label": {
                "en": "Concrete Workers - Present",
                "fa": "بتن ریز - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "hr_concrete_workers_absent",
            "type": "number",
            "label": {
                "en": "Concrete Workers - Absent",
                "fa": "بتن ریز - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "hr_warehouse_keeper_present",
            "type": "number",
            "label": {
                "en": "Warehouse Keeper - Present",
                "fa": "انباردار - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_warehouse_keeper_absent",
            "type": "number",
            "label": {
                "en": "Warehouse Keeper - Absent",
                "fa": "انباردار - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 10,
            "step": 1
        },
        {
            "name": "hr_security_present",
            "type": "number",
            "label": {
                "en": "Security - Present",
                "fa": "نگهبان - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "hr_security_absent",
            "type": "number",
            "label": {
                "en": "Security - Absent",
                "fa": "نگهبان - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "hr_services_present",
            "type": "number",
            "label": {
                "en": "Services - Present",
                "fa": "خدمات - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "hr_services_absent",
            "type": "number",
            "label": {
                "en": "Services - Absent",
                "fa": "خدمات - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "hr_heavy_drivers_present",
            "type": "number",
            "label": {
                "en": "Heavy Vehicle Drivers - Present",
                "fa": "راننده ماشین سنگین - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "hr_heavy_drivers_absent",
            "type": "number",
            "label": {
                "en": "Heavy Vehicle Drivers - Absent",
                "fa": "راننده ماشین سنگین - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "hr_light_drivers_present",
            "type": "number",
            "label": {
                "en": "Light Vehicle Drivers - Present",
                "fa": "راننده سواری و وانت - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "hr_light_drivers_absent",
            "type": "number",
            "label": {
                "en": "Light Vehicle Drivers - Absent",
                "fa": "راننده سواری و وانت - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "hr_electrician_present",
            "type": "number",
            "label": {
                "en": "Electrician - Present",
                "fa": "برقکار - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "hr_electrician_absent",
            "type": "number",
            "label": {
                "en": "Electrician - Absent",
                "fa": "برقکار - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "hr_service_technician_present",
            "type": "number",
            "label": {
                "en": "Service Technician - Present",
                "fa": "سرویسکار - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "hr_service_technician_absent",
            "type": "number",
            "label": {
                "en": "Service Technician - Absent",
                "fa": "سرویسکار - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "hr_mechanic_present",
            "type": "number",
            "label": {
                "en": "Mechanic - Present",
                "fa": "مکانیک - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "hr_mechanic_absent",
            "type": "number",
            "label": {
                "en": "Mechanic - Absent",
                "fa": "مکانیک - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "hr_welder_present",
            "type": "number",
            "label": {
                "en": "Welder - Present",
                "fa": "جوشکار - حاضر"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "hr_welder_absent",
            "type": "number",
            "label": {
                "en": "Welder - Absent",
                "fa": "جوشکار - مرخصی"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        
        # ========== SECTION 4: EQUIPMENT AND MACHINERY ==========
        {
            "name": "eq_excavator_active",
            "type": "number",
            "label": {
                "en": "Excavator - Active",
                "fa": "بیل مکانیکی - فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_excavator_repair",
            "type": "number",
            "label": {
                "en": "Excavator - Under Repair",
                "fa": "بیل مکانیکی - تعمیر"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_excavator_inactive",
            "type": "number",
            "label": {
                "en": "Excavator - Inactive",
                "fa": "بیل مکانیکی - غیر فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_loader_active",
            "type": "number",
            "label": {
                "en": "Loader - Active",
                "fa": "لودر - فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_loader_repair",
            "type": "number",
            "label": {
                "en": "Loader - Under Repair",
                "fa": "لودر - تعمیر"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_loader_inactive",
            "type": "number",
            "label": {
                "en": "Loader - Inactive",
                "fa": "لودر - غیر فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_dump_truck_10wheel_active",
            "type": "number",
            "label": {
                "en": "Dump Truck (10-wheel) - Active",
                "fa": "کامیون کمپرسی ده چرخ - فعال"
            },
            "required": True,
            "min": 0,
            "max": 100,
            "step": 1
        },
        {
            "name": "eq_dump_truck_10wheel_repair",
            "type": "number",
            "label": {
                "en": "Dump Truck (10-wheel) - Under Repair",
                "fa": "کامیون کمپرسی ده چرخ - تعمیر"
            },
            "required": True,
            "min": 0,
            "max": 100,
            "step": 1
        },
        {
            "name": "eq_dump_truck_10wheel_inactive",
            "type": "number",
            "label": {
                "en": "Dump Truck (10-wheel) - Inactive",
                "fa": "کامیون کمپرسی ده چرخ - غیر فعال"
            },
            "required": True,
            "min": 0,
            "max": 100,
            "step": 1
        },
        {
            "name": "eq_dump_truck_single_active",
            "type": "number",
            "label": {
                "en": "Dump Truck (Single) - Active",
                "fa": "کامیون کمپرسی تک - فعال"
            },
            "required": True,
            "min": 0,
            "max": 100,
            "step": 1
        },
        {
            "name": "eq_dump_truck_single_repair",
            "type": "number",
            "label": {
                "en": "Dump Truck (Single) - Under Repair",
                "fa": "کامیون کمپرسی تک - تعمیر"
            },
            "required": True,
            "min": 0,
            "max": 100,
            "step": 1
        },
        {
            "name": "eq_dump_truck_single_inactive",
            "type": "number",
            "label": {
                "en": "Dump Truck (Single) - Inactive",
                "fa": "کامیون کمپرسی تک - غیر فعال"
            },
            "required": True,
            "min": 0,
            "max": 100,
            "step": 1
        },
        {
            "name": "eq_water_truck_active",
            "type": "number",
            "label": {
                "en": "Water Truck - Active",
                "fa": "کامیون آبپاش - فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_water_truck_repair",
            "type": "number",
            "label": {
                "en": "Water Truck - Under Repair",
                "fa": "کامیون آبپاش - تعمیر"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_water_truck_inactive",
            "type": "number",
            "label": {
                "en": "Water Truck - Inactive",
                "fa": "کامیون آبپاش - غیر فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_water_tanker_active",
            "type": "number",
            "label": {
                "en": "Water Tanker - Active",
                "fa": "تانکر آب - فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_water_tanker_repair",
            "type": "number",
            "label": {
                "en": "Water Tanker - Under Repair",
                "fa": "تانکر آب - تعمیر"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_water_tanker_inactive",
            "type": "number",
            "label": {
                "en": "Water Tanker - Inactive",
                "fa": "تانکر آب - غیر فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_fuel_tanker_active",
            "type": "number",
            "label": {
                "en": "Fuel Tanker - Active",
                "fa": "تانکر گازوییل - فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_fuel_tanker_repair",
            "type": "number",
            "label": {
                "en": "Fuel Tanker - Under Repair",
                "fa": "تانکر گازوییل - تعمیر"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_fuel_tanker_inactive",
            "type": "number",
            "label": {
                "en": "Fuel Tanker - Inactive",
                "fa": "تانکر گازوییل - غیر فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_grader_active",
            "type": "number",
            "label": {
                "en": "Grader - Active",
                "fa": "گریدر - فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_grader_repair",
            "type": "number",
            "label": {
                "en": "Grader - Under Repair",
                "fa": "گریدر - تعمیر"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_grader_inactive",
            "type": "number",
            "label": {
                "en": "Grader - Inactive",
                "fa": "گریدر - غیر فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_roller_active",
            "type": "number",
            "label": {
                "en": "Roller - Active",
                "fa": "غلطک - فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_roller_repair",
            "type": "number",
            "label": {
                "en": "Roller - Under Repair",
                "fa": "غلطک - تعمیر"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_roller_inactive",
            "type": "number",
            "label": {
                "en": "Roller - Inactive",
                "fa": "غلطک - غیر فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_trailer_active",
            "type": "number",
            "label": {
                "en": "Trailer - Active",
                "fa": "تریلی - فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_trailer_repair",
            "type": "number",
            "label": {
                "en": "Trailer - Under Repair",
                "fa": "تریلی - تعمیر"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_trailer_inactive",
            "type": "number",
            "label": {
                "en": "Trailer - Inactive",
                "fa": "تریلی - غیر فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_pickup_active",
            "type": "number",
            "label": {
                "en": "Pickup Truck - Active",
                "fa": "وانت - فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_pickup_repair",
            "type": "number",
            "label": {
                "en": "Pickup Truck - Under Repair",
                "fa": "وانت - تعمیر"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_pickup_inactive",
            "type": "number",
            "label": {
                "en": "Pickup Truck - Inactive",
                "fa": "وانت - غیر فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_car_active",
            "type": "number",
            "label": {
                "en": "Car - Active",
                "fa": "سواری - فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_car_repair",
            "type": "number",
            "label": {
                "en": "Car - Under Repair",
                "fa": "سواری - تعمیر"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_car_inactive",
            "type": "number",
            "label": {
                "en": "Car - Inactive",
                "fa": "سواری - غیر فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_survey_camera_active",
            "type": "number",
            "label": {
                "en": "Survey Camera - Active",
                "fa": "دوربین نقشه برداری - فعال"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "eq_survey_camera_repair",
            "type": "number",
            "label": {
                "en": "Survey Camera - Under Repair",
                "fa": "دوربین نقشه برداری - تعمیر"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "eq_survey_camera_inactive",
            "type": "number",
            "label": {
                "en": "Survey Camera - Inactive",
                "fa": "دوربین نقشه برداری - غیر فعال"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "eq_gps_camera_active",
            "type": "number",
            "label": {
                "en": "GPS Camera - Active",
                "fa": "دوربین GPS - فعال"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "eq_gps_camera_repair",
            "type": "number",
            "label": {
                "en": "GPS Camera - Under Repair",
                "fa": "دوربین GPS - تعمیر"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "eq_gps_camera_inactive",
            "type": "number",
            "label": {
                "en": "GPS Camera - Inactive",
                "fa": "دوربین GPS - غیر فعال"
            },
            "required": True,
            "min": 0,
            "max": 20,
            "step": 1
        },
        {
            "name": "eq_bulldozer_client_active",
            "type": "number",
            "label": {
                "en": "Bulldozer (Client's) - Active",
                "fa": "بولدوزر (کارفرما) - فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_bulldozer_client_repair",
            "type": "number",
            "label": {
                "en": "Bulldozer (Client's) - Under Repair",
                "fa": "بولدوزر (کارفرما) - تعمیر"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_bulldozer_client_inactive",
            "type": "number",
            "label": {
                "en": "Bulldozer (Client's) - Inactive",
                "fa": "بولدوزر (کارفرما) - غیر فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_loader_client_active",
            "type": "number",
            "label": {
                "en": "Loader (Client's) - Active",
                "fa": "لودر (کارفرما) - فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_loader_client_repair",
            "type": "number",
            "label": {
                "en": "Loader (Client's) - Under Repair",
                "fa": "لودر (کارفرما) - تعمیر"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_loader_client_inactive",
            "type": "number",
            "label": {
                "en": "Loader (Client's) - Inactive",
                "fa": "لودر (کارفرما) - غیر فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_excavator_client_active",
            "type": "number",
            "label": {
                "en": "Excavator (Client's) - Active",
                "fa": "بیل مکانیکی (کارفرما) - فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_excavator_client_repair",
            "type": "number",
            "label": {
                "en": "Excavator (Client's) - Under Repair",
                "fa": "بیل مکانیکی (کارفرما) - تعمیر"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        {
            "name": "eq_excavator_client_inactive",
            "type": "number",
            "label": {
                "en": "Excavator (Client's) - Inactive",
                "fa": "بیل مکانیکی (کارفرما) - غیر فعال"
            },
            "required": True,
            "min": 0,
            "max": 50,
            "step": 1
        },
        
        # ========== SECTION 5: MATERIALS AND SUPPLIES ==========
        {
            "name": "materials_received",
            "type": "textarea",
            "label": {
                "en": "Materials and Supplies Received",
                "fa": "مصالح و کالای ورودی به کارگاه"
            },
            "placeholder": {
                "en": "List materials received today (material name, quantity, unit)",
                "fa": "لیست مصالح دریافتی امروز (نام مصالح، مقدار، واحد)"
            },
            "help": {
                "en": "Example: Cement - 50 - Bag, Steel Rebar - 2000 - Kg",
                "fa": "مثال: سیمان - 50 - کیسه، میلگرد - 2000 - کیلوگرم"
            },
            "required": False,
            "max": 2000
        },
        
        # ========== SECTION 6: DAILY ACTIVITIES ==========
        {
            "name": "activity_1_description",
            "type": "textarea",
            "label": {
                "en": "Activity 1 - Description",
                "fa": "فعالیت 1 - شرح فعالیت"
            },
            "placeholder": {
                "en": "Describe the work performed",
                "fa": "شرح کار انجام شده"
            },
            "required": False,
            "max": 500
        },
        {
            "name": "activity_1_location",
            "type": "text",
            "label": {
                "en": "Activity 1 - Location",
                "fa": "فعالیت 1 - موقعیت"
            },
            "placeholder": {
                "en": "e.g., 1+130 to 1+100",
                "fa": "مثال: 1+130 الی 1+100"
            },
            "required": False,
            "max": 200
        },
        {
            "name": "activity_1_unit",
            "type": "text",
            "label": {
                "en": "Activity 1 - Unit",
                "fa": "فعالیت 1 - واحد"
            },
            "placeholder": {
                "en": "e.g., cubic meter, meter, etc.",
                "fa": "مثال: مترمکعب، متر و غیره"
            },
            "required": False,
            "max": 50
        },
        {
            "name": "activity_1_daily_amount",
            "type": "number",
            "label": {
                "en": "Activity 1 - Daily Amount",
                "fa": "فعالیت 1 - مقدار روزانه"
            },
            "placeholder": {
                "en": "Amount completed today",
                "fa": "مقدار انجام شده امروز"
            },
            "required": False,
            "min": 0,
            "step": 0.01
        },
        {
            "name": "activity_1_total_amount",
            "type": "number",
            "label": {
                "en": "Activity 1 - Cumulative Total",
                "fa": "فعالیت 1 - مقدار کل"
            },
            "placeholder": {
                "en": "Total amount to date",
                "fa": "مقدار کل تا به امروز"
            },
            "required": False,
            "min": 0,
            "step": 0.01
        },
        {
            "name": "activity_2_description",
            "type": "textarea",
            "label": {
                "en": "Activity 2 - Description",
                "fa": "فعالیت 2 - شرح فعالیت"
            },
            "placeholder": {
                "en": "Describe the work performed",
                "fa": "شرح کار انجام شده"
            },
            "required": False,
            "max": 500
        },
        {
            "name": "activity_2_location",
            "type": "text",
            "label": {
                "en": "Activity 2 - Location",
                "fa": "فعالیت 2 - موقعیت"
            },
            "placeholder": {
                "en": "Location or station",
                "fa": "موقعیت یا ایستگاه"
            },
            "required": False,
            "max": 200
        },
        {
            "name": "activity_2_unit",
            "type": "text",
            "label": {
                "en": "Activity 2 - Unit",
                "fa": "فعالیت 2 - واحد"
            },
            "placeholder": {
                "en": "Unit of measurement",
                "fa": "واحد اندازه‌گیری"
            },
            "required": False,
            "max": 50
        },
        {
            "name": "activity_2_daily_amount",
            "type": "number",
            "label": {
                "en": "Activity 2 - Daily Amount",
                "fa": "فعالیت 2 - مقدار روزانه"
            },
            "required": False,
            "min": 0,
            "step": 0.01
        },
        {
            "name": "activity_2_total_amount",
            "type": "number",
            "label": {
                "en": "Activity 2 - Cumulative Total",
                "fa": "فعالیت 2 - مقدار کل"
            },
            "required": False,
            "min": 0,
            "step": 0.01
        },
        {
            "name": "activity_3_description",
            "type": "textarea",
            "label": {
                "en": "Activity 3 - Description",
                "fa": "فعالیت 3 - شرح فعالیت"
            },
            "placeholder": {
                "en": "Describe the work performed",
                "fa": "شرح کار انجام شده"
            },
            "required": False,
            "max": 500
        },
        {
            "name": "activity_3_location",
            "type": "text",
            "label": {
                "en": "Activity 3 - Location",
                "fa": "فعالیت 3 - موقعیت"
            },
            "required": False,
            "max": 200
        },
        {
            "name": "activity_3_unit",
            "type": "text",
            "label": {
                "en": "Activity 3 - Unit",
                "fa": "فعالیت 3 - واحد"
            },
            "required": False,
            "max": 50
        },
        {
            "name": "activity_3_daily_amount",
            "type": "number",
            "label": {
                "en": "Activity 3 - Daily Amount",
                "fa": "فعالیت 3 - مقدار روزانه"
            },
            "required": False,
            "min": 0,
            "step": 0.01
        },
        {
            "name": "activity_3_total_amount",
            "type": "number",
            "label": {
                "en": "Activity 3 - Cumulative Total",
                "fa": "فعالیت 3 - مقدار کل"
            },
            "required": False,
            "min": 0,
            "step": 0.01
        },
        
        # ========== SECTION 7: ISSUES AND OBSTACLES ==========
        {
            "name": "issues_and_obstacles",
            "type": "textarea",
            "label": {
                "en": "Project Issues and Obstacles",
                "fa": "مشکلات و موانع پروژه"
            },
            "placeholder": {
                "en": "Describe any issues, obstacles, or delays encountered today",
                "fa": "هر مشکل، مانع یا تاخیری که امروز با آن مواجه شدید را شرح دهید"
            },
            "help": {
                "en": "Include equipment breakdowns, weather delays, material shortages, etc.",
                "fa": "شامل خرابی تجهیزات، تاخیرهای آب و هوایی، کمبود مصالح و غیره"
            },
            "required": False,
            "max": 2000
        },
        
        # ========== SECTION 8: ADDITIONAL NOTES ==========
        {
            "name": "additional_notes",
            "type": "textarea",
            "label": {
                "en": "Additional Notes",
                "fa": "یادداشت‌های اضافی"
            },
            "placeholder": {
                "en": "Any other relevant information",
                "fa": "هر اطلاعات مرتبط دیگری"
            },
            "required": False,
            "max": 1000
        },
        
        # ========== SECTION 9: ATTACHMENTS ==========
        {
            "name": "attachments",
            "type": "file",
            "label": {
                "en": "Attachments (Photos, Documents)",
                "fa": "پیوست‌ها (عکس‌ها، اسناد)"
            },
            "help": {
                "en": "Upload photos of work progress, signed documents, or other relevant files",
                "fa": "عکس‌های پیشرفت کار، اسناد امضا شده یا سایر فایل‌های مرتبط را آپلود کنید"
            },
            "required": False,
            "accept": ".pdf,.jpg,.jpeg,.png,.doc,.docx",
            "multiple": True
        },
        
        # ========== SECTION 10: SIGNATURES ==========
        {
            "name": "execution_manager_name",
            "type": "text",
            "label": {
                "en": "Execution Manager / Technical Office",
                "fa": "مسئول اجرا / دفتر فنی"
            },
            "placeholder": {
                "en": "Full name",
                "fa": "نام کامل"
            },
            "required": False,
            "max": 100
        },
        {
            "name": "site_supervisor_name",
            "type": "text",
            "label": {
                "en": "Site Supervisor",
                "fa": "سرپرست کارگاه"
            },
            "placeholder": {
                "en": "Full name",
                "fa": "نام کامل"
            },
            "required": False,
            "max": 100
        },
        {
            "name": "supervision_supervisor_name",
            "type": "text",
            "label": {
                "en": "Supervision Supervisor",
                "fa": "سرپرست نظارت"
            },
            "placeholder": {
                "en": "Full name",
                "fa": "نام کامل"
            },
            "required": False,
            "max": 100
        },
        {
            "name": "client_representative_name",
            "type": "text",
            "label": {
                "en": "Client Representative",
                "fa": "نماینده کارفرما"
            },
            "placeholder": {
                "en": "Full name",
                "fa": "نام کامل"
            },
            "required": False,
            "max": 100
        }
    ]
    
    def custom_validation(self, data):
        """Custom validation for daily report."""
        errors = []
        
        # Validate that at least one activity is filled
        has_activity = False
        for i in range(1, 4):
            if (data.get(f'activity_{i}_description') or 
                data.get(f'activity_{i}_location') or 
                data.get(f'activity_{i}_daily_amount')):
                has_activity = True
                break
        
        if not has_activity:
            errors.append("At least one activity must be recorded")
        
        # Validate activity completeness
        for i in range(1, 4):
            desc = data.get(f'activity_{i}_description', '').strip()
            daily = data.get(f'activity_{i}_daily_amount')
            
            # If description is filled, daily amount should be filled
            if desc and not daily:
                errors.append(f"Activity {i}: Daily amount is required when description is provided")
            
            # If daily amount is filled, description should be filled
            if daily and not desc:
                errors.append(f"Activity {i}: Description is required when daily amount is provided")
        
        # Validate temperature range if provided
        temp = data.get('temperature')
        if temp is not None:
            try:
                temp_float = float(temp)
                if temp_float < -50 or temp_float > 60:
                    errors.append("Temperature seems unrealistic (should be between -50°C and 60°C)")
            except (ValueError, TypeError):
                pass
        
        # Validate humidity range if provided
        humidity = data.get('humidity')
        if humidity is not None:
            try:
                humidity_float = float(humidity)
                if humidity_float < 0 or humidity_float > 100:
                    errors.append("Humidity must be between 0% and 100%")
            except (ValueError, TypeError):
                pass
        
        return errors
    
    def process_submission(self, data, user_id, project_id=None):
        """Process the daily report submission."""
        # Calculate totals
        total_hr_present = 0
        total_hr_absent = 0
        total_eq_active = 0
        total_eq_repair = 0
        total_eq_inactive = 0
        
        # Sum human resources
        for key, value in data.items():
            if key.startswith('hr_') and key.endswith('_present'):
                try:
                    total_hr_present += int(value or 0)
                except (ValueError, TypeError):
                    pass
            elif key.startswith('hr_') and key.endswith('_absent'):
                try:
                    total_hr_absent += int(value or 0)
                except (ValueError, TypeError):
                    pass
        
        # Sum equipment
        for key, value in data.items():
            if key.startswith('eq_') and key.endswith('_active'):
                try:
                    total_eq_active += int(value or 0)
                except (ValueError, TypeError):
                    pass
            elif key.startswith('eq_') and key.endswith('_repair'):
                try:
                    total_eq_repair += int(value or 0)
                except (ValueError, TypeError):
                    pass
            elif key.startswith('eq_') and key.endswith('_inactive'):
                try:
                    total_eq_inactive += int(value or 0)
                except (ValueError, TypeError):
                    pass
        
        processed_data = {
            **data,
            'submitted_by': user_id,
            'project_id': project_id,
            'submission_date': datetime.now().isoformat(),
            'status': 'submitted',
            'total_personnel_present': total_hr_present,
            'total_personnel_absent': total_hr_absent,
            'total_equipment_active': total_eq_active,
            'total_equipment_repair': total_eq_repair,
            'total_equipment_inactive': total_eq_inactive,
            'total_personnel': total_hr_present + total_hr_absent,
            'total_equipment': total_eq_active + total_eq_repair + total_eq_inactive
        }
        
        return processed_data
