"""
=============================================================================
PROJECT-01 CONFIGURATION
احداث تقاطع غیر همسطح ورودی و پل دو دهانه بتنی - کاریزبوم یزد
=============================================================================
"""

# Set to True after you have filled in all the values
is_configured = False  # TODO: Set to True after filling values

# =============================================================================
# PROJECT BASIC INFORMATION
# =============================================================================
PROJECT_INFO = {
    "project_code": "Project-01",
    "name": "احداث تقاطع غیر همسطح ورودی و پل دو دهانه بتنی بر روی دره زنجیر پردیس ۲۵۰ هکتاری مجتمع تفریحی، فرهنگی و توریستی کوثر یزد (کاریزبوم)",
    "location": "یزد",
    "contract_number": "124012300",
    "start_date": "2022-08-14",
    "end_date": "2024-10-07",
    "budget": 761693497874.0,
    "owner": "کوثر",
    "manager": "دکتر امیری",
    "description": "",
}

# =============================================================================
# HUMAN RESOURCES
# List of job positions available for this project
# =============================================================================
HUMAN_RESOURCES = [
    "مدیر پروژه",
    "سرپرست کارگاه",
    "معاونت اجراء",
    "مسئول ابنیه فنی",
    "سرپرست دفتر فنی",
    "کارشناس دفتر فنی",
    "نقشه بردار",
    "کمک نقشه بردار",
    "مباشر عملیات خاکی",
    "مسئول کنترل پروژه",
    "اداری- مالی",
    "کارپرداز",
    "کارشناس ایمنی",
    "سرپرست ماشین آلات",
    "راننده سنگین",
    "راننده ویژه",
    "راننده سبک",
    "مکانیک",
    "سرویس کار",
    "انباردار",
    "مسئول حراست",
    "نگهبان",
    "مسئول امور داخلی",
    "تاسیسات",
    "استاد کار بنایی",
    "کارگر",
    "کارگر ساده",
    "خدمات",
    "تکنسین آزمایشگاه",
    "کارگر آزمایشگاه",
    "اکیپ تاسیسات برق",
    "آرماتوربند",
    "قالب بند",
    "بتن ریز",
    "عایق کار",
    "اکیپ آسفالت",
]

# =============================================================================
# HUMAN RESOURCES RATES (Rial per hour)
# =============================================================================
HUMAN_RESOURCES_RATES = {
    "مدیر پروژه": {"hourly_rate": 100},  # TODO: Fill rate
    "سرپرست کارگاه": {"hourly_rate": 100},
    "معاونت اجراء": {"hourly_rate": 100},
    "مسئول ابنیه فنی": {"hourly_rate": 100},
    "سرپرست دفتر فنی": {"hourly_rate": 100},
    "کارشناس دفتر فنی": {"hourly_rate": 100},
    "نقشه بردار": {"hourly_rate": 100},
    "کمک نقشه بردار": {"hourly_rate": 100},
    "مباشر عملیات خاکی": {"hourly_rate": 100},
    "مسئول کنترل پروژه": {"hourly_rate": 100},
    "اداری- مالی": {"hourly_rate": 100},
    "کارپرداز": {"hourly_rate": 100},
    "کارشناس ایمنی": {"hourly_rate": 100},
    "سرپرست ماشین آلات": {"hourly_rate": 100},
    "راننده سنگین": {"hourly_rate": 100},
    "راننده ویژه": {"hourly_rate": 100},
    "راننده سبک": {"hourly_rate": 100},
    "مکانیک": {"hourly_rate": 100},
    "سرویس کار": {"hourly_rate": 100},
    "انباردار": {"hourly_rate": 100},
    "مسئول حراست": {"hourly_rate": 100},
    "نگهبان": {"hourly_rate": 100},
    "مسئول امور داخلی": {"hourly_rate": 100},
    "تاسیسات": {"hourly_rate": 100},
    "استاد کار بنایی": {"hourly_rate": 100},
    "کارگر": {"hourly_rate": 100},
    "کارگر ساده": {"hourly_rate": 100},
    "خدمات": {"hourly_rate": 100},
    "تکنسین آزمایشگاه": {"hourly_rate": 100},
    "کارگر آزمایشگاه": {"hourly_rate": 100},
    "اکیپ تاسیسات برق": {"hourly_rate": 100},
    "آرماتوربند": {"hourly_rate": 100},
    "قالب بند": {"hourly_rate": 100},
    "بتن ریز": {"hourly_rate": 100},
    "عایق کار": {"hourly_rate": 100},
    "اکیپ آسفالت": {"hourly_rate": 100},
}

