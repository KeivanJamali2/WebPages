#!/usr/bin/env python3
"""
=============================================================================
DAILY FORM EXCEL GENERATOR
=============================================================================

Generates random but realistic Excel files matching the daily form template.
These can be uploaded via the "Upload from Excel" feature.

USAGE:
    python generate_daily_forms.py --project Project-01 --start 1404/01/01 --end 1404/01/15 --shift both
    python generate_daily_forms.py --project Project-01 --start 1404/01/01 --end 1404/01/15 --shift morning
    python generate_daily_forms.py --project Project-01 --start 1404/01/01 --end 1404/01/15 --shift night --output ./output

OPTIONS:
    --project   Project code (e.g., Project-01, Project-02)
    --start     Start date in Jalali format (e.g., 1404/01/01)
    --end       End date in Jalali format (e.g., 1404/01/15)
    --shift     Shift type: morning, night, or both (default: both)
    --output    Output directory for generated files (default: ./generated_forms)
"""

import os
import sys
import random
import argparse
from datetime import timedelta

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir) if os.path.basename(script_dir) == 'utils' else script_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import jdatetime
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

# =============================================================================
# CONFIGURATION
# =============================================================================

# Persian weekday names indexed by jdatetime weekday (Saturday=0 ... Friday=6)
PERSIAN_WEEKDAYS = {
    0: 'شنبه',
    1: 'یکشنبه',
    2: 'دوشنبه',
    3: 'سه‌شنبه',
    4: 'چهارشنبه',
    5: 'پنج‌شنبه',
    6: 'جمعه'
}

WEATHER_TYPES = ['صاف', 'ابری', 'بارانی', 'مه‌آلود', 'برفی']
WEATHER_WEIGHTS = [50, 25, 15, 5, 5]  # Weighted random

WIND_SPEEDS = ['آرام', 'معمولی', 'تند']
WIND_WEIGHTS = [40, 45, 15]

CLIMATE_EFFECTS = ['بدون تاثیر', 'کندی پیشرفت', 'توقف کار']
CLIMATE_EFFECT_WEIGHTS = [70, 25, 5]

SAFETY_SITUATIONS = ['بدون حادثه', 'شبه حادثه', 'حادثه']
SAFETY_WEIGHTS = [85, 12, 3]

EQUIPMENT_SITUATIONS = ['فعال', 'غیرفعال', 'در حال تعمیر']
EQUIPMENT_SITUATION_WEIGHTS = [75, 15, 10]

EVENT_TYPES = ['بازدید', 'جلسه', 'سایر']

STORAGE_PLACES = ['انبار اصلی', 'انبار فرعی', 'کارگاه', 'محل پروژه', 'انبار مصالح']

INACTIVITY_REASONS = [
    'خرابی موتور', 'نیاز به سرویس', 'کمبود سوخت',
    'خرابی هیدرولیک', 'تعویض لاستیک', 'در انتظار قطعه',
    'عدم نیاز', 'نقص فنی'
]

SAMPLE_EVENT_NAMES = [
    'بازدید مدیرعامل', 'جلسه هماهنگی هفتگی', 'بازدید ناظر',
    'جلسه ایمنی', 'بازدید کارفرما', 'جلسه فنی',
    'بازرسی کارگاه', 'جلسه پیمانکاران', 'بازدید مشاور',
]

ISSUE_EFFECTS = [
    'تاخیر در پیشرفت', 'توقف موقت عملیات', 'افزایش هزینه',
    'کاهش کیفیت', 'بدون تاثیر قابل توجه', 'نیاز به بازنگری برنامه',
]


def load_project_configuration(project_code):
    """Load project configuration from the project_configurations package."""
    try:
        from Projects.project_configurations import load_project_config, load_project_info
        config = load_project_config(project_code)
        info = load_project_info(project_code)
        return config, info
    except Exception as e:
        print(f"Error loading configuration for {project_code}: {e}")
        print("Make sure you run this script from the V5 directory.")
        sys.exit(1)


def parse_jalali_date(date_str):
    """Parse Jalali date string (YYYY/MM/DD or YYYY-MM-DD) to jdatetime.date."""
    date_str = date_str.replace('/', '-')
    parts = date_str.split('-')
    return jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))


