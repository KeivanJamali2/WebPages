"""
=============================================================================
Daily Form Configuration - Bridge Module
=============================================================================

This module provides backward-compatible access to project configurations.
The actual configurations are stored in individual files under:
    Projects/project_configurations/

For new code, import directly from Projects.project_configurations:
    from Projects.project_configurations import load_project_config, get_activities

For legacy code, this module still works:
    from forms.daily_form_configuration import get_configuration_for_project
"""

import copy
import os
import sys

# Add Projects to path if needed
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import from the new configuration system
from Projects.project_configurations import (
    load_project_config,
    load_project_info,
    list_available_projects,
    get_human_resources,
    get_human_resources_rates,
    get_equipment_types as _get_equipment_types,
    get_equipment_costs,
    get_materials,
    get_material_prices,
    get_activities,
    get_activity_budget as _get_activity_budget,
    get_project_issues,
    get_climate_conditions,
    is_project_configured,
    reload_project_config,
)


# =============================================================================
# DEFAULT CONFIGURATION (for backward compatibility)
# This is used when no project is specified
# =============================================================================

DEFAULT_CONFIGURATION = {
    "Date_And_Time": [
        "کد سند",
        "تاریخ",
        "روز هفته",
        "شیفت کاری",
    ],
    
    "Human_Resources": [
        "مدیر پروژه",
        "سرپرست کارگاه",
        "معاونت اجراء",
        "مسئول اجرا",
        "مسئول ابنیه فنی",
        "سرپرست دفتر فنی",
        "کارشناس دفتر فنی",
        "نقشه بردار",
        "کمک نقشه بردار",
        "مباشر عملیات خاکی",
        "مسئول کنترل پروژه",
        "کنترل پروژه",
        "اداری- مالی",
        "حسابدار",
        "کارپرداز",
        "تدارکات",
        "کارشناس ایمنی",
        "مسئول HSE",
        "سرپرست ماشین آلات",
        "کارشناس نت ماشین آلات",
        "راننده سنگین",
        "راننده ماشین سنگین",
        "راننده ویژه",
        "راننده سبک",
        "راننده سواری و وانت",
        "مکانیک",
        "سرویس کار",
        "انباردار",
        "مسئول حراست",
        "نگهبان",
        "مسئول امور داخلی",
        "تاسیسات",
        "برقکار",
        "استاد کار بنایی",
        "بنا",
        "کارگر",
        "کارگر ساده",
        "بتن ریز",
        "جوشکار",
        "آرماتوربند",
        "قالب بند",
        "عایق کار",
        "خدمات",
        "تکنسین آزمایشگاه",
        "کارگر آزمایشگاه",
        "نصاب ساندویچ پنل",
        "اکیپ تاسیسات برق",
        "اکیپ آسفالت",
    ],
    
    "Tools_And_Equipments": {
        "بیل مکانیکی": ["۲۲۰", "۳۶۰", "کارفرما"],
        "لودر": ["۵ تن تیراژه", "کارفرما"],
        "بولدوزر": ["کاترپیلار D6", "کاترپیلار D8", "کارفرما"],
        "جرثقیل": ["۲۵ تن", "۵۰ تن", "۱۰۰ تن"],
        "کمپرسی": ["تک", "جفت", "۱۰ چرخ"],
        "تانکر": ["آب", "آبپاش", "گازوئیل"],
        "گریدر": ["کوماتسو 661A", "کوماتسو GdA-705", "کاترپیلار 140G"],
        "غلتک": ["HC100B", "HC100C", "کششی", "چرخ فلزی", "چرخ لاستیکی"],
        "تریلی": ["کفی", "کمرشکن"],
        "تراکتور": [],
        "وانت": [],
        "سواری": [],
        "دوربین نقشه برداری": ["GPS", "توتال"],
        "ژنراتور": ["KVA 40", "KVA 150", "KVA 250"],
        "موتور جوش": [],
        "موتور برق": [],
        "کمپرسور باد": [],
        "کانکس": [],
        "کانتینر": [],
        "مخزن": [],
        "بتونیر": ["دیزلی", "برقی"],
        "سیلو": ["۵۰ تنی", "۱۰۰ تنی"],
        "میکسر بتن": [],
        "پمپ بتن": [],
        "فینیشر": [],
        "دستگاه خط‌کش": [],
        "کارخانه آسفالت": [],
        "بچینگ بتن": [],
    },
    
    "Incoming_Materials_And_Goods": {
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
    },
    
    "Climate_Condition": [
        "حداقل دمای هوا",
        "حداکثر دمای هوا",
        "رطوبت هوا",
        "صاف",
        "ابری",
        "بارانی",
        "مه‌آلود",
        "برفی",
    ],
    
    "Daily_Activity_Report": {
        "خاکریزی": "متر مکعب (m³)",
        "خاکبرداری": "متر مکعب (m³)",
        "پی‌ریزی": "متر مکعب (m³)",
        "آرماتوربندی": "کیلوگرم (kg)",
        "قالب‌بندی": "متر مربع (m²)",
        "بتن‌ریزی": "متر مکعب (m³)",
        "آسفالت‌ریزی": "تن (ton)",
        "سنگ‌کاری": "متر مربع (m²)",
        "آجرچینی": "متر مربع (m²)",
        "شخم زنی": "متر مربع (m²)",
        "بارریزی": "متر مکعب (m³)",
        "کوبیدن لایه خاکریز": "متر مربع (m²)",
        "کوبیدن لایه بستر": "متر مربع (m²)",
        "اجرای لایه ساب بیس(زیراساس)": "متر مکعب (m³)",
        "اجرای بیس(اساس)": "متر مکعب (m³)",
        "پریمکوت": "متر مربع (m²)",
        "تک کت": "متر مربع (m²)",
        "اجرای اسفالت گرم": "تن (ton)",
        "خطکشی مسیر": "متر (m)",
        "پی کنی": "متر مکعب (m³)",
        "اجرای شفته": "متر مکعب (m³)",
        "اجرای بتن مگر": "متر مکعب (m³)",
        "قالب بندی": "متر مربع (m²)",
        "آرماتور بندی": "کیلوگرم (kg)",
        "بتن ریزی": "متر مکعب (m³)",
        "اجرای باکس": "تعداد",
        "آرماتوربندی آپردال باکس": "کیلوگرم (kg)",
        "اجرای نیوجرسی": "متر (m)",
        "انتقال ترافیک": "متر (m)",
        "عایق کاری": "متر مربع (m²)",
    },
    
    "Project_Issues": [
        "معضلات مردمی",
        "مشکلات تامین مصالح",
        "مشکلات نیروی انسانی",
        "مشکلات تجهیزاتی",
        "مسائل مالی",
        "مسائل فنی",
    ],
}


