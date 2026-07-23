"""
Generate daily reports from extracted Excel data.

This script maps the extracted tables from Daily_for_month.xlsx to the 
Project-03_template_1.xlsx format and generates 30 individual Excel files.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from converter import read_excel_with_multiple_tables


def map_human_resources(table: pd.DataFrame, ws, start_row: int = 7):
    """
    Map Table 1 (نیروی انسانی) to template section 2.
    
    Template columns (0-indexed in openpyxl, 1-indexed):
    - Col A (1): سمت (position name) - already filled in template
    - Col B (2): تعداد (count)
    - Col C (3): ساعت کار (work hours)
    - Col D (4): توضیحات (notes)
    
    Source columns:
    - نیروی انسانی: position name
    - تعداد كل: total count
    - حاضر: present
    - مرخصی: leave
    """
    # Mapping of source position names to template row numbers (1-indexed)
    position_mapping = {
        'مدیر پروژه': 7,
        'سرپرست کارگاه': 8,
        'معاونت اجراء': 9,
        'مسئول ابنیه فنی': 10,
        'سرپرست دفتر فنی': 11,
        'کارشناس دفتر فنی': 12,
        'نقشه بردار': 13,
        'کمک نقشه بردار': 14,
        'مباشر عملیات خاکی': 15,
        'مسئول کنترل پروژه': 16,
        'اداری- مالی': 17,
        'کارپرداز': 18,
        'کارشناس ایمنی': 19,
        'سرپرست ماشین آلات': 20,
        'کارشناس نت ماشین آلات': 21,
        'راننده سنگین': 22,
        'راننده ویژه': 23,
        'راننده سبک': 24,
        'مکانیک': 25,
        'سرویس کار': 26,
        'انباردار': 27,
        'مسئول حراست': 28,
        'نگهبان': 29,
        'مسئول امور داخلی': 30,
        'تاسیسات': 31,
        'استاد کار بنایی': 32,
        'کارگر ساده': 34,  # Note: کارگر ساده maps to row 34
        'کارگر': 33,
        'خدمات': 35,
        'تکنسین آزمایشگاه': 36,
        'کارگر آزمایشگاه': 37,
        'نصاب ساندویچ پنل': 38,
        'اکیپ تاسیسات برق': 39,
    }
    
    # Get column names from the table
    cols = list(table.columns)
    position_col = cols[1] if len(cols) > 1 else None  # نیروی انسانی
    count_col = cols[2] if len(cols) > 2 else None  # تعداد كل
    present_col = cols[3] if len(cols) > 3 else None  # حاضر
    
    for _, row in table.iterrows():
        position = str(row[position_col]).strip() if position_col else None
        if position and position in position_mapping:
            template_row = position_mapping[position]
            
            # Write تعداد (count) - use حاضر (present) as the active count
            if present_col and pd.notna(row[present_col]):
                ws.cell(row=template_row, column=2, value=row[present_col])
            elif count_col and pd.notna(row[count_col]):
                ws.cell(row=template_row, column=2, value=row[count_col])


def map_equipment(table: pd.DataFrame, ws, start_row: int = 43):
    """
    Map Table 2 (ماشین آلات) to template section 3.
    
    Template columns:
    - Col A (1): نام تجهیزات - already filled
    - Col B (2): تعداد فعال
    - Col C (3): ساعت کار
    - Col D (4): وضعیت
    - Col E (5): دلیل غیرفعال
    
    Source columns:
    - نوع ماشین آلات و تجهيزات: equipment name
    - تعداد كل: total
    - فعال: active
    - آماده به کار: standby
    - تحت تعمیر: under repair
    """
    # Mapping of source equipment names to template row numbers
    equipment_mapping = {
        'بولدوزر کاترپیلار D6': 43,
        'لودر 5 تن تیراژه': 44,
        'لودر ۵ تن تیراژه': 44,
        'بیل مکانیکی360': 45,
        'بیل مکانیکی۳۶۰': 45,
        'بیل مکانیکی220': 46,
        'بیل مکانیکی۲۲۰': 46,
        'کمپرسی جفت': 47,
        'گریدرکوماتسو661A': 48,
        'گریدر کوماتسو661A': 48,
        'گریدر کوماتسو GdA-705': 49,
        'گریدر کاترپیلار 140G': 50,
        'غلطک HC100B': 51,
        'غلطک HC100C': 52,
        'غلطک کششی': 53,
        'تانکر آبپاش': 54,
        'تراکتور': 55,
        'ژنراتور KVA 40': 56,
        'ژنراتور KVA 150': 57,
        'سواری': 58,
        'وانت': 59,
        'موتور جوش': 60,
        'کمپرسور باد': 61,
        'کانکس': 62,
        'کانتینر': 63,
        'مخزن': 64,
        'بتونیر دیزلی': 65,
        'سیلوی 100 تنی': 66,
        'سیلوی ۱۰۰ تنی': 66,
    }
    
    cols = list(table.columns)
    equip_col = cols[1] if len(cols) > 1 else None
    active_col = cols[3] if len(cols) > 3 else None  # فعال
    standby_col = cols[4] if len(cols) > 4 else None  # آماده به کار
    repair_col = cols[5] if len(cols) > 5 else None  # تحت تعمیر
    
    for _, row in table.iterrows():
        equipment = str(row[equip_col]).strip() if equip_col else None
        if equipment and equipment in equipment_mapping:
            template_row = equipment_mapping[equipment]
            
            # Write تعداد فعال
            if active_col and pd.notna(row[active_col]):
                ws.cell(row=template_row, column=2, value=row[active_col])
            
            # Write وضعیت based on standby/repair status
            status_parts = []
            if standby_col and pd.notna(row[standby_col]) and row[standby_col]:
                status_parts.append(f"آماده به کار: {row[standby_col]}")
            if repair_col and pd.notna(row[repair_col]) and row[repair_col]:
                status_parts.append(f"تحت تعمیر: {row[repair_col]}")
            
            if status_parts:
                ws.cell(row=template_row, column=4, value=", ".join(status_parts))


def map_materials(table: pd.DataFrame, ws, start_row: int = 80):
    """
    Map Table 3 (مواد و مصالح) to template section 5.
    
    Template columns:
    - Col A (1): نوع مصالح - already filled
    - Col B (2): مقدار ورودی (today's input)
    - Col C (3): مجموع ورودی (total input)
    - Col D (4): مقدار مصرفی
    - Col E (5): مجموع مصرفی
    - Col F (6): محل نگهداری
    - Col G (7): شماره بارنامه
    
    Source columns:
    - نوع مصالح
    - وارده امروز (today's input)
    - وارده تاکنون (total input)
    """
    # Mapping of source material names to template row numbers
    material_mapping = {
        'سیمان/Ton': 80,
        'شن وماسه و بادامی/ Ton': 81,
        'شن و ماسه و بادامی/Ton': 81,
        'گازوئیل/ liter': 82,
        'گازوئیل/liter': 82,
        'بلوک سیمانی/ no': 83,
        'بلوک سیمانی/no': 83,
        'آب  تجهیز/ متر مکعب': 84,
        'آب تجهیز/متر مکعب': 84,
        'آب عملیات خاکی / متر مکعب': 85,
        'آب عملیات خاکی/متر مکعب': 85,
        'پروفیل سقف(کیلو گرم)': 86,
        'پروفیل سقف (کیلوگرم)': 86,
        'میلگرد سایز 16(کیلوگرم)': 87,
        'میلگرد سایز 16 (کیلوگرم)': 87,
        'میلگرد سایز 12(کیلوگرم)': 88,
        'میلگرد سایز 12 (کیلوگرم)': 88,
    }
    
    cols = list(table.columns)
    material_col = cols[1] if len(cols) > 1 else None
    today_col = cols[2] if len(cols) > 2 else None  # وارده امروز
    total_col = cols[4] if len(cols) > 4 else None  # وارده تاکنون
    
    for _, row in table.iterrows():
        material = str(row[material_col]).strip() if material_col else None
        if material and material in material_mapping:
            template_row = material_mapping[material]
            
            # Write مقدار ورودی (today's input)
            if today_col and pd.notna(row[today_col]):
                ws.cell(row=template_row, column=2, value=row[today_col])
            
            # Write مجموع ورودی (total input)
            if total_col and pd.notna(row[total_col]):
                ws.cell(row=template_row, column=3, value=row[total_col])


def map_activities(table: pd.DataFrame, ws, start_row: int = 70):
    """
    Map Table 4 (شرح فعالیت) to template section 4.
    
    This is more free-form, we'll write activities as rows.
    """
    cols = list(table.columns)
    activity_col = cols[1] if len(cols) > 1 else None
    
    row_num = start_row
    for _, row in table.iterrows():
        if activity_col and pd.notna(row[activity_col]):
            activity = str(row[activity_col]).strip()
            if activity and activity != 'nan':
                ws.cell(row=row_num, column=1, value=activity)
                row_num += 1
                if row_num > 77:  # Don't overflow section
                    break


def set_date_info(ws, sheet_name: str):
    """
    Set date information in the template.
    Sheet name format: 1404-08-01 or 1404-08.01
    """
    # Parse date from sheet name
    date_str = sheet_name.replace('.', '-')
    
    # Set date in row 2
    ws.cell(row=2, column=1, value=date_str)


def generate_daily_reports(
    source_file: str = "Daily_for_month.xlsx",
    template_file: str = "Project-03_template_1.xlsx",
    output_dir: str = "output"
):
    """
    Generate daily reports from extracted data.
    
    Args:
        source_file: Path to the source Excel file with daily data
        template_file: Path to the template Excel file
        output_dir: Directory to save output files
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Read source data
    print("Reading source data...")
    data = read_excel_with_multiple_tables(source_file)
    
    print(f"Found {len(data)} sheets")
    
    for sheet_name, tables in data.items():
        print(f"\nProcessing sheet: {sheet_name}")
        
        if len(tables) < 4:
            print(f"  Warning: Only {len(tables)} tables found, need at least 4")
            continue
        
        # Load template workbook
        wb = load_workbook(template_file)
        ws = wb.active
        
        # Set date info
        set_date_info(ws, sheet_name)
        
        # Map each table
        print("  Mapping human resources (Table 1)...")
        map_human_resources(tables[0], ws)
        
        print("  Mapping equipment (Table 2)...")
        map_equipment(tables[1], ws)
        
        print("  Mapping materials (Table 3)...")
        map_materials(tables[2], ws)
        
        print("  Mapping activities (Table 4)...")
        map_activities(tables[3], ws)
        
        # Save output file
        date_str = sheet_name.replace('.', '-').replace('/', '-')
        output_file = output_path / f"Project-03--{date_str}.xlsx"
        wb.save(output_file)
        print(f"  Saved: {output_file}")
    
    print(f"\nDone! Generated {len(data)} files in '{output_dir}' directory.")


if __name__ == "__main__":
    generate_daily_reports()
