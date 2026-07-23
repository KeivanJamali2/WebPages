"""
=============================================================================
PROJECT-01 CONFIGURATION
احداث تقاطع غیر همسطح ورودی و پل دو دهانه بتنی - کاریزبوم یزد
=============================================================================

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
=============================================================================
"""
import os
from Projects.project_configuration import projects

# Set to True after you have filled in all the values
is_configured = True  # TODO: Set to True after filling values

# =============================================================================
# PROJECT BASIC INFORMATION
# =============================================================================
_current_file = os.path.basename(__file__)
_project_code = _current_file.replace('.py', '')

# Try both naming conventions (Project-01 and Project_01)
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
    "مدیر پروژه": {"total_days_per_year": 60},
    "سرپرست کارگاه": {"total_days_per_year": 360},
    "نقشه بردار": {"total_days_per_year": 360},
    "کنترل پروژه": {"total_days_per_year": 360},
    "دفتر فنی": {"total_days_per_year": 360},
    "سرپرست اجرا": {"total_days_per_year": 360},
    "راننده کامیون": {"total_days_per_year": 360},
    "کارگر ساده": {"total_days_per_year": 360},
    "راننده بولدوزر": {"total_days_per_year": 360},
    "راننده غلتک": {"total_days_per_year": 360},
    "اکیپ بتن ریزی": {"total_days_per_year": 360},
    "راننده گریدر": {"total_days_per_year": 360},
    "اداری": {"total_days_per_year": 25},
    "مباشر": {"total_days_per_year": 360},
}

# =============================================================================
# EQUIPMENT COSTS (Rial per hour) & PLANNED QUANTITIES
# Single source: type → {model → {hourly_rate, planned_quantity}}
# The equipment types and models list is derived from the keys.
# Use "default" key for equipment without specific models.
# =============================================================================
EQUIPMENT_COSTS = {
    "لودر": {"default": {"planned_quantity": 3},},
    "غلتک": {
        "ویبره": {"planned_quantity": 3},
        "چرخ فلزی": {"planned_quantity": 2},
        "چرخ لاستیکی": {"planned_quantity": 3},},
    "قیرپاش": {"default": {"planned_quantity": 1}},
    "کامیون": {"default": {"planned_quantity": 8}},
    "جاروی مکانیکی": {"default": {"planned_quantity": 1}},
    "کمپرسور باد": {"default": {"planned_quantity": 1}},
    "اتومبیل سبک": {"default": {"planned_quantity": 2}},
    "گریدر": {"default": {"planned_quantity": 2},},
    "کامیون آب پاش": {"default" : {"planned_quantity": 3}},
    "فینیشر مخصوص پخش آسفالت": {"default": {"planned_quantity": 1}},
    "بیل مکانیکی": {"default": {"planned_quantity": 1}},
    "بولدوزر": {"default" : {"planned_quantity": 1}},
    "میکسر حمل بتن": {"default": {"planned_quantity": 3}},
    "سنگ شکن": {"default": {"planned_quantity": 1}},
    "بچینگ مخصوص تولید بتن": {"default": {"planned_quantity": 1}},
    "ویبراتور با قدرت کافی": {"default": {"planned_quantity": 3}},
    "قالب فلزی نو": {"default": {"planned_quantity": 0}},
    "دستگاه گارد کوب": {"default": {"planned_quantity": 1}},
    "دستگاه مخصوص خط‌کش": {"default": {"planned_quantity": 1}},
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
    "تجهیز کارگاه": {"unit": "تعداد", "planned_amount": 100, "price_per_unit": 3.85},
    "بنایی با سنگ": {"unit": "متر مکعب (m³)", "planned_amount": 3716, "price_per_unit": 6.23},
    "اجرای موزاییک": {"unit": "متر مربع (m²)", "planned_amount": 5400, "price_per_unit": 1.18},
    "اجرای سنگ پلاک": {"unit": "متر مربع (m²)", "planned_amount": 1534.5, "price_per_unit": 1.21},
    "لوله پی وی سی": {"unit": "متر (m)", "planned_amount": 150, "price_per_unit": 0.03},
    "لوله پلی اتیلن": {"unit": "متر (m)", "planned_amount": 120, "price_per_unit": 0.02},
    "لوازم بهداشتی": {"unit": "تعداد", "planned_amount": 6, "price_per_unit": 0},
    "روشنایی": {"unit": "تعداد", "planned_amount": 600, "price_per_unit": 14.16},
    "تخریب بتن": {"unit": "متر مکعب (m³)", "planned_amount": 79, "price_per_unit": 0.22},
    "پرچیدن جدول بتنی": {"unit": "متر (m)", "planned_amount": 100, "price_per_unit": 0.01},
    "تخریب آسفالت": {"unit": "متر مربع (m²)", "planned_amount": 1800, "price_per_unit": 0.04},
    "حفر میله چاه": {"unit": "متر مکعب (m³)", "planned_amount": 15.7, "price_per_unit": 0.01},
    "بستر سازی": {"unit": "متر مربع (m²)", "planned_amount": 105809, "price_per_unit": 0.47},
    "خاکبرداری": {"unit": "متر مکعب (m³)", "planned_amount": 48847, "price_per_unit": 2.12},
    "پی کنی": {"unit": "متر مکعب (m³)", "planned_amount": 3148, "price_per_unit": 0.43},
    "خاکریزی": {"unit": "متر مکعب (m³)", "planned_amount": 97743, "price_per_unit": 7.13},
    "درناژ": {"unit": "متر مکعب (m³)", "planned_amount": 2217.55, "price_per_unit": 0.37},
    "قالب بندی": {"unit": "متر مربع (m²)", "planned_amount": 7500.4, "price_per_unit": 3.62},
    "میلگرد": {"unit": "کیلوگرم (kg)", "planned_amount": 291270, "price_per_unit": 10.4},
    "فولادی سبک": {"unit": "کیلوگرم (kg)", "planned_amount": 42039, "price_per_unit": 2.83},
    "بتن درجا": {"unit": "متر مکعب (m³)", "planned_amount": 5548, "price_per_unit": 7.71},
    "بتن پیش ساخته": {"unit": "متر مکعب (m³)", "planned_amount": 543, "price_per_unit": 1.44},
    "زیر اساس": {"unit": "متر مکعب (m³)", "planned_amount": 11167, "price_per_unit": 1.63},
    "اساس": {"unit": "متر مکعب (m³)", "planned_amount": 9275, "price_per_unit": 3.69},
    "پریمکت": {"unit": "کیلوگرم (kg)", "planned_amount": 92636, "price_per_unit": 2.94},
    "اساس قیری۰-۳۷": {"unit": "متر مربع (m²)", "planned_amount": 219212, "price_per_unit": 6.32},
    "بیندر ۰-۲۵": {"unit": "متر مربع (m²)", "planned_amount": 362658, "price_per_unit": 12.49},
    "بیندر ۰-۱۹": {"unit": "متر مربع (m²)", "planned_amount": 116508, "price_per_unit": 4.10},
    "عایقکاری": {"unit": "متر مربع (m²)", "planned_amount": 4956, "price_per_unit": 0.40},
    "خطکشی": {"unit": "متر (m)", "planned_amount": 20500, "price_per_unit": 0.24},
    "تابلو علائم": {"unit": "متر مربع (m²)", "planned_amount": 1105, "price_per_unit": 4.73},
}

# =============================================================================
# CLIMATE CONDITIONS
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
