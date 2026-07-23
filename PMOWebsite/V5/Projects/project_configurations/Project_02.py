"""
=============================================================================
PROJECT-02 CONFIGURATION
پروژه چادرملو-بهاباد
=============================================================================

DATA STRUCTURE (NO DUPLICATION):
- HUMAN_RESOURCES_RATES: position → {total_days}
  → "Human_Resources" list is derived from dict keys
- EQUIPMENT_COSTS: type → {model → {planned_quantity, hourly_rate (optional)}}
  → "Tools_And_Equipments" dict is derived (type → [models])
  → Use "default" key for equipment without specific models
- MATERIAL_PRICES: material → {unit, price_per_unit, planned_total}
  → "Incoming_Materials_And_Goods" dict is derived (material → unit)
- ACTIVITY_BUDGET: activity → {unit, planned_amount, price_per_unit}
  → "Daily_Activity_Report" dict is derived (activity → unit)
=============================================================================
"""

import os
from Projects.project_configuration import projects

# Set to True after you have filled in all the values
is_configured = True

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
# Single source: position → {total_days}
# total_days = تعداد روز مورد نیاز (total days needed in contract)
# The list of positions is derived from the keys of this dict.
# =============================================================================
HUMAN_RESOURCES_RATES = {
    # مدیریت و فنی
    "مدیر پروژه": {"total_days": 120},
    "سرپرست کارگاه": {"total_days": 365},
    "سرپرست دفترفنی": {"total_days": 365},
    "نقشه بردار": {"total_days": 365},
    "کمک نقشه بردار": {"total_days": 365},
    "مسئول ابنیه فنی": {"total_days": 365},
    "مسئول کنترل پروژه": {"total_days": 365},
    "کارشناس دفتر فنی": {"total_days": 365},
    # ایمنی
    "مسئول ایمنی": {"total_days": 365},
    "افسر ایمنی": {"total_days": 365},
    # پشتیبانی و اداری
    "مسئول پشتیبانی": {"total_days": 365},
    "مسئول ماشین آلات": {"total_days": 365},
    "کارشناس نت ماشین آلات": {"total_days": 365},
    "امور داخلی کارگاه": {"total_days": 365},
    "مسئول حراست": {"total_days": 365},
    "کارگر گریدر": {"total_days": 365},
    "انباردار": {"total_days": 365},
    "اداری-مالی": {"total_days": 365},
    "کارپرداز": {"total_days": 365},
    "مباشر": {"total_days": 365},
    "تاسیسات": {"total_days": 365},
    "برق کار (ماشین آلات)": {"total_days": 365},
    # رانندگان
    "راننده گریدر": {"total_days": 365},
    "راننده لودر": {"total_days": 365},
    "راننده بیل": {"total_days": 365},
    "راننده غلطک": {"total_days": 365},
    "راننده کامیون": {"total_days": 365},
    "راننده جرثقیل": {"total_days": 365},
    "راننده آبپاش": {"total_days": 365},
    "راننده میکسر": {"total_days": 365},
    "راننده جارو": {"total_days": 365},
    "راننده کمرشکن": {"total_days": 365},
    # کارگران و خدمات
    "کارگر": {"total_days": 365},
    "خدمات": {"total_days": 365},
    "کنترلچی": {"total_days": 365},
    "نگهبان": {"total_days": 365},
    "سرویس کار": {"total_days": 365},
    "مکانیک": {"total_days": 365},
    "اپراتور بچینگ": {"total_days": 365},
}