def jalali_to_gregorian(j_date):
    """Convert jdatetime.date to Gregorian date."""
    return j_date.togregorian()


def get_jalali_weekday(j_date):
    """Get Persian weekday name for a jdatetime.date."""
    # jdatetime weekday: Saturday=0, Sunday=1, ..., Friday=6
    return PERSIAN_WEEKDAYS.get(j_date.weekday(), '')


def weighted_choice(choices, weights):
    """Select a random choice with weights."""
    return random.choices(choices, weights=weights, k=1)[0]


def random_station(min_km=0, max_km=50):
    """Generate a random station in format 00+000."""
    km = random.randint(min_km, max_km)
    meters = random.choice([0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500,
                            550, 600, 650, 700, 750, 800, 850, 900, 950])
    return f"{km:02d}+{meters:03d}"


def random_time_str(hour_min=6, hour_max=18):
    """Generate a random time string in HH:MM format."""
    hour = random.randint(hour_min, hour_max)
    minute = random.choice([0, 15, 30, 45])
    return f"{hour:02d}:{minute:02d}"


def generate_single_form(config, project_info, j_date, shift, project_name):
    """
    Generate a single daily form Excel file with random data.

    Args:
        config: Project configuration dict
        project_info: Project info dict
        j_date: jdatetime.date for the form
        shift: 'صبح' or 'شب'
        project_name: Project name string

    Returns:
        openpyxl.Workbook
    """
    wb = openpyxl.Workbook()

    # Styles
    header_font = Font(bold=True, size=12, color="FFFFFF")
    header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
    section_font = Font(bold=True, size=14, color="FFFFFF")
    section_fill = PatternFill(start_color="059669", end_color="059669", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
    right_align = Alignment(horizontal='right', vertical='center', wrap_text=True)

    ws = wb.active
    ws.title = "فرم روزانه"
    ws.sheet_view.rightToLeft = True

    current_row = 1
    date_str = j_date.strftime('%Y/%m/%d')
    weekday = get_jalali_weekday(j_date)

    # ==================== Section 1: Date and Time ====================
    ws.merge_cells(f'A{current_row}:D{current_row}')
    ws[f'A{current_row}'] = "۱. تاریخ و زمان"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1

    headers = ["تاریخ (1404/01/01)", "روز هفته", "شیفت کاری", "پروژه"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col)].width = 20
    current_row += 1

    # Fill date/time data
    ws.cell(row=current_row, column=1, value=date_str).border = thin_border
    ws.cell(row=current_row, column=1).alignment = center_align
    ws.cell(row=current_row, column=2, value=weekday).border = thin_border
    ws.cell(row=current_row, column=2).alignment = center_align
    ws.cell(row=current_row, column=3, value=shift).border = thin_border
    ws.cell(row=current_row, column=3).alignment = center_align
    ws.cell(row=current_row, column=4, value=project_name).border = thin_border
    ws.cell(row=current_row, column=4).alignment = center_align
    current_row += 2

    # ==================== Section 2: Human Resources ====================
    ws.merge_cells(f'A{current_row}:D{current_row}')
    ws[f'A{current_row}'] = "۲. نیروی انسانی"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1

    hr_headers = ["سمت", "تعداد", "ساعت کار", "توضیحات"]
    for col, header in enumerate(hr_headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    current_row += 1

    positions = config.get("Human_Resources", [])
    hr_rates = config.get("Human_Resources_Rates", {})

    # Use total_days from config to decide who's likely to be present
    # Positions with more total_days are more likely to show up on any given day
    active_positions = []
    for pos in positions:
        total_days = hr_rates.get(pos, {}).get("total_days", 0)
        if total_days <= 0:
            # Low chance for unconfigured positions
            if random.random() < 0.15:
                active_positions.append(pos)
        else:
            # Probability = total_days / 365, capped at 0.95
            prob = min(total_days / 365.0, 0.95)
            if random.random() < prob:
                active_positions.append(pos)

    for position in positions:
        ws.cell(row=current_row, column=1, value=position).border = thin_border
        ws.cell(row=current_row, column=1).alignment = right_align
        if position in active_positions:
            # Managers/specialists get count=1, workers/drivers may get more
            total_days = hr_rates.get(position, {}).get("total_days", 0)
            if total_days <= 120:
                count = 1
            elif total_days <= 365:
                count = random.randint(1, 3)
            else:
                count = random.randint(1, 5)
            hours = random.choice([7, 7.5, 8, 8, 8, 8, 10, 10, 12])
            ws.cell(row=current_row, column=2, value=count).border = thin_border
            ws.cell(row=current_row, column=3, value=hours).border = thin_border
        else:
            ws.cell(row=current_row, column=2, value="").border = thin_border
            ws.cell(row=current_row, column=3, value="").border = thin_border
        ws.cell(row=current_row, column=2).alignment = center_align
        ws.cell(row=current_row, column=3).alignment = center_align
        ws.cell(row=current_row, column=4, value="").border = thin_border
        ws.cell(row=current_row, column=4).alignment = center_align
        current_row += 1

    current_row += 1

    # ==================== Section 3: Tools and Equipment ====================
    ws.merge_cells(f'A{current_row}:F{current_row}')
    ws[f'A{current_row}'] = "۳. ماشین‌آلات و تجهیزات"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1

    eq_headers = ["نوع تجهیزات", "مدل", "تعداد", "ساعت کار", "وضعیت", "دلیل غیرفعال"]
    col_widths = [20, 20, 10, 12, 16, 25]
    for col, (header, width) in enumerate(zip(eq_headers, col_widths), 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col)].width = width
    current_row += 1

    equipment_config = config.get("Tools_And_Equipments", {})
    equipment_costs = config.get("Equipment_Costs", {})
    # Build flat list of (type, model) tuples
    all_equipment = []
    for eq_type, models in equipment_config.items():
        if models:
            for model in models:
                all_equipment.append((eq_type, model))
        else:
            all_equipment.append((eq_type, ""))

    # Use planned_quantity from config to decide which equipment is active
    for idx, (eq_type, model) in enumerate(all_equipment):
        ws.cell(row=current_row, column=1, value=eq_type).border = thin_border
        ws.cell(row=current_row, column=1).alignment = right_align
        ws.cell(row=current_row, column=2, value=model).border = thin_border
        ws.cell(row=current_row, column=2).alignment = right_align

        # Get planned_quantity from config
        model_key = model if model else "default"
        eq_info = equipment_costs.get(eq_type, {}).get(model_key, {})
        planned_qty = eq_info.get("planned_quantity", 0)

        # Higher planned_quantity = higher chance of being active
        if planned_qty <= 0:
            is_active = random.random() < 0.15
        else:
            is_active = random.random() < 0.75

        if is_active:
            situation = weighted_choice(EQUIPMENT_SITUATIONS, EQUIPMENT_SITUATION_WEIGHTS)
            # Count based on planned_quantity (use a fraction of planned, minimum 1)
            if planned_qty > 0:
                count = random.randint(1, max(1, planned_qty))
            else:
                count = random.randint(1, 3)
            hours = random.choice([4, 6, 7, 8, 8, 8, 10, 12]) if situation == 'فعال' else 0
            reason = random.choice(INACTIVITY_REASONS) if situation != 'فعال' else ''

            ws.cell(row=current_row, column=3, value=count).border = thin_border
            ws.cell(row=current_row, column=4, value=hours).border = thin_border
            ws.cell(row=current_row, column=5, value=situation).border = thin_border
            ws.cell(row=current_row, column=6, value=reason).border = thin_border
        else:
            for col in range(3, 7):
                ws.cell(row=current_row, column=col, value="").border = thin_border

        for col in range(3, 7):
            ws.cell(row=current_row, column=col).alignment = center_align
        current_row += 1

    current_row += 1

    # ==================== Section 4: Construction Operations ====================
    ws.merge_cells(f'A{current_row}:E{current_row}')
    ws[f'A{current_row}'] = "۴. عملیات ساختمانی"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1

    op_headers = ["نوع عملیات", "ایستگاه شروع (00+000)", "ایستگاه پایان (00+000)", "واحد", "مقدار"]
    op_widths = [25, 20, 20, 18, 15]
    for col, (header, width) in enumerate(zip(op_headers, op_widths), 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col)].width = width
    current_row += 1

    activities = config.get("Daily_Activity_Report", {})
    activity_budget = config.get("Activity_Budget", {})
    activity_list = list(activities.items())

    # Use planned_amount to decide which activities are active
    # Activities with larger planned_amount are more likely to be active
    active_ops = set()
    for idx, (operation, unit) in enumerate(activity_list):
        budget = activity_budget.get(operation, {})
        planned = budget.get("planned_amount", 0)
        if planned > 0:
            # Bigger operations are more likely to be active on any day
            if random.random() < 0.35:
                active_ops.add(idx)
        else:
            if random.random() < 0.05:
                active_ops.add(idx)
    # Ensure at least 2 activities are active
    if len(active_ops) < 2 and len(activity_list) >= 2:
        remaining = [i for i in range(len(activity_list)) if i not in active_ops]
        for i in random.sample(remaining, min(2 - len(active_ops), len(remaining))):
            active_ops.add(i)

    for idx, (operation, unit) in enumerate(activity_list):
        ws.cell(row=current_row, column=1, value=operation).border = thin_border
        ws.cell(row=current_row, column=1).alignment = right_align

        if idx in active_ops:
            start_km = random.randint(0, 40)
            start_m = random.choice([0, 100, 200, 300, 400, 500, 600, 700, 800, 900])
            end_km = start_km + random.randint(0, 3)
            end_m = random.choice([0, 100, 200, 300, 400, 500, 600, 700, 800, 900])
            if end_km == start_km and end_m <= start_m:
                end_m = start_m + random.choice([100, 200, 300, 400, 500])
                if end_m >= 1000:
                    end_km += 1
                    end_m -= 1000

            start_station = f"{start_km:02d}+{start_m:03d}"
            end_station = f"{end_km:02d}+{end_m:03d}"

            # Generate daily amount as a fraction of planned_amount
            budget = activity_budget.get(operation, {})
            planned = budget.get("planned_amount", 0)
            if planned > 0:
                # Daily work ≈ planned_amount / 365 * random factor
                daily_base = planned / 365.0
                amount = round(daily_base * random.uniform(0.3, 2.5), 2)
                # Ensure at least 1 for small amounts
                amount = max(amount, 0.5)
            elif 'متر مکعب' in unit:
                amount = round(random.uniform(10, 500), 2)
            elif 'کیلوگرم' in unit:
                amount = round(random.uniform(100, 5000), 2)
            elif 'تن' in unit:
                amount = round(random.uniform(5, 200), 2)
            elif 'متر مربع' in unit:
                amount = round(random.uniform(20, 1000), 2)
            elif 'متر' in unit:
                amount = round(random.uniform(50, 2000), 2)
            elif 'تعداد' in unit:
                amount = random.randint(1, 20)
            else:
                amount = round(random.uniform(1, 100), 2)

            ws.cell(row=current_row, column=2, value=start_station).border = thin_border
            ws.cell(row=current_row, column=3, value=end_station).border = thin_border
            ws.cell(row=current_row, column=4, value=unit).border = thin_border
            ws.cell(row=current_row, column=5, value=amount).border = thin_border
        else:
            ws.cell(row=current_row, column=2, value="").border = thin_border
            ws.cell(row=current_row, column=3, value="").border = thin_border
            ws.cell(row=current_row, column=4, value=unit).border = thin_border
            ws.cell(row=current_row, column=5, value="").border = thin_border

        for col in range(2, 6):
            ws.cell(row=current_row, column=col).alignment = center_align
        current_row += 1

    current_row += 1

    # ==================== Section 5: Incoming Materials ====================
    ws.merge_cells(f'A{current_row}:F{current_row}')
    ws[f'A{current_row}'] = "۵. مواد و کالاهای ورودی"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1

    mat_headers = ["نوع مصالح", "واحد", "مقدار ورودی", "مقدار مصرفی", "محل نگهداری", "شماره بارنامه"]
    mat_widths = [20, 15, 13, 13, 18, 18]
    for col, (header, width) in enumerate(zip(mat_headers, mat_widths), 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col)].width = width
    current_row += 1

    materials_config = config.get("Incoming_Materials_And_Goods", {})
    material_prices = config.get("Material_Prices", {})
    material_list = list(materials_config.items())

    # Use planned_total from config to decide which materials arrive today
    active_mats = set()
    for idx, (material, unit) in enumerate(material_list):
        mat_info = material_prices.get(material, {})
        planned = mat_info.get("planned_total", 0)
        if planned > 0:
            # Materials with stock are more likely to arrive
            if random.random() < 0.25:
                active_mats.add(idx)
        else:
            if random.random() < 0.03:
                active_mats.add(idx)
    # Ensure at least 1-2 materials arrive
    if len(active_mats) < 1 and len(material_list) >= 1:
        remaining = [i for i in range(len(material_list)) if i not in active_mats]
        for i in random.sample(remaining, min(2, len(remaining))):
            active_mats.add(i)

    for idx, (material, unit) in enumerate(material_list):
        ws.cell(row=current_row, column=1, value=material).border = thin_border
        ws.cell(row=current_row, column=1).alignment = right_align
        ws.cell(row=current_row, column=2, value=unit).border = thin_border
        ws.cell(row=current_row, column=2).alignment = center_align

        if idx in active_mats:
            mat_info = material_prices.get(material, {})
            planned_total = mat_info.get("planned_total", 0)

            if planned_total > 0:
                # Daily incoming ≈ planned_total / ~200 work days * random factor
                daily_base = planned_total / 200.0
                incoming = round(daily_base * random.uniform(0.5, 3.0), 2)
                incoming = max(incoming, 1)
            elif 'تن' in unit:
                incoming = round(random.uniform(5, 100), 2)
            elif 'متر مکعب' in unit:
                incoming = round(random.uniform(5, 50), 2)
            elif 'کیلوگرم' in unit:
                incoming = round(random.uniform(100, 5000), 2)
            elif 'لیتر' in unit:
                incoming = round(random.uniform(50, 500), 2)
            elif 'تعداد' in unit:
                incoming = random.randint(50, 500)
            else:
                incoming = round(random.uniform(10, 200), 2)

            used = round(incoming * random.uniform(0.3, 0.9), 2)
            storage = random.choice(STORAGE_PLACES)
            waybill = f"{random.randint(100000, 999999)}"

            ws.cell(row=current_row, column=3, value=incoming).border = thin_border
            ws.cell(row=current_row, column=4, value=used).border = thin_border
            ws.cell(row=current_row, column=5, value=storage).border = thin_border
            ws.cell(row=current_row, column=6, value=waybill).border = thin_border
        else:
            for col in range(3, 7):
                ws.cell(row=current_row, column=col, value="").border = thin_border

        for col in range(3, 7):
            ws.cell(row=current_row, column=col).alignment = center_align
        current_row += 1

    current_row += 1

    # ==================== Section 6: Climate Condition ====================
    ws.merge_cells(f'A{current_row}:F{current_row}')
    ws[f'A{current_row}'] = "۶. شرایط آب و هوایی"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1

    climate_headers = ["حداقل دما", "حداکثر دما", "رطوبت (%)", "وضعیت آب و هوا", "سرعت باد", "تاثیر بر پروژه"]
    for col, header in enumerate(climate_headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    current_row += 1

    # Generate climate data based on month
    month = j_date.month
    if month in [1, 2, 3]:  # Spring
        min_temp = random.randint(8, 20)
        max_temp = min_temp + random.randint(8, 15)
        humidity = random.randint(20, 50)
    elif month in [4, 5, 6]:  # Summer
        min_temp = random.randint(18, 30)
        max_temp = min_temp + random.randint(10, 18)
        humidity = random.randint(10, 35)
    elif month in [7, 8, 9]:  # Autumn
        min_temp = random.randint(5, 18)
        max_temp = min_temp + random.randint(8, 15)
        humidity = random.randint(25, 55)
    else:  # Winter
        min_temp = random.randint(-5, 10)
        max_temp = min_temp + random.randint(5, 12)
        humidity = random.randint(30, 65)

    weather = weighted_choice(WEATHER_TYPES, WEATHER_WEIGHTS)
    wind = weighted_choice(WIND_SPEEDS, WIND_WEIGHTS)
    climate_effect = weighted_choice(CLIMATE_EFFECTS, CLIMATE_EFFECT_WEIGHTS)
    # If weather is bad, more likely to have effect
    if weather in ['بارانی', 'برفی']:
        climate_effect = weighted_choice(CLIMATE_EFFECTS, [30, 50, 20])

    ws.cell(row=current_row, column=1, value=min_temp).border = thin_border
    ws.cell(row=current_row, column=2, value=max_temp).border = thin_border
    ws.cell(row=current_row, column=3, value=humidity).border = thin_border
    ws.cell(row=current_row, column=4, value=weather).border = thin_border
    ws.cell(row=current_row, column=5, value=wind).border = thin_border
    ws.cell(row=current_row, column=6, value=climate_effect).border = thin_border
    for col in range(1, 7):
        ws.cell(row=current_row, column=col).alignment = center_align
    current_row += 2

    # ==================== Section 7: Project Issues ====================
    ws.merge_cells(f'A{current_row}:F{current_row}')
    ws[f'A{current_row}'] = "۷. مسائل و مشکلات پروژه"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1

    issue_headers = ["نوع مشکل", "تاثیر", "محل (۰۰+۰۰۰)", "ساعت شروع", "ساعت پایان", "توضیحات"]
    issue_widths = [22, 20, 15, 12, 12, 25]
    for col, (header, width) in enumerate(zip(issue_headers, issue_widths), 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col)].width = width
    current_row += 1

    issues_list = config.get("Project_Issues", [])
    # 40% chance of having issues on any given day
    has_issues = random.random() < 0.4
    if has_issues:
        num_issues = random.randint(1, min(3, len(issues_list)))
        active_issues = random.sample(issues_list, num_issues)
    else:
        active_issues = []

    for issue in issues_list:
        ws.cell(row=current_row, column=1, value=issue).border = thin_border
        ws.cell(row=current_row, column=1).alignment = right_align

        if issue in active_issues:
            effect = random.choice(ISSUE_EFFECTS)
            location = random_station(0, 30)
            start_h = random.randint(7, 14)
            end_h = start_h + random.randint(1, 4)
            start_time = f"{start_h:02d}:{random.choice([0, 15, 30, 45]):02d}"
            end_time = f"{min(end_h, 23):02d}:{random.choice([0, 15, 30, 45]):02d}"

            ws.cell(row=current_row, column=2, value=effect).border = thin_border
            ws.cell(row=current_row, column=3, value=location).border = thin_border
            ws.cell(row=current_row, column=4, value=start_time).border = thin_border
            ws.cell(row=current_row, column=5, value=end_time).border = thin_border
            ws.cell(row=current_row, column=6, value="").border = thin_border
        else:
            for col in range(2, 7):
                ws.cell(row=current_row, column=col, value="").border = thin_border

        for col in range(2, 7):
            ws.cell(row=current_row, column=col).alignment = center_align
        current_row += 1

    current_row += 1

    # ==================== Section 8: Safety ====================
    ws.merge_cells(f'A{current_row}:D{current_row}')
    ws[f'A{current_row}'] = "۸. ایمنی"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1

    safety_headers = ["وضعیت ایمنی", "بازرسی ایمنی", "حادثه رخ داده", "توضیحات حادثه"]
    for col, header in enumerate(safety_headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    current_row += 1

    safety_situation = weighted_choice(SAFETY_SITUATIONS, SAFETY_WEIGHTS)
    safety_inspection = 'بله' if random.random() < 0.7 else 'خیر'
    incident = 'بله' if safety_situation == 'حادثه' else 'خیر'
    incident_text = 'حادثه جزئی - بدون مصدومیت' if incident == 'بله' else ''

    ws.cell(row=current_row, column=1, value=safety_situation).border = thin_border
    ws.cell(row=current_row, column=2, value=safety_inspection).border = thin_border
    ws.cell(row=current_row, column=3, value=incident).border = thin_border
    ws.cell(row=current_row, column=4, value=incident_text).border = thin_border
    for col in range(1, 5):
        ws.cell(row=current_row, column=col).alignment = center_align
    current_row += 2

    # ==================== Section 9: Events ====================
    ws.merge_cells(f'A{current_row}:C{current_row}')
    ws[f'A{current_row}'] = "۹. رویدادها"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1

    event_headers = ["نوع رویداد", "نام رویداد", "توضیحات"]
    event_widths = [18, 30, 50]
    for col, (header, width) in enumerate(zip(event_headers, event_widths), 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col)].width = width
    current_row += 1

    # 30% chance of events
    if random.random() < 0.3:
        num_events = random.randint(1, 2)
        for _ in range(num_events):
            event_type = random.choice(EVENT_TYPES)
            event_name = random.choice(SAMPLE_EVENT_NAMES)
            ws.cell(row=current_row, column=1, value=event_type).border = thin_border
            ws.cell(row=current_row, column=2, value=event_name).border = thin_border
            ws.cell(row=current_row, column=3, value="").border = thin_border
            for col in range(1, 4):
                ws.cell(row=current_row, column=col).alignment = center_align
            current_row += 1

    return wb


