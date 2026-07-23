"""
=============================================================================
DEFAULT PROJECT CONFIGURATION TEMPLATE
=============================================================================

HOW TO USE:
1. Copy this file and rename it to your project code (e.g., Project_02.py)
2. PROJECT_INFO automatically loads from project_configuration.py
3. Update other sections with project-specific values
4. All prices are in Rial (ریال)
5. All rates marked with # TODO need to be filled

DATA STRUCTURE (NO DUPLICATION):
- HUMAN_RESOURCES_RATES: position → {total_days_per_year}
  → "Human_Resources" list is derived from dict keys
- EQUIPMENT_COSTS: type → {model → {planned_quantity, hourly_rate (optional)}}
  → "Tools_And_Equipments" dict is derived (type → [models])
  → Use "default" key for equipment without specific models
- MATERIALS: material → unit
  → "Incoming_Materials_And_Goods" dict is derived (material → unit)
- ACTIVITY_BUDGET: activity → {unit, planned_amount, price_per_unit}
  → "Daily_Activity_Report" dict is derived (activity → unit)

IMPORTANT: 
- Do NOT modify this template file directly
- Keep all keys exactly as they are (Persian names must match)
- Set is_configured = True after you fill in the values
- PROJECT_INFO is auto-loaded from project_configuration.py
=============================================================================
"""

import os
from project_configuration import projects

# Set to True after you have filled in all the values
is_configured = False

# =============================================================================
# PROJECT BASIC INFORMATION
# Auto-loaded from project_configuration.py
# =============================================================================
_current_file = os.path.basename(__file__)
_project_code = _current_file.replace('.py', '')
_config_key = _project_code.replace('_', '-') if '_' in _project_code else _project_code

if _config_key in projects:
    _config = projects[_config_key]
    PROJECT_INFO = {
        "project_code": _config_key,
        "name": _config.get("name", "نام پروژه"),
        "location": _config.get("location", "محل پروژه"),
        "contract_number": _config.get("contract_number", ""),
        "start_date": _config.get("start_date", "YYYY-MM-DD"),
        "end_date": _config.get("end_date", "YYYY-MM-DD"),
        "budget": _config.get("budget", 0),
        "owner": _config.get("Owner", "نام کارفرما"),
        "manager": _config.get("manager", "نام مدیر پروژه"),
        "description": _config.get("description", "توضیحات پروژه"),
    }
else:
    PROJECT_INFO = {
        "project_code": _project_code,
        "name": "نام پروژه",
        "location": "محل پروژه",
        "contract_number": "",
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD",
        "budget": 0,
        "owner": "نام کارفرما",
        "manager": "نام مدیر پروژه",
        "description": "توضیحات پروژه",
    }