# =============================================================================
# EQUIPMENT & PLANNED QUANTITIES
# Single source: type → {model → {planned_quantity}}
# The equipment types and models list is derived from the keys.
# Use "default" key for equipment without specific models.
# =============================================================================
EQUIPMENT_COSTS = {
    "لودر": {"default": {"planned_quantity": 4}},
    "تجهیزات کامل سنگ شکن و ماسه ساز": {"default": {"planned_quantity": 1}},
    "غلطک چرخ لاستیکی": {"default": {"planned_quantity": 4}},
    "قیرپاش": {"default": {"planned_quantity": 1}},
    "کامیون": {"default": {"planned_quantity": 20}},
    "جاروی مکانیکی": {"default": {"planned_quantity": 1}},
    "کمپرسور باد": {"default": {"planned_quantity": 1}},
    "اتومبیل سبک": {"default": {"planned_quantity": 6}},
    "گریدر": {"default": {"planned_quantity": 4}},
    "کامیون آب پاش": {"default": {"planned_quantity": 6}},
    "غلطک ویبره": {"default": {"planned_quantity": 8}},
    "فینیشر پخش آسفالت گرم": {"default": {"planned_quantity": 1}},
    "بیل مکانیکی": {"default": {"planned_quantity": 2}},
    "بولدوزر": {"default": {"planned_quantity": 1}},
    "کارخانه آسفالت": {"default": {"planned_quantity": 1}},
    "بچینگ تولید بتن": {"default": {"planned_quantity": 1}},
    "میکسر حمل بتن": {"default": {"planned_quantity": 6}},
    "پمپ تخلیه بتن": {"default": {"planned_quantity": 1}},
    "غلطک چرخ فلزی": {"default": {"planned_quantity": 4}},
    "دستگاه قطع و خم آرماتور": {"default": {"planned_quantity": 2}},
    "ویبراتور": {"default": {"planned_quantity": 4}},
    "دستگاه آسفالت سطحی(چیپسیلر)": {"default": {"planned_quantity": 1}},
    "دستگاه آسفالت حفاظتی(اسلاری سیل)": {"default": {"planned_quantity": 1}},
}

# =============================================================================
# MATERIAL PRICES (Rial per unit) & PLANNED TOTALS
# Single source: material → {unit, price_per_unit, planned_total}
# The materials list and units are derived from this dict.
# =============================================================================
MATERIAL_PRICES = {
    # خاک و ماسه
    "شن و ماسه": {"unit": "تن (ton)", "price_per_unit": 45000, "planned_total": 2000},
    "شن و ماسه و بادامی": {"unit": "تن (ton)", "price_per_unit": 50000, "planned_total": 1500},
    "ماسه بادی": {"unit": "تن (ton)", "price_per_unit": 40000, "planned_total": 1000},
    "ماسه شکسته": {"unit": "تن (ton)", "price_per_unit": 55000, "planned_total": 800},
    # آسفالت و قیر
    "آسفالت": {"unit": "تن (ton)", "price_per_unit": 280000, "planned_total": 500},
    "پریمکت": {"unit": "کیلوگرم (kg)", "price_per_unit": 12, "planned_total": 1500},
    "قیر امولسیون": {"unit": "کیلوگرم (kg)", "price_per_unit": 8, "planned_total": 2000},
    "قیر خالص": {"unit": "تن (ton)", "price_per_unit": 320000, "planned_total": 150},
    # بتن و سیمان
    "بتن آماده": {"unit": "متر مکعب (m³)", "price_per_unit": 420000, "planned_total": 100},
    "سیمان": {"unit": "تن (ton)", "price_per_unit": 180000, "planned_total": 80},
    # آهن آلات
    "آهن آلات": {"unit": "کیلوگرم (kg)", "price_per_unit": 85, "planned_total": 3000},
    "میلگرد": {"unit": "کیلوگرم (kg)", "price_per_unit": 90, "planned_total": 2500},
    # مصالح جانبی
    "آجر": {"unit": "تعداد", "price_per_unit": 1500, "planned_total": 5000},
    "بلوک سیمانی": {"unit": "تعداد", "price_per_unit": 3500, "planned_total": 2000},
    # سایع و کمکی
    "پاورشل": {"unit": "کیلوگرم (kg)", "price_per_unit": 22, "planned_total": 500},
    "روان کننده": {"unit": "لیتر (L)", "price_per_unit": 15000, "planned_total": 100},
    "پرایمر": {"unit": "لیتر (L)", "price_per_unit": 35000, "planned_total": 50},
    "ضدیخ بتن": {"unit": "لیتر (L)", "price_per_unit": 25000, "planned_total": 30},
    # آب و سوخت
    "گازوئیل": {"unit": "لیتر (L)", "price_per_unit": 28000, "planned_total": 200},
    "آب تجهیز": {"unit": "متر مکعب (m³)", "price_per_unit": 15000, "planned_total": 500},
    "آب عملیات خاکی": {"unit": "متر مکعب (m³)", "price_per_unit": 8000, "planned_total": 1000},
    # پروفیل و فلزی
    "پروفیل سقف": {"unit": "کیلوگرم (kg)", "price_per_unit": 120, "planned_total": 800},
    # میلگردهای مختلف
    "میلگرد سایز 8": {"unit": "کیلوگرم (kg)", "price_per_unit": 92, "planned_total": 200},
    "میلگرد سایز 10": {"unit": "کیلوگرم (kg)", "price_per_unit": 91, "planned_total": 300},
    "میلگرد سایز 12": {"unit": "کیلوگرم (kg)", "price_per_unit": 90, "planned_total": 400},
    "میلگرد سایز 16": {"unit": "کیلوگرم (kg)", "price_per_unit": 89, "planned_total": 500},
    "میلگرد سایز 18": {"unit": "کیلوگرم (kg)", "price_per_unit": 88, "planned_total": 600},
    "میلگرد سایز 20": {"unit": "کیلوگرم (kg)", "price_per_unit": 87, "planned_total": 700},
    "میلگرد سایز 25": {"unit": "کیلوگرم (kg)", "price_per_unit": 86, "planned_total": 800},
    "میلگرد سایز 32": {"unit": "کیلوگرم (kg)", "price_per_unit": 85, "planned_total": 600},
}

