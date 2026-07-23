"""
Excel template generator and parser for daily forms.
"""
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO
from forms.daily_form_configuration import configuration


def create_daily_form_template():
    """Create an Excel template for daily form data entry."""
    wb = openpyxl.Workbook()
    
    # Styles
    header_font = Font(bold=True, size=12, color="FFFFFF")
    header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
    section_font = Font(bold=True, size=14, color="FFFFFF")
    section_fill = PatternFill(start_color="059669", end_color="059669", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
    right_align = Alignment(horizontal='right', vertical='center', wrap_text=True)
    
    # Remove default sheet
    ws = wb.active
    ws.title = "فرم روزانه"
    ws.sheet_view.rightToLeft = True  # RTL for Persian
    
    current_row = 1
    
    # ==================== Section 1: Date and Time ====================
    ws.merge_cells(f'A{current_row}:D{current_row}')
    ws[f'A{current_row}'] = "۱. تاریخ و زمان"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1
    
    # Date and Time headers
    headers = ["تاریخ (1404/01/01)", "روز هفته", "شیفت کاری", "پروژه"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col)].width = 20
    current_row += 1
    
    # Empty row for data
    for col in range(1, 5):
        cell = ws.cell(row=current_row, column=col, value="")
        cell.border = thin_border
        cell.alignment = center_align
    current_row += 2
    
    # ==================== Section 2: Human Resources ====================
    ws.merge_cells(f'A{current_row}:D{current_row}')
    ws[f'A{current_row}'] = "۲. نیروی انسانی"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1
    
    # HR headers
    hr_headers = ["سمت", "تعداد", "ساعت کار", "توضیحات"]
    for col, header in enumerate(hr_headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    current_row += 1
    
    # Pre-filled positions from config
    for position in configuration["Human_Resources"]:
        cell = ws.cell(row=current_row, column=1, value=position)
        cell.border = thin_border
        cell.alignment = right_align
        for col in range(2, 5):
            cell = ws.cell(row=current_row, column=col, value="")
            cell.border = thin_border
            cell.alignment = center_align
        current_row += 1
    
    current_row += 1
    
    # ==================== Section 3: Tools and Equipment ====================
    ws.merge_cells(f'A{current_row}:E{current_row}')
    ws[f'A{current_row}'] = "۳. ماشین‌آلات و تجهیزات"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1
    
    # Equipment headers
    eq_headers = ["نام تجهیزات", "تعداد فعال", "ساعت کار", "وضعیت", "دلیل غیرفعال"]
    for col, header in enumerate(eq_headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    current_row += 1
    
    # Pre-filled equipment from config
    for equipment in configuration["Tools_And_Equipments"]:
        cell = ws.cell(row=current_row, column=1, value=equipment)
        cell.border = thin_border
        cell.alignment = right_align
        for col in range(2, 6):
            cell = ws.cell(row=current_row, column=col, value="")
            cell.border = thin_border
            cell.alignment = center_align
        current_row += 1
    
    current_row += 1
    
    # ==================== Section 4: Construction Operations ====================
    ws.merge_cells(f'A{current_row}:F{current_row}')
    ws[f'A{current_row}'] = "۴. عملیات ساختمانی"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1
    
    # Operations headers
    op_headers = ["نوع عملیات", "کیلومتر شروع", "کیلومتر پایان", "واحد", "پیشرفت", "شماره نقشه"]
    for col, header in enumerate(op_headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    current_row += 1
    
    # Pre-filled operations from config
    for operation in configuration["Daily_Activity_Report"]:
        cell = ws.cell(row=current_row, column=1, value=operation)
        cell.border = thin_border
        cell.alignment = right_align
        for col in range(2, 7):
            cell = ws.cell(row=current_row, column=col, value="")
            cell.border = thin_border
            cell.alignment = center_align
        current_row += 1
    
    # Add extra empty rows for additional operations
    for _ in range(3):
        for col in range(1, 7):
            cell = ws.cell(row=current_row, column=col, value="")
            cell.border = thin_border
            cell.alignment = center_align
        current_row += 1
    
    current_row += 1
    
    # ==================== Section 5: Incoming Materials ====================
    ws.merge_cells(f'A{current_row}:G{current_row}')
    ws[f'A{current_row}'] = "۵. مواد و کالاهای ورودی"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1
    
    # Materials headers
    mat_headers = ["نوع مصالح", "مقدار ورودی", "مجموع ورودی", "مقدار مصرفی", "مجموع مصرفی", "محل نگهداری", "شماره بارنامه"]
    for col, header in enumerate(mat_headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    current_row += 1
    
    # Pre-filled materials from config
    for material in configuration["Incoming_Materials_And_Goods"]:
        cell = ws.cell(row=current_row, column=1, value=material)
        cell.border = thin_border
        cell.alignment = right_align
        for col in range(2, 8):
            cell = ws.cell(row=current_row, column=col, value="")
            cell.border = thin_border
            cell.alignment = center_align
        current_row += 1
    
    # Add extra empty rows
    for _ in range(3):
        for col in range(1, 8):
            cell = ws.cell(row=current_row, column=col, value="")
            cell.border = thin_border
            cell.alignment = center_align
        current_row += 1
    
    current_row += 1
    
    # ==================== Section 6: Climate Condition ====================
    ws.merge_cells(f'A{current_row}:F{current_row}')
    ws[f'A{current_row}'] = "۶. شرایط آب و هوایی"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1
    
    # Climate headers
    climate_headers = ["حداقل دما", "حداکثر دما", "رطوبت (%)", "وضعیت آب و هوا", "سرعت باد", "تاثیر بر پروژه"]
    for col, header in enumerate(climate_headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    current_row += 1
    
    # Empty row with hints
    hints = ["", "", "", "صاف/ابری/بارانی/مه‌آلود/برفی", "آرام/معمولی/تند", "بدون تاثیر/کندی پیشرفت/توقف کامل"]
    for col, hint in enumerate(hints, 1):
        cell = ws.cell(row=current_row, column=col, value=hint)
        cell.border = thin_border
        cell.alignment = center_align
        cell.font = Font(italic=True, size=9, color="888888")
    current_row += 1
    
    # Data row
    for col in range(1, 7):
        cell = ws.cell(row=current_row, column=col, value="")
        cell.border = thin_border
        cell.alignment = center_align
    current_row += 2
    
    # ==================== Section 7: Project Issues ====================
    ws.merge_cells(f'A{current_row}:D{current_row}')
    ws[f'A{current_row}'] = "۷. مسائل و مشکلات پروژه"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1
    
    # Issues headers
    issue_headers = ["نوع مشکل", "تاثیر", "محل (کیلومتر)", "توضیحات"]
    for col, header in enumerate(issue_headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    current_row += 1
    
    # Pre-filled issues from config
    for issue in configuration["Project_Issues"]:
        cell = ws.cell(row=current_row, column=1, value=issue)
        cell.border = thin_border
        cell.alignment = right_align
        for col in range(2, 5):
            cell = ws.cell(row=current_row, column=col, value="")
            cell.border = thin_border
            cell.alignment = center_align
        current_row += 1
    
    current_row += 1
    
    # ==================== Section 8: Safety ====================
    ws.merge_cells(f'A{current_row}:D{current_row}')
    ws[f'A{current_row}'] = "۸. ایمنی"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1
    
    # Safety headers
    safety_headers = ["وضعیت ایمنی", "بازرسی ایمنی", "حادثه رخ داده", "توضیحات حادثه"]
    for col, header in enumerate(safety_headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    current_row += 1
    
    # Hints row
    safety_hints = ["خوب/متوسط/ضعیف", "بله/خیر", "بله/خیر", ""]
    for col, hint in enumerate(safety_hints, 1):
        cell = ws.cell(row=current_row, column=col, value=hint)
        cell.border = thin_border
        cell.alignment = center_align
        cell.font = Font(italic=True, size=9, color="888888")
    current_row += 1
    
    # Data row
    for col in range(1, 5):
        cell = ws.cell(row=current_row, column=col, value="")
        cell.border = thin_border
        cell.alignment = center_align
    current_row += 2
    
    # ==================== Section 9: Events ====================
    ws.merge_cells(f'A{current_row}:B{current_row}')
    ws[f'A{current_row}'] = "۹. رویدادها"
    ws[f'A{current_row}'].font = section_font
    ws[f'A{current_row}'].fill = section_fill
    ws[f'A{current_row}'].alignment = center_align
    current_row += 1
    
    # Events headers
    event_headers = ["نام رویداد", "توضیحات"]
    for col, header in enumerate(event_headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    ws.column_dimensions['B'].width = 50
    current_row += 1
    
    # Add empty rows for events
    for _ in range(5):
        for col in range(1, 3):
            cell = ws.cell(row=current_row, column=col, value="")
            cell.border = thin_border
            cell.alignment = center_align
        current_row += 1
    
    # Set print area and other settings
    ws.print_title_rows = '1:1'
    
    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return output


def parse_daily_form_excel(file):
    """
    Parse an uploaded Excel file and extract daily form data.
    Returns a dictionary with all form data.
    """
    wb = openpyxl.load_workbook(file, data_only=True)
    ws = wb.active
    
    data = {
        'date_time': {},
        'human_resources': [],
        'tools_equipment': [],
        'operations': [],
        'materials': [],
        'climate': {},
        'issues': [],
        'safety': {},
        'events': []
    }
    
    current_row = 1
    
    # Helper to get cell value
    def get_value(row, col):
        val = ws.cell(row=row, column=col).value
        return str(val).strip() if val is not None else ""
    
    # Helper to convert Persian yes/no to boolean
    def to_bool(val):
        if not val:
            return False
        val = str(val).strip().lower()
        return val in ['بله', 'yes', 'true', '1', 'انجام شد']
    
    # Find sections by looking for section headers
    section_rows = {}
    for row in range(1, ws.max_row + 1):
        cell_val = get_value(row, 1)
        if '۱. تاریخ و زمان' in cell_val:
            section_rows['date_time'] = row
        elif '۲. نیروی انسانی' in cell_val:
            section_rows['human_resources'] = row
        elif '۳. ماشین‌آلات و تجهیزات' in cell_val:
            section_rows['tools_equipment'] = row
        elif '۴. عملیات ساختمانی' in cell_val:
            section_rows['operations'] = row
        elif '۵. مواد و کالاهای ورودی' in cell_val:
            section_rows['materials'] = row
        elif '۶. شرایط آب و هوایی' in cell_val:
            section_rows['climate'] = row
        elif '۷. مسائل و مشکلات پروژه' in cell_val:
            section_rows['issues'] = row
        elif '۸. ایمنی' in cell_val:
            section_rows['safety'] = row
        elif '۹. رویدادها' in cell_val:
            section_rows['events'] = row
    
    # Parse Date and Time (row after header + 1 for data)
    if 'date_time' in section_rows:
        data_row = section_rows['date_time'] + 2  # Skip header row
        data['date_time'] = {
            'form_date': get_value(data_row, 1),
            'day_of_week': get_value(data_row, 2),
            'work_shift': get_value(data_row, 3),
            'project_name': get_value(data_row, 4)
        }
    
    # Parse Human Resources
    if 'human_resources' in section_rows:
        start_row = section_rows['human_resources'] + 2  # Skip section header and column headers
        end_row = section_rows.get('tools_equipment', ws.max_row) - 2
        
        for row in range(start_row, end_row + 1):
            post = get_value(row, 1)
            if post:
                count = get_value(row, 2)
                hours = get_value(row, 3)
                notes = get_value(row, 4)
                
                if count or hours:  # Only add if there's data
                    data['human_resources'].append({
                        'post': post,
                        'count': count,
                        'working_hours': hours,
                        'notes': notes
                    })
    
    # Parse Tools and Equipment
    if 'tools_equipment' in section_rows:
        start_row = section_rows['tools_equipment'] + 2
        end_row = section_rows.get('operations', ws.max_row) - 2
        
        for row in range(start_row, end_row + 1):
            name = get_value(row, 1)
            if name:
                active = get_value(row, 2)
                hours = get_value(row, 3)
                situation = get_value(row, 4)
                reason = get_value(row, 5)
                
                if active or hours:
                    data['tools_equipment'].append({
                        'equipment_name': name,
                        'count_active': active,
                        'working_hours': hours,
                        'situation': situation,
                        'inactivity_reason': reason
                    })
    
    # Parse Construction Operations
    if 'operations' in section_rows:
        start_row = section_rows['operations'] + 2
        end_row = section_rows.get('materials', ws.max_row) - 2
        
        for row in range(start_row, end_row + 1):
            op_type = get_value(row, 1)
            if op_type:
                start_km = get_value(row, 2)
                end_km = get_value(row, 3)
                unit = get_value(row, 4)
                progress = get_value(row, 5)
                map_num = get_value(row, 6)
                
                if start_km or end_km or progress:
                    data['operations'].append({
                        'operation_type': op_type,
                        'start_km': start_km,
                        'end_km': end_km,
                        'unit': unit,
                        'progress': progress,
                        'map_number': map_num
                    })
    
    # Parse Incoming Materials
    if 'materials' in section_rows:
        start_row = section_rows['materials'] + 2
        end_row = section_rows.get('climate', ws.max_row) - 2
        
        for row in range(start_row, end_row + 1):
            mat_type = get_value(row, 1)
            if mat_type:
                incoming = get_value(row, 2)
                cum_in = get_value(row, 3)
                used = get_value(row, 4)
                cum_used = get_value(row, 5)
                storage = get_value(row, 6)
                waybill = get_value(row, 7)
                
                if incoming or cum_in or used:
                    data['materials'].append({
                        'material_type': mat_type,
                        'incoming_amount': incoming,
                        'cumulative_incoming': cum_in,
                        'used_amount': used,
                        'cumulative_used': cum_used,
                        'storage_place': storage,
                        'waybill_number': waybill
                    })
    
    # Parse Climate Condition
    if 'climate' in section_rows:
        data_row = section_rows['climate'] + 3  # Skip header and hints row
        
        weather_val = get_value(data_row, 4).lower()
        weather_type = ''
        if 'صاف' in weather_val or 'clear' in weather_val:
            weather_type = 'clear'
        elif 'ابری' in weather_val or 'cloudy' in weather_val:
            weather_type = 'cloudy'
        elif 'بارانی' in weather_val or 'rain' in weather_val:
            weather_type = 'rainy'
        elif 'مه' in weather_val or 'fog' in weather_val:
            weather_type = 'foggy'
        elif 'برفی' in weather_val or 'snow' in weather_val:
            weather_type = 'snowy'
        
        wind_val = get_value(data_row, 5).lower()
        wind_speed = ''
        if 'آرام' in wind_val or 'slow' in wind_val:
            wind_speed = 'slow'
        elif 'تند' in wind_val or 'fast' in wind_val:
            wind_speed = 'fast'
        elif 'معمولی' in wind_val or 'normal' in wind_val:
            wind_speed = 'normal'
        
        effect_val = get_value(data_row, 6).lower()
        climate_effect = ''
        if 'بدون' in effect_val or 'no' in effect_val:
            climate_effect = 'no_effect'
        elif 'کندی' in effect_val or 'slow' in effect_val:
            climate_effect = 'slow_progress'
        elif 'توقف' in effect_val or 'stop' in effect_val:
            climate_effect = 'stopped'
        
        data['climate'] = {
            'min_temperature': get_value(data_row, 1),
            'max_temperature': get_value(data_row, 2),
            'humidity': get_value(data_row, 3),
            'weather_type': weather_type,
            'wind_speed': wind_speed,
            'climate_effect': climate_effect
        }
    
    # Parse Project Issues
    if 'issues' in section_rows:
        start_row = section_rows['issues'] + 2
        end_row = section_rows.get('safety', ws.max_row) - 2
        
        for row in range(start_row, end_row + 1):
            issue_type = get_value(row, 1)
            if issue_type:
                effect = get_value(row, 2)
                location = get_value(row, 3)
                notes = get_value(row, 4)
                
                if effect or notes:
                    data['issues'].append({
                        'issue_type': issue_type,
                        'effect': effect,
                        'location_km': location,
                        'notes': notes
                    })
    
    # Parse Safety
    if 'safety' in section_rows:
        data_row = section_rows['safety'] + 3  # Skip header and hints row
        
        situation_val = get_value(data_row, 1).lower()
        safety_situation = ''
        if 'خوب' in situation_val or 'good' in situation_val:
            safety_situation = 'good'
        elif 'متوسط' in situation_val or 'fair' in situation_val:
            safety_situation = 'fair'
        elif 'ضعیف' in situation_val or 'poor' in situation_val:
            safety_situation = 'poor'
        
        data['safety'] = {
            'safety_situation': safety_situation,
            'safety_inspection': to_bool(get_value(data_row, 2)),
            'incident_occurred': to_bool(get_value(data_row, 3)),
            'incident_explanation': get_value(data_row, 4)
        }
    
    # Parse Events
    if 'events' in section_rows:
        start_row = section_rows['events'] + 2
        
        for row in range(start_row, min(start_row + 10, ws.max_row + 1)):
            event_name = get_value(row, 1)
            if event_name:
                explanation = get_value(row, 2)
                data['events'].append({
                    'event_name': event_name,
                    'explanation': explanation
                })
    
    return data