# =============================================================================
# BACKWARD COMPATIBLE FUNCTIONS
# =============================================================================

def get_configuration_for_project(project_code):
    """
    Get the configuration for a specific project.
    
    Args:
        project_code: The project code (e.g., "Project-01", "Project-02")
        
    Returns:
        Complete configuration dict for the project
    """
    try:
        return load_project_config(project_code)
    except FileNotFoundError:
        # Fall back to default if project config not found
        return copy.deepcopy(DEFAULT_CONFIGURATION)


def get_default_configuration():
    """
    Get the default configuration (all options).
    
    Returns:
        Default configuration dict
    """
    return copy.deepcopy(DEFAULT_CONFIGURATION)


def get_equipment_types(project_code=None):
    """
    Get list of equipment types for a project.
    
    Args:
        project_code: The project code, or None for default
        
    Returns:
        List of equipment type names
    """
    if project_code:
        try:
            equipment = _get_equipment_types(project_code)
            return list(equipment.keys())
        except FileNotFoundError:
            pass
    
    return list(DEFAULT_CONFIGURATION.get("Tools_And_Equipments", {}).keys())


def get_equipment_models(equipment_type, project_code=None):
    """
    Get list of models for a specific equipment type.
    
    Args:
        equipment_type: The equipment type name
        project_code: The project code, or None for default
        
    Returns:
        List of model names (can be empty)
    """
    if project_code:
        try:
            equipment = _get_equipment_types(project_code)
            return equipment.get(equipment_type, [])
        except FileNotFoundError:
            pass
    
    return DEFAULT_CONFIGURATION.get("Tools_And_Equipments", {}).get(equipment_type, [])