# =============================================================================
# TOOLS AND EQUIPMENTS
# Dictionary: equipment_type -> [list of models]
# =============================================================================
TOOLS_AND_EQUIPMENTS = {
    "بیل مکانیکی": ["۲۲۰", "۳۶۰"],
    "لودر": ["۵ تن تیراژه"],
    "بولدوزر": ["کاترپیلار D6"],
    "کمپرسی": ["جفت", "تک"],
    "تانکر": ["آبپاش"],
    "گریدر": ["کوماتسو 661A", "کوماتسو GdA-705", "کاترپیلار 140G"],
    "غلتک": ["HC100B", "HC100C", "کششی", "چرخ فلزی", "چرخ لاستیکی"],
    "تراکتور": [],
    "وانت": [],
    "سواری": [],
    "ژنراتور": ["KVA 40", "KVA 150"],
    "موتور برق": [],
    "کمپرسور باد": [],
    "کانکس": [],
    "کانتینر": [],
    "مخزن": [],
    "بتونیر": ["دیزلی"],
    "سیلو": ["۱۰۰ تنی"],
    "جرثقیل": ["۲۵ تن", "۵۰ تن"],
    "تریلی": ["کفی"],
    "دستگاه خط‌کش": [],
    "میکسر بتن": [],
    "پمپ بتن": [],
    "فینیشر": [],
    "دوربین نقشه برداری": ["GPS", "توتال"],
    "کارخانه آسفالت": [],
    "بچینگ بتن": [],
}