def generate_forms(project_code, start_date_str, end_date_str, shift_type='both', output_dir='./generated_forms'):
    """
    Generate daily form Excel files for a date range.

    Args:
        project_code: Project code (e.g., "Project-01")
        start_date_str: Start date in Jalali format (YYYY/MM/DD)
        end_date_str: End date in Jalali format (YYYY/MM/DD)
        shift_type: 'morning', 'night', or 'both'
        output_dir: Directory to save generated files
    """
    # Load config
    config, project_info = load_project_configuration(project_code)
    project_name = project_info.get('name', project_code)

    # Parse dates
    start_date = parse_jalali_date(start_date_str)
    end_date = parse_jalali_date(end_date_str)

    if end_date < start_date:
        print("Error: End date must be after start date.")
        sys.exit(1)

    # Create output directory
    output_path = os.path.join(output_dir, project_code)
    os.makedirs(output_path, exist_ok=True)

    # Determine shifts
    shifts = []
    if shift_type in ['morning', 'both']:
        shifts.append('صبح')
    if shift_type in ['night', 'both']:
        shifts.append('شب')

    # Generate forms
    current_date = start_date
    total_files = 0

    while current_date <= end_date:
        # Skip Fridays (weekday 6 in jdatetime) - 80% chance
        if current_date.weekday() == 6 and random.random() < 0.8:
            current_date += timedelta(days=1)
            continue

        for shift in shifts:
            wb = generate_single_form(config, project_info, current_date, shift, project_name)

            # Generate filename
            date_str = current_date.strftime('%Y-%m-%d')
            shift_en = 'morning' if shift == 'صبح' else 'night'
            filename = f"{project_code}_{date_str}_{shift_en}.xlsx"
            filepath = os.path.join(output_path, filename)

            wb.save(filepath)
            total_files += 1
            print(f"  Generated: {filename}")

        current_date += timedelta(days=1)

    print(f"\n{'='*60}")
    print(f"  Total files generated: {total_files}")
    print(f"  Output directory: {os.path.abspath(output_path)}")
    print(f"{'='*60}")

    return total_files