# =============================================================================
# ACTIVITY BUDGET & PRICING
# Single source: activity → {unit, planned_amount, price_per_unit}
# The activities list and units are derived from this dict.
# =============================================================================
ACTIVITY_BUDGET = {
    # تجهیز و عملیات اولیه
    "تجهیز کارگاه": {"unit": "درصد (%)", "planned_amount": 100, "price_per_unit": 3.36},
    "بوته کنی": {"unit": "متر مربع (m²)", "planned_amount": 633988, "price_per_unit": 0.03},
    "تخریب بتن": {"unit": "متر مکعب (m³)", "planned_amount": 40, "price_per_unit": 0.01},
    "تخریب آسفالت": {"unit": "متر مکعب (m³)", "planned_amount": 2000, "price_per_unit": 0.01},
    "خاکبرداری دستی": {"unit": "متر مکعب (m³)", "planned_amount": 2103, "price_per_unit": 0.05},
    # عملیات خاکی
    "شخم زنی": {"unit": "متر مربع (m²)", "planned_amount": 702741, "price_per_unit": 0.08},
    "برداشت خاک نباتی(دکوپاژ)": {"unit": "متر مکعب (m³)", "planned_amount": 95098, "price_per_unit": 0.20},
    "خاکبرداری با ماشین": {"unit": "متر مکعب (m³)", "planned_amount": 275632, "price_per_unit": 2.14},
    "پی کنی": {"unit": "متر مکعب (m³)", "planned_amount": 17444, "price_per_unit": 0.34},
    "خاکریزی": {"unit": "متر مکعب (m³)", "planned_amount": 983980, "price_per_unit": 27.74},
    "بستر کوبی": {"unit": "متر مربع (m²)", "planned_amount": 742701, "price_per_unit": 0.29},
    "درناژ": {"unit": "متر مکعب (m³)", "planned_amount": 5542, "price_per_unit": 0.19},
    # ابنیه و سازه
    "بنایی با سنگ لاشه": {"unit": "متر مکعب (m³)", "planned_amount": 1320, "price_per_unit": 0.25},
    "بندکشی نمای سنگی": {"unit": "متر مربع (m²)", "planned_amount": 100, "price_per_unit": 0.00},
    "قالب بندی": {"unit": "متر مربع (m²)", "planned_amount": 45837, "price_per_unit": 2.35},
    "تهیه ، بریدن ، خم کردن میلگرد": {"unit": "کیلوگرم (kg)", "planned_amount": 413477, "price_per_unit": 2.57},
    "بولت": {"unit": "کیلوگرم (kg)", "planned_amount": 22176, "price_per_unit": 0.23},
    "مصالح جان پناه و پایه تابلو": {"unit": "کیلوگرم (kg)", "planned_amount": 212177, "price_per_unit": 2.36},
    "اتصالات": {"unit": "کیلوگرم (kg)", "planned_amount": 109501, "price_per_unit": 0.98},
    "بتن ریزی": {"unit": "متر مکعب (m³)", "planned_amount": 26951, "price_per_unit": 7.46},
    "اجرای جدول بتنی": {"unit": "متر مکعب (m³)", "planned_amount": 20, "price_per_unit": 0.01},
    "نیوجرسی": {"unit": "متر مکعب (m³)", "planned_amount": 6753, "price_per_unit": 3.34},
    "پل های باکسی(جعبه ای)": {"unit": "متر مکعب (m³)", "planned_amount": 64, "price_per_unit": 0.02},
    # زیرسازی و روسازی
    "زیر اساس": {"unit": "متر مکعب (m³)", "planned_amount": 68565, "price_per_unit": 3.29},
    "اساس": {"unit": "متر مکعب (m³)", "planned_amount": 69426, "price_per_unit": 5.65},
    "پریمکت": {"unit": "کیلوگرم (kg)", "planned_amount": 367200, "price_per_unit": 1.68},
    "قیر امولسیون(تک کت)": {"unit": "کیلوگرم (kg)", "planned_amount": 523320, "price_per_unit": 2.03},
    "آسفالت سطحی": {"unit": "تن (ton)", "planned_amount": 2409, "price_per_unit": 0.27},
    "اساس قیری": {"unit": "متر مربع (m²)", "planned_amount": 2555700, "price_per_unit": 11.50},
    "بیندر25-0": {"unit": "متر مربع (m²)", "planned_amount": 2167200, "price_per_unit": 11.43},
    "بیندر 19-0": {"unit": "متر مربع (m²)", "planned_amount": 1432800, "price_per_unit": 7.74},
    "اجرای اسلاری سیل": {"unit": "متر مربع (m²)", "planned_amount": 109500, "price_per_unit": 0.54},
    # عایق و تکمیلی
    "عایقکاری": {"unit": "متر مربع (m²)", "planned_amount": 17553, "price_per_unit": 0.24},
    "خط کشی منقطع": {"unit": "متر (m)", "planned_amount": 60000, "price_per_unit": 0.08},
    "خط کشی متصل": {"unit": "متر (m)", "planned_amount": 120000, "price_per_unit": 0.39},
    "صفحه تابلو": {"unit": "متر مربع (m²)", "planned_amount": 1320, "price_per_unit": 0.74},
    "زنگ زدایی": {"unit": "کیلوگرم (kg)", "planned_amount": 5000, "price_per_unit": 0.00},
    "ضدزنگ": {"unit": "کیلوگرم (kg)", "planned_amount": 5000, "price_per_unit": 0.00},
    "نایلون پلی اتیلن": {"unit": "متر مربع (m²)", "planned_amount": 234012, "price_per_unit": 0.42},
    "لوله پلاستیکی": {"unit": "کیلوگرم (kg)", "planned_amount": 277, "price_per_unit": 0.01},
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
        # Derived from MATERIAL_PRICES (extract unit)
        "Incoming_Materials": {name: info["unit"] for name, info in MATERIAL_PRICES.items()},
        "Incoming_Materials_And_Goods": {name: info["unit"] for name, info in MATERIAL_PRICES.items()},
        "Material_Prices": MATERIAL_PRICES,
        # Derived from ACTIVITY_BUDGET (extract unit)
        "Daily_Activity_Report": {name: info["unit"] for name, info in ACTIVITY_BUDGET.items()},
        "Activity_Budget": ACTIVITY_BUDGET,
        "Climate_Condition": CLIMATE_CONDITIONS,
        "Project_Issues": PROJECT_ISSUES,
    }


def get_project_info():
    """Return project basic information."""
    return PROJECT_INFO
