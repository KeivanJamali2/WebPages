"""
Excel template generator and parser for daily forms.
"""
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from io import BytesIO
from forms.daily_form_configuration import configuration as default_configuration


def create_daily_form_template(config=None, project_name=None):
    """Create an Excel template for daily form data entry.
    
    Args:
        config: Optional project-specific configuration dict. If None, uses default.
        project_name: Optional project name to pre-fill in the template.
    """
    # Use provided config or fall back to default
    if config is None:
        config = default_configuration
    
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
    
    # Pre-fill project name if provided
    if project_name:
        ws.cell(row=current_row, column=4, value=project_name)
    
    # Add dropdown for shift (column 3)
    shift_validation = DataValidation(
        type="list",
        formula1='"صبح,شب"',
        allow_blank=True
    )
    shift_validation.error = "لطفاً یکی از گزینه‌ها را انتخاب کنید"
    shift_validation.errorTitle = "شیفت نامعتبر"
    shift_validation.prompt = "شیفت کاری را انتخاب کنید"
    shift_validation.promptTitle = "شیفت کاری"
    ws.add_data_validation(shift_validation)
    shift_validation.add(ws.cell(row=current_row, column=3))
    
    # Add dropdown for day of week (column 2)
    weekday_validation = DataValidation(
        type="list",
        formula1='"شنبه,یکشنبه,دوشنبه,سه‌شنبه,چهارشنبه,پنج‌شنبه,جمعه"',
        allow_blank=True
    )
    weekday_validation.error = "لطفاً یکی از روزهای هفته را انتخاب کنید"
    weekday_validation.errorTitle = "روز نامعتبر"
    ws.add_data_validation(weekday_validation)
    weekday_validation.add(ws.cell(row=current_row, column=2))
    
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
    for position in config["Human_Resources"]:
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
    eq_headers = ["نام تجهیزات", "تعداد", "ساعت کار", "وضعیت", "دلیل غیرفعال"]
    for col, header in enumerate(eq_headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    current_row += 1
    
    # Pre-filled equipment from config
    eq_start_row = current_row
    for equipment in config["Tools_And_Equipments"]:
        cell = ws.cell(row=current_row, column=1, value=equipment)
        cell.border = thin_border
        cell.alignment = right_align
        for col in range(2, 6):
            cell = ws.cell(row=current_row, column=col, value="")
            cell.border = thin_border
            cell.alignment = center_align
        current_row += 1
    eq_end_row = current_row - 1
    
    # Add dropdown for equipment situation (column 4)
    if eq_start_row <= eq_end_row:
        eq_situation_validation = DataValidation(
            type="list",
            formula1='"فعال,غیرفعال,در حال تعمیر"',
            allow_blank=True
        )
        eq_situation_validation.error = "لطفاً یکی از گزینه‌ها را انتخاب کنید"
        eq_situation_validation.errorTitle = "وضعیت نامعتبر"
        ws.add_data_validation(eq_situation_validation)
        for row in range(eq_start_row, eq_end_row + 1):
            eq_situation_validation.add(ws.cell(row=row, column=4))
    
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
    op_start_row = current_row
    for operation in config["Daily_Activity_Report"]:
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
    op_end_row = current_row - 1
    
    # Add dropdown for units (column 4)
    if op_start_row <= op_end_row:
        units_list = ",".join(config["Units"])
        units_validation = DataValidation(
            type="list",
            formula1=f'"{units_list}"',
            allow_blank=True
        )
        units_validation.error = "لطفاً یکی از واحدها را انتخاب کنید"
        units_validation.errorTitle = "واحد نامعتبر"
        ws.add_data_validation(units_validation)
        for row in range(op_start_row, op_end_row + 1):
            units_validation.add(ws.cell(row=row, column=4))
    
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
    for material in config["Incoming_Materials_And_Goods"]:
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
    
    # Data row (removed hints row to avoid confusion)
    climate_data_row = current_row
    for col in range(1, 7):
        cell = ws.cell(row=current_row, column=col, value="")
        cell.border = thin_border
        cell.alignment = center_align
    
    # Add dropdown for weather type (column 4)
    weather_validation = DataValidation(
        type="list",
        formula1='"صاف,ابری,بارانی,مه‌آلود,برفی"',
        allow_blank=True
    )
    weather_validation.error = "لطفاً یکی از گزینه‌ها را انتخاب کنید"
    weather_validation.errorTitle = "وضعیت نامعتبر"
    ws.add_data_validation(weather_validation)
    weather_validation.add(ws.cell(row=climate_data_row, column=4))
    
    # Add dropdown for wind speed (column 5)
    wind_validation = DataValidation(
        type="list",
        formula1='"آرام,معمولی,تند"',
        allow_blank=True
    )
    wind_validation.error = "لطفاً یکی از گزینه‌ها را انتخاب کنید"
    wind_validation.errorTitle = "سرعت نامعتبر"
    ws.add_data_validation(wind_validation)
    wind_validation.add(ws.cell(row=climate_data_row, column=5))
    
    # Add dropdown for climate effect (column 6)
    effect_validation = DataValidation(
        type="list",
        formula1='"بدون تاثیر,کندی پیشرفت,توقف کار"',
        allow_blank=True
    )
    effect_validation.error = "لطفاً یکی از گزینه‌ها را انتخاب کنید"
    effect_validation.errorTitle = "تاثیر نامعتبر"
    ws.add_data_validation(effect_validation)
    effect_validation.add(ws.cell(row=climate_data_row, column=6))
    
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
    for issue in config["Project_Issues"]:
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
    
    # Data row (removed hints row to avoid confusion)
    safety_data_row = current_row
    for col in range(1, 5):
        cell = ws.cell(row=current_row, column=col, value="")
        cell.border = thin_border
        cell.alignment = center_align
    
    # Add dropdown for safety situation (column 1)
    safety_situation_validation = DataValidation(
        type="list",
        formula1='"خوب,متوسط,ضعیف"',
        allow_blank=True
    )
    safety_situation_validation.error = "لطفاً یکی از گزینه‌ها را انتخاب کنید"
    safety_situation_validation.errorTitle = "وضعیت نامعتبر"
    ws.add_data_validation(safety_situation_validation)
    safety_situation_validation.add(ws.cell(row=safety_data_row, column=1))
    
    # Add dropdown for safety inspection (column 2)
    yes_no_validation1 = DataValidation(
        type="list",
        formula1='"بله,خیر"',
        allow_blank=True
    )
    yes_no_validation1.error = "لطفاً بله یا خیر را انتخاب کنید"
    yes_no_validation1.errorTitle = "گزینه نامعتبر"
    ws.add_data_validation(yes_no_validation1)
    yes_no_validation1.add(ws.cell(row=safety_data_row, column=2))
    
    # Add dropdown for incident occurred (column 3)
    yes_no_validation2 = DataValidation(
        type="list",
        formula1='"بله,خیر"',
        allow_blank=True
    )
    yes_no_validation2.error = "لطفاً بله یا خیر را انتخاب کنید"
    yes_no_validation2.errorTitle = "گزینه نامعتبر"
    ws.add_data_validation(yes_no_validation2)
    yes_no_validation2.add(ws.cell(row=safety_data_row, column=3))
    
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
        
        # Convert Persian shift to English for database
        shift_val = get_value(data_row, 3).lower()
        work_shift = ''
        if 'صبح' in shift_val or 'morning' in shift_val:
            work_shift = 'Morning'
        elif 'شب' in shift_val or 'night' in shift_val:
            work_shift = 'Night'
        
        data['date_time'] = {
            'form_date': get_value(data_row, 1),
            'day_of_week': get_value(data_row, 2),
            'work_shift': work_shift,
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
                situation_val = get_value(row, 4).lower()
                reason = get_value(row, 5)
                
                # Convert Persian situation to English for database
                situation = ''
                if 'فعال' in situation_val and 'غیر' not in situation_val:
                    situation = 'Active'
                elif 'غیرفعال' in situation_val or 'غیر فعال' in situation_val:
                    situation = 'Inactive'
                elif 'تعمیر' in situation_val or 'repair' in situation_val:
                    situation = 'Under Repair'
                elif 'active' in situation_val and 'in' not in situation_val:
                    situation = 'Active'
                elif 'inactive' in situation_val:
                    situation = 'Inactive'
                
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
        # Try to find the data row - check rows after header for actual data
        # Structure: section header (+0), column headers (+1), hints row (+2), data row (+3)
        # But user might enter data in hints row, so check both +2 and +3
        base_row = section_rows['climate']
        data_row = None
        
        # Check rows +2, +3, +4 for any data (temperature, weather, etc.)
        for offset in [2, 3, 4]:
            test_row = base_row + offset
            if test_row > ws.max_row:
                break
            # Check if this row has any climate data (temperature or weather selection)
            temp_val = get_value(test_row, 1)
            weather_val = get_value(test_row, 4)
            if temp_val or weather_val:
                data_row = test_row
                break
        
        # If no data found, default to +3
        if data_row is None:
            data_row = base_row + 3
        
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
        # Try to find the data row - check rows after header for actual data
        # Structure: section header (+0), column headers (+1), hints row (+2), data row (+3)
        # But user might enter data in hints row, so check both +2 and +3
        base_row = section_rows['safety']
        data_row = None
        
        # Check rows +2, +3, +4 for any data (safety situation, inspection, etc.)
        for offset in [2, 3, 4]:
            test_row = base_row + offset
            if test_row > ws.max_row:
                break
            # Check if this row has any safety data
            situation_val = get_value(test_row, 1)
            inspection_val = get_value(test_row, 2)
            if situation_val or inspection_val:
                data_row = test_row
                break
        
        # If no data found, default to +3
        if data_row is None:
            data_row = base_row + 3
        
        situation_val = get_value(data_row, 1).lower()
        safety_situation = ''
        if 'حادثه' in situation_val and 'شبه' not in situation_val and 'بدون' not in situation_val:
            safety_situation = 'Incident'
        elif 'شبه' in situation_val or 'near' in situation_val:
            safety_situation = 'NearMiss'
        elif 'بدون' in situation_val or 'no incident' in situation_val or 'no_incident' in situation_val:
            safety_situation = 'NoIncident'
        elif 'incident' in situation_val and 'near' not in situation_val and 'no' not in situation_val:
            safety_situation = 'Incident'
        
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