# =============================================================================
# HUMAN RESOURCES & PLANNED DAYS
# Single source: position → {total_days_per_year}
# total_days_per_year = تعداد روز مورد نیاز در سال (total days needed per year)
# The list of positions is derived from the keys of this dict.
# =============================================================================
HUMAN_RESOURCES_RATES = {
    "مدیر پروژه": {"total_days_per_year": 0},  # TODO: Fill days
    "سرپرست کارگاه": {"total_days_per_year": 0},
    "معاونت اجراء": {"total_days_per_year": 0},
    "مسئول اجرا": {"total_days_per_year": 0},
    "مسئول ابنیه فنی": {"total_days_per_year": 0},
    "سرپرست دفتر فنی": {"total_days_per_year": 0},
    "سرپرست دفترفنی": {"total_days_per_year": 0},
    "کارشناس دفتر فنی": {"total_days_per_year": 0},
    "نقشه بردار": {"total_days_per_year": 0},
    "کمک نقشه بردار": {"total_days_per_year": 0},
    "مباشر عملیات خاکی": {"total_days_per_year": 0},
    "مباشر": {"total_days_per_year": 0},
    "مسئول کنترل پروژه": {"total_days_per_year": 0},
    "کنترل پروژه": {"total_days_per_year": 0},
    "اداری- مالی": {"total_days_per_year": 0},
    "اداری-مالی": {"total_days_per_year": 0},
    "حسابدار": {"total_days_per_year": 0},
    "کارپرداز": {"total_days_per_year": 0},
    "تدارکات": {"total_days_per_year": 0},
    "کارشناس ایمنی": {"total_days_per_year": 0},
    "مسئول ایمنی": {"total_days_per_year": 0},
    "افسر ایمنی": {"total_days_per_year": 0},
    "مسئول HSE": {"total_days_per_year": 0},
    "سرپرست ماشین آلات": {"total_days_per_year": 0},
    "مسئول ماشین آلات": {"total_days_per_year": 0},
    "کارشناس نت ماشین آلات": {"total_days_per_year": 0},
    "راننده سنگین": {"total_days_per_year": 0},
    "راننده ماشین سنگین": {"total_days_per_year": 0},
    "راننده ویژه": {"total_days_per_year": 0},
    "راننده سبک": {"total_days_per_year": 0},
    "راننده سواری و وانت": {"total_days_per_year": 0},
    "راننده گریدر": {"total_days_per_year": 0},
    "راننده لودر": {"total_days_per_year": 0},
    "راننده بیل": {"total_days_per_year": 0},
    "راننده غلطک": {"total_days_per_year": 0},
    "راننده کامیون": {"total_days_per_year": 0},
    "راننده جرثقیل": {"total_days_per_year": 0},
    "راننده آبپاش": {"total_days_per_year": 0},
    "راننده میکسر": {"total_days_per_year": 0},
    "راننده جارو": {"total_days_per_year": 0},
    "راننده کمرشکن": {"total_days_per_year": 0},
    "مکانیک": {"total_days_per_year": 0},
    "سرویس کار": {"total_days_per_year": 0},
    "انباردار": {"total_days_per_year": 0},
    "مسئول حراست": {"total_days_per_year": 0},
    "نگهبان": {"total_days_per_year": 0},
    "مسئول امور داخلی": {"total_days_per_year": 0},
    "امور داخلی کارگاه": {"total_days_per_year": 0},
    "مسئول پشتیبانی": {"total_days_per_year": 0},
    "تاسیسات": {"total_days_per_year": 0},
    "برقکار": {"total_days_per_year": 0},
    "برق کار (ماشین آلات)": {"total_days_per_year": 0},
    "استاد کار بنایی": {"total_days_per_year": 0},
    "بنا": {"total_days_per_year": 0},
    "کارگر": {"total_days_per_year": 0},
    "کارگر ساده": {"total_days_per_year": 0},
    "کارگر گریدر": {"total_days_per_year": 0},
    "بتن ریز": {"total_days_per_year": 0},
    "جوشکار": {"total_days_per_year": 0},
    "آرماتوربند": {"total_days_per_year": 0},
    "قالب بند": {"total_days_per_year": 0},
    "عایق کار": {"total_days_per_year": 0},
    "خدمات": {"total_days_per_year": 0},
    "کنترلچی": {"total_days_per_year": 0},
    "تکنسین آزمایشگاه": {"total_days_per_year": 0},
    "کارگر آزمایشگاه": {"total_days_per_year": 0},
    "نصاب ساندویچ پنل": {"total_days_per_year": 0},
    "اکیپ تاسیسات برق": {"total_days_per_year": 0},
    "اکیپ آسفالت": {"total_days_per_year": 0},
    "اپراتور بچینگ": {"total_days_per_year": 0},
}