# =============================================================================
# EQUIPMENT COSTS (Rial per hour) & PLANNED QUANTITIES
# =============================================================================
EQUIPMENT_COSTS = {
    "بیل مکانیکی": {
        "۲۲۰": {"hourly_rate": 100, "planned_quantity": 5},  # TODO: Fill values
        "۳۶۰": {"hourly_rate": 100, "planned_quantity": 5},
    },
    "لودر": {
        "۵ تن تیراژه": {"hourly_rate": 100, "planned_quantity": 5},
    },
    "بولدوزر": {
        "کاترپیلار D6": {"hourly_rate": 100, "planned_quantity": 5},
    },
    "کمپرسی": {
        "جفت": {"hourly_rate": 100, "planned_quantity": 5},
        "تک": {"hourly_rate": 100, "planned_quantity": 5},
    },
    "تانکر": {
        "آبپاش": {"hourly_rate": 100, "planned_quantity": 5},
    },
    "گریدر": {
        "کوماتسو 661A": {"hourly_rate": 100, "planned_quantity": 5},
        "کوماتسو GdA-705": {"hourly_rate": 100, "planned_quantity": 5},
        "کاترپیلار 140G": {"hourly_rate": 100, "planned_quantity": 5},
    },
    "غلتک": {
        "HC100B": {"hourly_rate": 100, "planned_quantity": 5},
        "HC100C": {"hourly_rate": 100, "planned_quantity": 5},
        "کششی": {"hourly_rate": 100, "planned_quantity": 5},
        "چرخ فلزی": {"hourly_rate": 0, "planned_quantity": 0},
        "چرخ لاستیکی": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "تراکتور": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "وانت": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "سواری": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "ژنراتور": {
        "KVA 40": {"hourly_rate": 0, "planned_quantity": 0},
        "KVA 150": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "موتور برق": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "کمپرسور باد": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "کانکس": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "کانتینر": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "مخزن": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "بتونیر": {
        "دیزلی": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "سیلو": {
        "۱۰۰ تنی": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "جرثقیل": {
        "۲۵ تن": {"hourly_rate": 0, "planned_quantity": 0},
        "۵۰ تن": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "تریلی": {
        "کفی": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "دستگاه خط‌کش": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "میکسر بتن": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "پمپ بتن": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "فینیشر": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "دوربین نقشه برداری": {
        "GPS": {"hourly_rate": 0, "planned_quantity": 0},
        "توتال": {"hourly_rate": 0, "planned_quantity": 0},
    },
    "کارخانه آسفالت": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
    "بچینگ بتن": {"default": {"hourly_rate": 0, "planned_quantity": 0}},
}

# =============================================================================
# INCOMING MATERIALS AND GOODS
# Dictionary: material_name -> unit
# =============================================================================
INCOMING_MATERIALS = {
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
# MATERIAL PRICES (Rial per unit) & PLANNED TOTALS
# =============================================================================
MATERIAL_PRICES = {
    "شن و ماسه": {"price_per_unit": 100, "planned_total": 1000},  # TODO: Fill values
    "شن و ماسه و بادامی": {"price_per_unit": 100, "planned_total": 1000},
    "آسفالت": {"price_per_unit": 100, "planned_total": 1000},
    "بتن آماده": {"price_per_unit": 100, "planned_total": 1000},
    "آجر": {"price_per_unit": 100, "planned_total": 1000},
    "آهن آلات": {"price_per_unit": 100, "planned_total": 1000},
    "سیمان": {"price_per_unit": 100, "planned_total": 1000},
    "ماسه بادی": {"price_per_unit": 100, "planned_total": 1000},
    "ماسه شکسته": {"price_per_unit": 100, "planned_total": 1000},
    "گازوئیل": {"price_per_unit": 0, "planned_total": 0},
    "بلوک سیمانی": {"price_per_unit": 0, "planned_total": 0},
    "آب تجهیز": {"price_per_unit": 0, "planned_total": 0},
    "آب عملیات خاکی": {"price_per_unit": 0, "planned_total": 0},
    "پاورشل": {"price_per_unit": 0, "planned_total": 0},
    "روان کننده": {"price_per_unit": 0, "planned_total": 0},
    "پرایمر": {"price_per_unit": 0, "planned_total": 0},
    "ضدیخ بتن": {"price_per_unit": 0, "planned_total": 0},
    "قیر خالص": {"price_per_unit": 0, "planned_total": 0},
    "پروفیل سقف": {"price_per_unit": 0, "planned_total": 0},
    "میلگرد سایز 8": {"price_per_unit": 0, "planned_total": 0},
    "میلگرد سایز 10": {"price_per_unit": 0, "planned_total": 0},
    "میلگرد سایز 12": {"price_per_unit": 0, "planned_total": 0},
    "میلگرد سایز 16": {"price_per_unit": 0, "planned_total": 0},
    "میلگرد سایز 18": {"price_per_unit": 0, "planned_total": 0},
    "میلگرد سایز 20": {"price_per_unit": 0, "planned_total": 0},
    "میلگرد سایز 25": {"price_per_unit": 0, "planned_total": 0},
    "میلگرد سایز 32": {"price_per_unit": 0, "planned_total": 0},
}

# =============================================================================
# DAILY ACTIVITIES (Construction Operations)
# Dictionary: activity_name -> unit
# =============================================================================
DAILY_ACTIVITIES = {
    "خاکریزی": "متر مکعب (m³)",
    "خاکبرداری": "متر مکعب (m³)",
    "بارریزی": "متر مکعب (m³)",
    "کوبیدن لایه خاکریز": "متر مربع (m²)",
    "کوبیدن لایه بستر": "متر مربع (m²)",
    "اجرای لایه ساب بیس(زیراساس)": "متر مکعب (m³)",
    "اجرای بیس(اساس)": "متر مکعب (m³)",
    "پریمکوت": "متر مربع (m²)",
    "تک کت": "متر مربع (m²)",
    "اجرای اسفالت گرم": "تن (ton)",
    "آسفالت‌ریزی": "تن (ton)",
    "خطکشی مسیر": "متر (m)",
    "پی کنی": "متر مکعب (m³)",
    "پی‌ریزی": "متر مکعب (m³)",
    "اجرای شفته": "متر مکعب (m³)",
    "اجرای بتن مگر": "متر مکعب (m³)",
    "قالب بندی": "متر مربع (m²)",
    "قالب‌بندی": "متر مربع (m²)",
    "آرماتور بندی": "کیلوگرم (kg)",
    "آرماتوربندی": "کیلوگرم (kg)",
    "بتن ریزی": "متر مکعب (m³)",
    "بتن‌ریزی": "متر مکعب (m³)",
    "آرماتوربندی آپردال باکس": "کیلوگرم (kg)",
    "اجرای باکس": "تعداد",
    "اجرای نیوجرسی": "متر (m)",
    "انتقال ترافیک": "متر (m)",
    "عایق کاری": "متر مربع (m²)",
    "سنگ‌کاری": "متر مربع (m²)",
    "آجرچینی": "متر مربع (m²)",
    "شخم زنی": "متر مربع (m²)",
}

# =============================================================================
# ACTIVITY BUDGET & PRICING
# =============================================================================
ACTIVITY_BUDGET = {
    # عملیات خاکی و زیرسازی
    "خاکریزی": {"planned_amount": 1000, "price_per_unit": 100},  # TODO: Fill values
    "خاکبرداری": {"planned_amount": 1000, "price_per_unit": 100},
    "بارریزی": {"planned_amount": 1000, "price_per_unit": 100},
    "کوبیدن لایه خاکریز": {"planned_amount": 0, "price_per_unit": 0},
    "کوبیدن لایه بستر": {"planned_amount": 0, "price_per_unit": 0},
    "اجرای لایه ساب بیس(زیراساس)": {"planned_amount": 0, "price_per_unit": 0},
    "اجرای بیس(اساس)": {"planned_amount": 0, "price_per_unit": 0},
    
    # آسفالت
    "پریمکوت": {"planned_amount": 0, "price_per_unit": 0},
    "تک کت": {"planned_amount": 0, "price_per_unit": 0},
    "اجرای اسفالت گرم": {"planned_amount": 0, "price_per_unit": 0},
    "آسفالت‌ریزی": {"planned_amount": 0, "price_per_unit": 0},
    "خطکشی مسیر": {"planned_amount": 0, "price_per_unit": 0},
    
    # ابنیه فنی و بتن
    "پی کنی": {"planned_amount": 0, "price_per_unit": 0},
    "پی‌ریزی": {"planned_amount": 0, "price_per_unit": 0},
    "اجرای شفته": {"planned_amount": 0, "price_per_unit": 0},
    "اجرای بتن مگر": {"planned_amount": 0, "price_per_unit": 0},
    "قالب بندی": {"planned_amount": 0, "price_per_unit": 0},
    "قالب‌بندی": {"planned_amount": 0, "price_per_unit": 0},
    "آرماتور بندی": {"planned_amount": 0, "price_per_unit": 0},
    "آرماتوربندی": {"planned_amount": 0, "price_per_unit": 0},
    "بتن ریزی": {"planned_amount": 0, "price_per_unit": 0},
    "بتن‌ریزی": {"planned_amount": 0, "price_per_unit": 0},
    "آرماتوربندی آپردال باکس": {"planned_amount": 0, "price_per_unit": 0},
    "اجرای باکس": {"planned_amount": 0, "price_per_unit": 0},
    
    # سایر
    "اجرای نیوجرسی": {"planned_amount": 0, "price_per_unit": 0},
    "انتقال ترافیک": {"planned_amount": 0, "price_per_unit": 0},
    "عایق کاری": {"planned_amount": 0, "price_per_unit": 0},
    "سنگ‌کاری": {"planned_amount": 0, "price_per_unit": 0},
    "آجرچینی": {"planned_amount": 0, "price_per_unit": 0},
    "شخم زنی": {"planned_amount": 0, "price_per_unit": 0},
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
# DO NOT MODIFY BELOW THIS LINE
# =============================================================================
def get_configuration():
    """Convert this config file to the standard configuration format."""
    return {
        "Date_And_Time": [
            "کد سند",
            "تاریخ",
            "روز هفته",
            "شیفت کاری",
        ],
        "Human_Resources": HUMAN_RESOURCES,
        "Human_Resources_Rates": HUMAN_RESOURCES_RATES,
        "Tools_And_Equipments": TOOLS_AND_EQUIPMENTS,
        "Equipment_Costs": EQUIPMENT_COSTS,
        "Incoming_Materials_And_Goods": INCOMING_MATERIALS,
        "Material_Prices": MATERIAL_PRICES,
        "Daily_Activity_Report": DAILY_ACTIVITIES,
        "Activity_Budget": ACTIVITY_BUDGET,
        "Climate_Condition": CLIMATE_CONDITIONS,
        "Project_Issues": PROJECT_ISSUES,
    }


def get_project_info():
    """Return project basic information."""
    return PROJECT_INFO