def get_activity_budget(activity_name, project_code=None):
    """
    Get the budget info (planned_amount, price_per_unit) for an activity.
    
    Args:
        activity_name: The activity name
        project_code: The project code, or None for default
        
    Returns:
        Dict with 'planned_amount' and 'price_per_unit', or None if not found
    """
    if project_code:
        try:
            budget = _get_activity_budget(project_code)
            return budget.get(activity_name)
        except FileNotFoundError:
            pass
    
    return None


def get_all_activity_budgets(project_code=None):
    """
    Get all activity budgets for a project.
    
    Args:
        project_code: The project code, or None for default
        
    Returns:
        Dict of activity_name -> {planned_amount, price_per_unit}
    """
    if project_code:
        try:
            return _get_activity_budget(project_code)
        except FileNotFoundError:
            pass
    
    return {}


def get_planned_equipment(project_code=None):
    """
    Get all planned equipment quantities for a project.
    
    Args:
        project_code: The project code, or None for default
        
    Returns:
        Dict of equipment_type -> {model: {hourly_rate, planned_quantity}}
    """
    if project_code:
        try:
            return get_equipment_costs(project_code)
        except FileNotFoundError:
            pass
    
    return {}


def get_planned_equipment_quantity(equipment_type, model=None, project_code=None):
    """
    Get the planned quantity for a specific equipment type/model.
    
    Args:
        equipment_type: The equipment type name
        model: The model name (use 'default' or None for equipment without models)
        project_code: The project code, or None for default
        
    Returns:
        The planned quantity (int), or 0 if not found
    """
    planned = get_planned_equipment(project_code)
    equipment = planned.get(equipment_type, {})
    
    if model:
        return equipment.get(model, {}).get("planned_quantity", 0)
    elif "default" in equipment:
        return equipment.get("default", {}).get("planned_quantity", 0)
    else:
        # Sum all models if no specific model requested
        return sum(m.get("planned_quantity", 0) for m in equipment.values() if isinstance(m, dict))


# =============================================================================
# NEW FUNCTIONS FOR COST ANALYSIS
# =============================================================================

def get_hr_hourly_rate(position, project_code):
    """
    Get the hourly rate for a human resource position.
    
    Args:
        position: The position name
        project_code: The project code
        
    Returns:
        Hourly rate in Rial, or 0 if not found
    """
    try:
        rates = get_human_resources_rates(project_code)
        return rates.get(position, {}).get("hourly_rate", 0)
    except FileNotFoundError:
        return 0


def get_equipment_hourly_rate(equipment_type, model, project_code):
    """
    Get the hourly rate for equipment.
    
    Args:
        equipment_type: The equipment type
        model: The model name (or 'default')
        project_code: The project code
        
    Returns:
        Hourly rate in Rial, or 0 if not found
    """
    try:
        costs = get_equipment_costs(project_code)
        equipment = costs.get(equipment_type, {})
        return equipment.get(model, {}).get("hourly_rate", 0)
    except FileNotFoundError:
        return 0


def get_material_price(material_name, project_code):
    """
    Get the price per unit for a material.
    
    Args:
        material_name: The material name
        project_code: The project code
        
    Returns:
        Price per unit in Rial, or 0 if not found
    """
    try:
        prices = get_material_prices(project_code)
        return prices.get(material_name, {}).get("price_per_unit", 0)
    except FileNotFoundError:
        return 0


def get_activity_price(activity_name, project_code):
    """
    Get the price per unit for an activity.
    
    Args:
        activity_name: The activity name
        project_code: The project code
        
    Returns:
        Price per unit in Rial, or 0 if not found
    """
    try:
        budget = _get_activity_budget(project_code)
        return budget.get(activity_name, {}).get("price_per_unit", 0)
    except FileNotFoundError:
        return 0


# =============================================================================
# BACKWARD COMPATIBILITY - Keep old variable names
# =============================================================================

# Build project_configurations dict for any code still using it
project_configurations = {}
for project_code in list_available_projects():
    try:
        project_configurations[project_code] = load_project_config(project_code)
    except:
        pass

# Keep 'configuration' for backward compatibility (uses Project-01 or default)
try:
    configuration = load_project_config("Project-01")
except FileNotFoundError:
    configuration = copy.deepcopy(DEFAULT_CONFIGURATION)