# =============================================================================
# EQUIPMENT COSTS (Rial per hour) & PLANNED QUANTITIES
# Single source: type → {model → {hourly_rate, planned_quantity}}
# The equipment types and models list is derived from the keys.
# Use "default" key for equipment without specific models.
# =============================================================================
EQUIPMENT_COSTS = {
    "بیل مکانیکی": {
        "۲۲۰": {"hourly_rate": 0, "planned_quantity": 0},  # TODO: Fill values
        "۳۶۰": {"hourly_rate": 0, "planned_quantity": 0},
        "کارفرما": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "لودر": {
        "۵ تن تیراژه": {"hourly_rate": 0, "planned_quantity": 0},
        "کارفرما": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "بولدوزر": {
        "کاترپیلار D6": {"hourly_rate": 0, "planned_quantity": 0},
        "کاترپیلار D8": {"hourly_rate": 0, "planned_quantity": 0},
        "کارفرما": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "جرثقیل": {
        "۲۵ تن": {"hourly_rate": 0, "planned_quantity": 0},
        "۵۰ تن": {"hourly_rate": 0, "planned_quantity": 0},
        "۱۰۰ تن": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "کمپرسی": {
        "تک": {"hourly_rate": 0, "planned_quantity": 0},
        "جفت": {"hourly_rate": 0, "planned_quantity": 0},
        "۱۰ چرخ": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "تانکر": {
        "آب": {"hourly_rate": 0, "planned_quantity": 0},
        "آبپاش": {"hourly_rate": 0, "planned_quantity": 0},
        "گازوئیل": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "گریدر": {
        "کوماتسو 661A": {"hourly_rate": 0, "planned_quantity": 0},
        "کوماتسو GdA-705": {"hourly_rate": 0, "planned_quantity": 0},
        "کاترپیلار 140G": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "غلتک": {
        "HC100B": {"hourly_rate": 0, "planned_quantity": 0},
        "HC100C": {"hourly_rate": 0, "planned_quantity": 0},
        "کششی": {"hourly_rate": 0, "planned_quantity": 0},
        "چرخ فلزی": {"hourly_rate": 0, "planned_quantity": 0},
        "چرخ لاستیکی": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "تریلی": {
        "کفی": {"hourly_rate": 0, "planned_quantity": 0},
        "کمرشکن": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "تراکتور": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "وانت": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "سواری": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "دوربین نقشه برداری": {
        "GPS": {"hourly_rate": 0, "planned_quantity": 0},
        "توتال": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "ژنراتور": {
        "KVA 40": {"hourly_rate": 0, "planned_quantity": 0},
        "KVA 150": {"hourly_rate": 0, "planned_quantity": 0},
        "KVA 250": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "موتور جوش": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "موتور برق": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "کمپرسور باد": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "کانکس": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "کانتینر": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "مخزن": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "بتونیر": {
        "دیزلی": {"hourly_rate": 0, "planned_quantity": 0},
        "برقی": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "سیلو": {
        "۵۰ تنی": {"hourly_rate": 0, "planned_quantity": 0},
        "۱۰۰ تنی": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "میکسر بتن": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "پمپ بتن": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "فینیشر": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "دستگاه خط‌کش": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "کارخانه آسفالت": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "بچینگ بتن": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
}

# =============================================================================
# MATERIALS
# Single source: material → unit
# The materials list and units are derived from this dict.
# =============================================================================
MATERIALS = {
    "شن و ماسه": "تن (ton)",
    "شن و ماسه و بادامی": "تن (ton)",
    "آسفالت": "تن (ton)",
    "بتن آماده": "متر مکعب (m³)",
    "آجر": "تعداد",
    "آهن آلات": "کیلوگرم (kg)",
    "سیمان": "تن (ton)",
    "ماسه بادی": "تن (ton)",
    "ماسه شکسته": "تن (ton)",
    "گازوئیل": "لیتر (L)",
    "بلوک سیمانی": "تعداد",
    "آب تجهیز": "متر مکعب (m³)",
    "آب عملیات خاکی": "متر مکعب (m³)",
    "پاورشل": "کیلوگرم (kg)",
    "روان کننده": "لیتر (L)",
    "پرایمر": "لیتر (L)",
    "ضدیخ بتن": "لیتر (L)",
    "قیر خالص": "تن (ton)",
    "پروفیل سقف": "کیلوگرم (kg)",
    "میلگرد سایز 8": "کیلوگرم (kg)",
    "میلگرد سایز 10": "کیلوگرم (kg)",
    "میلگرد سایز 12": "کیلوگرم (kg)",
    "میلگرد سایز 16": "کیلوگرم (kg)",
    "میلگرد سایز 18": "کیلوگرم (kg)",
    "میلگرد سایز 20": "کیلوگرم (kg)",
    "میلگرد سایز 25": "کیلوگرم (kg)",
    "میلگرد سایز 32": "کیلوگرم (kg)",
}

# =============================================================================
# ACTIVITY BUDGET & PRICING
# Single source: activity → {unit, planned_amount, price_per_unit}
# The activities list and units are derived from this dict.
# =============================================================================
ACTIVITY_BUDGET = {
    "خاکریزی": {"unit": "متر مکعب (m³)", "planned_amount": 0, "price_per_unit": 0},  # TODO: Fill values
    "خاکبرداری": {"unit": "متر مکعب (m³)", "planned_amount": 0, "price_per_unit": 0},
    "پی‌ریزی": {"unit": "متر مکعب (m³)", "planned_amount": 0, "price_per_unit": 0},
    "آرماتوربندی": {"unit": "کیلوگرم (kg)", "planned_amount": 0, "price_per_unit": 0},
    "قالب‌بندی": {"unit": "متر مربع (m²)", "planned_amount": 0, "price_per_unit": 0},
    "بتن‌ریزی": {"unit": "متر مکعب (m³)", "planned_amount": 0, "price_per_unit": 0},
    "آسفالت‌ریزی": {"unit": "تن (ton)", "planned_amount": 0, "price_per_unit": 0},
    "سنگ‌کاری": {"unit": "متر مربع (m²)", "planned_amount": 0, "price_per_unit": 0},
    "آجرچینی": {"unit": "متر مربع (m²)", "planned_amount": 0, "price_per_unit": 0},
    "شخم زنی": {"unit": "متر مربع (m²)", "planned_amount": 0, "price_per_unit": 0},
    "بارریزی": {"unit": "متر مکعب (m³)", "planned_amount": 0, "price_per_unit": 0},
    "کوبیدن لایه خاکریز": {"unit": "متر مربع (m²)", "planned_amount": 0, "price_per_unit": 0},
    "کوبیدن لایه بستر": {"unit": "متر مربع (m²)", "planned_amount": 0, "price_per_unit": 0},
    "اجرای لایه ساب بیس(زیراساس)": {"unit": "متر مکعب (m³)", "planned_amount": 0, "price_per_unit": 0},
    "اجرای بیس(اساس)": {"unit": "متر مکعب (m³)", "planned_amount": 0, "price_per_unit": 0},
    "پریمکوت": {"unit": "متر مربع (m²)", "planned_amount": 0, "price_per_unit": 0},
    "تک کت": {"unit": "متر مربع (m²)", "planned_amount": 0, "price_per_unit": 0},
    "اجرای اسفالت گرم": {"unit": "تن (ton)", "planned_amount": 0, "price_per_unit": 0},
    "خطکشی مسیر": {"unit": "متر (m)", "planned_amount": 0, "price_per_unit": 0},
    "پی کنی": {"unit": "متر مکعب (m³)", "planned_amount": 0, "price_per_unit": 0},
    "اجرای شفته": {"unit": "متر مکعب (m³)", "planned_amount": 0, "price_per_unit": 0},
    "اجرای بتن مگر": {"unit": "متر مکعب (m³)", "planned_amount": 0, "price_per_unit": 0},
    "قالب بندی": {"unit": "متر مربع (m²)", "planned_amount": 0, "price_per_unit": 0},
    "آرماتور بندی": {"unit": "کیلوگرم (kg)", "planned_amount": 0, "price_per_unit": 0},
    "بتن ریزی": {"unit": "متر مکعب (m³)", "planned_amount": 0, "price_per_unit": 0},
    "اجرای باکس": {"unit": "تعداد", "planned_amount": 0, "price_per_unit": 0},
    "آرماتوربندی آپردال باکس": {"unit": "کیلوگرم (kg)", "planned_amount": 0, "price_per_unit": 0},
    "اجرای نیوجرسی": {"unit": "متر (m)", "planned_amount": 0, "price_per_unit": 0},
    "انتقال ترافیک": {"unit": "متر (m)", "planned_amount": 0, "price_per_unit": 0},
    "عایق کاری": {"unit": "متر مربع (m²)", "planned_amount": 0, "price_per_unit": 0},
}

# =============================================================================
# CLIMATE CONDITIONS
# List of weather-related fields
# =============================================================================
CLIMATE_CONDITIONS = [
    "حداقل دمای هوا",
    "حداکثر دمای هوا",
    "رطوبت هوا",
    "صاف",
    "ابری",
    "بارانی",
    "مه‌آلود",
    "برفی",
]

# =============================================================================
# PROJECT ISSUES
# List of issue types that can occur
# =============================================================================
PROJECT_ISSUES = [
    "معضلات مردمی",
    "مشکلات تامین مصالح",
    "مشکلات نیروی انسانی",
    "مشکلات تجهیزاتی",
    "مسائل مالی",
    "مسائل فنی",
]


# =============================================================================
# HELPER: Derive equipment type → [models] from EQUIPMENT_COSTS
# =============================================================================
def _derive_equipment_types():
    """Derive Tools_And_Equipments from EQUIPMENT_COSTS structure."""
    result = {}
    for eq_type, models_dict in EQUIPMENT_COSTS.items():
        if list(models_dict.keys()) == ["default"]:
            result[eq_type] = []
        else:
            result[eq_type] = [m for m in models_dict.keys() if m != "default"]
    return result


# =============================================================================
# DO NOT MODIFY BELOW THIS LINE
# get_configuration() output is identical to before — all downstream code
# (templates, routes, analysis, utils) works unchanged.
# =============================================================================
def get_configuration():
    """Convert this config file to the standard configuration format."""
    return {
        "Project_Info": PROJECT_INFO,
        "Date_And_Time": [
            "کد سند",
            "تاریخ",
            "روز هفته",
            "شیفت کاری",
        ],
        # Derived from HUMAN_RESOURCES_RATES keys
        "Human_Resources": list(HUMAN_RESOURCES_RATES.keys()),
        "Human_Resources_Rates": HUMAN_RESOURCES_RATES,
        # Derived from EQUIPMENT_COSTS structure
        "Tools_And_Equipments": _derive_equipment_types(),
        "Equipment_Costs": EQUIPMENT_COSTS,
        # Derived from MATERIALS (name → unit)
        "Incoming_Materials": MATERIALS,
        "Incoming_Materials_And_Goods": MATERIALS,
        # Derived from ACTIVITY_BUDGET (extract unit)
        "Daily_Activity_Report": {name: info["unit"] for name, info in ACTIVITY_BUDGET.items()},
        "Activity_Budget": ACTIVITY_BUDGET,
        "Climate_Condition": CLIMATE_CONDITIONS,
        "Project_Issues": PROJECT_ISSUES,
    }


def get_project_info():
    """Return project basic information."""
    return PROJECT_INFO