def main():
    parser = argparse.ArgumentParser(
        description='Generate random daily form Excel files for testing.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_daily_forms.py --project Project-01 --start 1404/01/01 --end 1404/01/10 --shift both
  python generate_daily_forms.py --project Project-02 --start 1404/02/01 --end 1404/02/15 --shift morning
  python generate_daily_forms.py --project Project-01 --start 1404/01/01 --end 1404/01/05 --shift night --output ./test_data
        """
    )

    parser.add_argument('--project', required=True, help='Project code (e.g., Project-01)')
    parser.add_argument('--start', required=True, help='Start date in Jalali (e.g., 1404/01/01)')
    parser.add_argument('--end', required=True, help='End date in Jalali (e.g., 1404/01/15)')
    parser.add_argument('--shift', choices=['morning', 'night', 'both'], default='both',
                        help='Shift type (default: both)')
    parser.add_argument('--output', default='./generated_forms', help='Output directory (default: ./generated_forms)')

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Daily Form Excel Generator")
    print(f"{'='*60}")
    print(f"  Project:    {args.project}")
    print(f"  Date range: {args.start} → {args.end}")
    print(f"  Shift:      {args.shift}")
    print(f"  Output:     {args.output}")
    print(f"{'='*60}\n")

    generate_forms(args.project, args.start, args.end, args.shift, args.output)


if __name__ == '__main__':
    main()
