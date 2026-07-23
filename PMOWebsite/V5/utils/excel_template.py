"""
Excel template generator and parser for daily forms.
Updated to match the current daily form structure (V5).
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

    headers = ["تاریخ (1404/01/01)", "روز هفته", "شیفت کاری", "پروژه"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col)].width = 20
    current_row += 1

    for col in range(1, 5):
        cell = ws.cell(row=current_row, column=col, value="")
        cell.border = thin_border
        cell.alignment = center_align

    if project_name:
        ws.cell(row=current_row, column=4, value=project_name)

    # Dropdown: shift
    shift_validation = DataValidation(type="list", formula1='"صبح,شب"', allow_blank=True)
    shift_validation.error = "لطفاً یکی از گزینه‌ها را انتخاب کنید"
    shift_validation.errorTitle = "شیفت نامعتبر"
    shift_validation.prompt = "شیفت کاری را انتخاب کنید"
    shift_validation.promptTitle = "شیفت کاری"
    ws.add_data_validation(shift_validation)
    shift_validation.add(ws.cell(row=current_row, column=3))

    # Dropdown: day of week
    weekday_validation = DataValidation(
        type="list",
        formula1='"شنبه,یکشنبه,دوشنبه,سه‌شنبه,چهارشنبه,پنج‌شنبه,جمعه"',
        allow_blank=True
    )
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

    hr_headers = ["سمت", "تعداد", "ساعت کار", "توضیحات"]
    for col, header in enumerate(hr_headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    current_row += 1

    for position in config.get("Human_Resources", []):
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

    # Pre-fill equipment type + model rows from config
    eq_start_row = current_row
    equipment_config = config.get("Tools_And_Equipments", {})
    for eq_type, models in equipment_config.items():
        if models:
            for model in models:
                ws.cell(row=current_row, column=1, value=eq_type).border = thin_border
                ws.cell(row=current_row, column=1).alignment = right_align
                ws.cell(row=current_row, column=2, value=model).border = thin_border
                ws.cell(row=current_row, column=2).alignment = right_align
                for col in range(3, 7):
                    cell = ws.cell(row=current_row, column=col, value="")
                    cell.border = thin_border
                    cell.alignment = center_align
                current_row += 1
        else:
            ws.cell(row=current_row, column=1, value=eq_type).border = thin_border
            ws.cell(row=current_row, column=1).alignment = right_align
            ws.cell(row=current_row, column=2, value="").border = thin_border
            for col in range(3, 7):
                cell = ws.cell(row=current_row, column=col, value="")
                cell.border = thin_border
                cell.alignment = center_align
            current_row += 1

    # Extra empty rows
    for _ in range(3):
        for col in range(1, 7):
            cell = ws.cell(row=current_row, column=col, value="")
            cell.border = thin_border
            cell.alignment = center_align
        current_row += 1
    eq_end_row = current_row - 1

    # Dropdown: equipment situation (column 5)
    if eq_start_row <= eq_end_row:
        eq_situation_validation = DataValidation(
            type="list",
            formula1='"فعال,غیرفعال,در حال تعمیر"',
            allow_blank=True
        )
        eq_situation_validation.error = "لطفاً یکی از گزینه‌ها را انتخاب کنید"
        ws.add_data_validation(eq_situation_validation)
        for row in range(eq_start_row, eq_end_row + 1):
            eq_situation_validation.add(ws.cell(row=row, column=5))

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

    # Pre-fill operations from config with their units
    activities = config.get("Daily_Activity_Report", {})
    for operation, unit in activities.items():
        ws.cell(row=current_row, column=1, value=operation).border = thin_border
        ws.cell(row=current_row, column=1).alignment = right_align
        ws.cell(row=current_row, column=2, value="").border = thin_border
        ws.cell(row=current_row, column=2).alignment = center_align
        ws.cell(row=current_row, column=3, value="").border = thin_border
        ws.cell(row=current_row, column=3).alignment = center_align
        ws.cell(row=current_row, column=4, value=unit).border = thin_border
        ws.cell(row=current_row, column=4).alignment = center_align
        ws.cell(row=current_row, column=5, value="").border = thin_border
        ws.cell(row=current_row, column=5).alignment = center_align
        current_row += 1

    # Extra empty rows
    for _ in range(3):
        for col in range(1, 6):
            cell = ws.cell(row=current_row, column=col, value="")
            cell.border = thin_border
            cell.alignment = center_align
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

    # Pre-fill materials from config with units
    materials_config = config.get("Incoming_Materials_And_Goods", {})
    for material, unit in materials_config.items():
        ws.cell(row=current_row, column=1, value=material).border = thin_border
        ws.cell(row=current_row, column=1).alignment = right_align
        ws.cell(row=current_row, column=2, value=unit).border = thin_border
        ws.cell(row=current_row, column=2).alignment = center_align
        for col in range(3, 7):
            cell = ws.cell(row=current_row, column=col, value="")
            cell.border = thin_border
            cell.alignment = center_align
        current_row += 1

    # Extra empty rows
    for _ in range(3):
        for col in range(1, 7):
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

    climate_headers = ["حداقل دما", "حداکثر دما", "رطوبت (%)", "وضعیت آب و هوا", "سرعت باد", "تاثیر بر پروژه"]
    for col, header in enumerate(climate_headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    current_row += 1

    climate_data_row = current_row
    for col in range(1, 7):
        cell = ws.cell(row=current_row, column=col, value="")
        cell.border = thin_border
        cell.alignment = center_align

    # Dropdown: weather type (column 4)
    weather_validation = DataValidation(type="list", formula1='"صاف,ابری,بارانی,مه‌آلود,برفی"', allow_blank=True)
    ws.add_data_validation(weather_validation)
    weather_validation.add(ws.cell(row=climate_data_row, column=4))

    # Dropdown: wind speed (column 5)
    wind_validation = DataValidation(type="list", formula1='"آرام,معمولی,تند"', allow_blank=True)
    ws.add_data_validation(wind_validation)
    wind_validation.add(ws.cell(row=climate_data_row, column=5))

    # Dropdown: climate effect (column 6)
    effect_validation = DataValidation(type="list", formula1='"بدون تاثیر,کندی پیشرفت,توقف کار"', allow_blank=True)
    ws.add_data_validation(effect_validation)
    effect_validation.add(ws.cell(row=climate_data_row, column=6))

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

    # Pre-fill issues from config
    for issue in config.get("Project_Issues", []):
        ws.cell(row=current_row, column=1, value=issue).border = thin_border
        ws.cell(row=current_row, column=1).alignment = right_align
        for col in range(2, 7):
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

    safety_headers = ["وضعیت ایمنی", "بازرسی ایمنی", "حادثه رخ داده", "توضیحات حادثه"]
    for col, header in enumerate(safety_headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    current_row += 1

    safety_data_row = current_row
    for col in range(1, 5):
        cell = ws.cell(row=current_row, column=col, value="")
        cell.border = thin_border
        cell.alignment = center_align

    # Dropdown: safety situation (column 1) - matches form: NoIncident / NearMiss / Incident
    safety_situation_validation = DataValidation(
        type="list",
        formula1='"بدون حادثه,شبه حادثه,حادثه"',
        allow_blank=True
    )
    ws.add_data_validation(safety_situation_validation)
    safety_situation_validation.add(ws.cell(row=safety_data_row, column=1))

    # Dropdown: safety inspection (column 2)
    yes_no_validation1 = DataValidation(type="list", formula1='"بله,خیر"', allow_blank=True)
    ws.add_data_validation(yes_no_validation1)
    yes_no_validation1.add(ws.cell(row=safety_data_row, column=2))

    # Dropdown: incident occurred (column 3)
    yes_no_validation2 = DataValidation(type="list", formula1='"بله,خیر"', allow_blank=True)
    ws.add_data_validation(yes_no_validation2)
    yes_no_validation2.add(ws.cell(row=safety_data_row, column=3))

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

    # Add empty rows for events with dropdown for event_type
    event_start_row = current_row
    for _ in range(5):
        for col in range(1, 4):
            cell = ws.cell(row=current_row, column=col, value="")
            cell.border = thin_border
            cell.alignment = center_align
        current_row += 1
    event_end_row = current_row - 1

    # Dropdown: event type (column 1)
    event_type_validation = DataValidation(
        type="list",
        formula1='"بازدید,جلسه,سایر"',
        allow_blank=True
    )
    ws.add_data_validation(event_type_validation)
    for row in range(event_start_row, event_end_row + 1):
        event_type_validation.add(ws.cell(row=row, column=1))

    # Set print area
    ws.print_title_rows = '1:1'

    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return output


def parse_daily_form_excel(file):
    """
    Parse an uploaded Excel file and extract daily form data.
    Returns a dictionary matching the form structure expected by the template.
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

    # ---- Parse Date and Time ----
    if 'date_time' in section_rows:
        data_row = section_rows['date_time'] + 2  # skip header row

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

    # ---- Parse Human Resources ----
    if 'human_resources' in section_rows:
        start_row = section_rows['human_resources'] + 2
        end_row = section_rows.get('tools_equipment', ws.max_row) - 2

        for row in range(start_row, end_row + 1):
            post = get_value(row, 1)
            if post:
                count = get_value(row, 2)
                hours = get_value(row, 3)
                notes = get_value(row, 4)

                if count or hours:
                    data['human_resources'].append({
                        'post': post,
                        'count': count,
                        'working_hours': hours,
                        'notes': notes
                    })

    # ---- Parse Tools and Equipment (type + model) ----
    if 'tools_equipment' in section_rows:
        start_row = section_rows['tools_equipment'] + 2
        end_row = section_rows.get('operations', ws.max_row) - 2

        for row in range(start_row, end_row + 1):
            eq_type = get_value(row, 1)
            if eq_type:
                eq_model = get_value(row, 2)
                count = get_value(row, 3)
                hours = get_value(row, 4)
                situation_val = get_value(row, 5)
                reason = get_value(row, 6)

                # Convert Persian situation to English for database
                situation = _parse_equipment_situation(situation_val)

                if count or hours or situation:
                    data['tools_equipment'].append({
                        'equipment_type': eq_type,
                        'equipment_model': eq_model if eq_model else None,
                        'count_active': count,
                        'working_hours': hours,
                        'situation': situation,
                        'inactivity_reason': reason
                    })

    # ---- Parse Construction Operations (station format) ----
    if 'operations' in section_rows:
        start_row = section_rows['operations'] + 2
        end_row = section_rows.get('materials', ws.max_row) - 2

        for row in range(start_row, end_row + 1):
            op_type = get_value(row, 1)
            if op_type:
                start_station = get_value(row, 2)
                end_station = get_value(row, 3)
                unit = get_value(row, 4)
                amount = get_value(row, 5)

                if start_station or end_station or amount:
                    data['operations'].append({
                        'operation_type': op_type,
                        'start_station': start_station,
                        'end_station': end_station,
                        'unit': unit,
                        'amount': amount
                    })

    # ---- Parse Incoming Materials (with unit column) ----
    if 'materials' in section_rows:
        start_row = section_rows['materials'] + 2
        end_row = section_rows.get('climate', ws.max_row) - 2

        for row in range(start_row, end_row + 1):
            mat_type = get_value(row, 1)
            if mat_type:
                mat_unit = get_value(row, 2)
                incoming = get_value(row, 3)
                used = get_value(row, 4)
                storage = get_value(row, 5)
                waybill = get_value(row, 6)

                if incoming or used:
                    data['materials'].append({
                        'material_type': mat_type,
                        'material_unit': mat_unit,
                        'incoming_amount': incoming,
                        'used_amount': used,
                        'storage_place': storage,
                        'waybill_number': waybill
                    })

    # ---- Parse Climate Condition ----
    if 'climate' in section_rows:
        base_row = section_rows['climate']
        data_row = _find_data_row(ws, base_row, [1, 4])

        weather_type = _parse_weather_type(get_value(data_row, 4))
        wind_speed = _parse_wind_speed(get_value(data_row, 5))
        climate_effect = _parse_climate_effect(get_value(data_row, 6))

        data['climate'] = {
            'min_temperature': get_value(data_row, 1),
            'max_temperature': get_value(data_row, 2),
            'humidity': get_value(data_row, 3),
            'weather_type': weather_type,
            'wind_speed': wind_speed,
            'climate_effect': climate_effect
        }

    # ---- Parse Project Issues (with start_time, end_time) ----
    if 'issues' in section_rows:
        start_row = section_rows['issues'] + 2
        end_row = section_rows.get('safety', ws.max_row) - 2

        for row in range(start_row, end_row + 1):
            issue_type = get_value(row, 1)
            if issue_type:
                effect = get_value(row, 2)
                location = get_value(row, 3)
                start_time = get_value(row, 4)
                end_time = get_value(row, 5)
                notes = get_value(row, 6)

                if effect or notes or location:
                    data['issues'].append({
                        'issue_type': issue_type,
                        'effect': effect,
                        'location_station': location,
                        'start_time': _format_time_value(start_time),
                        'end_time': _format_time_value(end_time),
                        'notes': notes
                    })

    # ---- Parse Safety (updated situation values) ----
    if 'safety' in section_rows:
        base_row = section_rows['safety']
        data_row = _find_data_row(ws, base_row, [1, 2])

        situation_val = get_value(data_row, 1)
        safety_situation = _parse_safety_situation(situation_val)

        data['safety'] = {
            'safety_situation': safety_situation,
            'safety_inspection': to_bool(get_value(data_row, 2)),
            'incident_occurred': to_bool(get_value(data_row, 3)),
            'incident_explanation': get_value(data_row, 4)
        }

    # ---- Parse Events (with event_type) ----
    if 'events' in section_rows:
        start_row = section_rows['events'] + 2

        for row in range(start_row, min(start_row + 10, ws.max_row + 1)):
            event_type_val = get_value(row, 1)
            event_name = get_value(row, 2)
            if event_name:
                event_type = _parse_event_type(event_type_val)
                explanation = get_value(row, 3)
                data['events'].append({
                    'event_type': event_type,
                    'event_name': event_name,
                    'explanation': explanation
                })

    return data


# =============================================================================
# HELPER FUNCTIONS FOR PARSING
# =============================================================================

def _find_data_row(ws, base_row, check_columns):
    """Find the actual data row after a section header.
    Checks rows +2, +3, +4 for any data in the given columns.
    """
    def get_val(r, c):
        val = ws.cell(row=r, column=c).value
        return str(val).strip() if val is not None else ""

    for offset in [2, 3, 4]:
        test_row = base_row + offset
        if test_row > ws.max_row:
            break
        for col in check_columns:
            if get_val(test_row, col):
                return test_row
    return base_row + 2  # default


def _parse_equipment_situation(val):
    """Convert Persian/English equipment situation to database value."""
    if not val:
        return ''
    val_lower = val.strip().lower()
    if 'غیرفعال' in val_lower or 'غیر فعال' in val_lower:
        return 'Inactive'
    elif 'فعال' in val_lower:
        return 'Active'
    elif 'تعمیر' in val_lower or 'repair' in val_lower:
        return 'Under Repair'
    elif 'active' in val_lower and 'in' not in val_lower:
        return 'Active'
    elif 'inactive' in val_lower:
        return 'Inactive'
    return ''


def _parse_weather_type(val):
    """Convert Persian weather to database value."""
    if not val:
        return ''
    val_lower = val.strip().lower()
    if 'صاف' in val_lower or 'clear' in val_lower:
        return 'clear'
    elif 'ابری' in val_lower or 'cloudy' in val_lower:
        return 'cloudy'
    elif 'بارانی' in val_lower or 'rain' in val_lower:
        return 'rainy'
    elif 'مه' in val_lower or 'fog' in val_lower:
        return 'foggy'
    elif 'برفی' in val_lower or 'snow' in val_lower:
        return 'snowy'
    return ''


def _parse_wind_speed(val):
    """Convert Persian wind speed to database value."""
    if not val:
        return ''
    val_lower = val.strip().lower()
    if 'آرام' in val_lower or 'slow' in val_lower:
        return 'slow'
    elif 'تند' in val_lower or 'fast' in val_lower:
        return 'fast'
    elif 'معمولی' in val_lower or 'normal' in val_lower:
        return 'normal'
    return ''


def _parse_climate_effect(val):
    """Convert Persian climate effect to database value."""
    if not val:
        return ''
    val_lower = val.strip().lower()
    if 'بدون' in val_lower or 'no' in val_lower:
        return 'no_effect'
    elif 'کندی' in val_lower or 'slow' in val_lower:
        return 'slow_progress'
    elif 'توقف' in val_lower or 'stop' in val_lower:
        return 'stopped'
    return ''


def _parse_safety_situation(val):
    """Convert Persian safety situation to database value."""
    if not val:
        return ''
    val_lower = val.strip().lower()
    # Order matters: check compound phrases before simple ones
    if 'بدون حادثه' in val_lower or 'بدون' in val_lower:
        return 'NoIncident'
    elif 'شبه حادثه' in val_lower or 'شبه' in val_lower or 'near' in val_lower:
        return 'NearMiss'
    elif 'حادثه' in val_lower:
        return 'Incident'
    elif 'no incident' in val_lower or 'no_incident' in val_lower or 'noincident' in val_lower:
        return 'NoIncident'
    elif 'near' in val_lower:
        return 'NearMiss'
    elif 'incident' in val_lower:
        return 'Incident'
    return ''


def _parse_event_type(val):
    """Convert Persian event type to database value."""
    if not val:
        return ''
    val_lower = val.strip().lower()
    if 'بازدید' in val_lower or 'visit' in val_lower:
        return 'Visit'
    elif 'جلسه' in val_lower or 'meeting' in val_lower:
        return 'Meeting'
    elif 'سایر' in val_lower or 'other' in val_lower:
        return 'Other'
    return ''


def _format_time_value(val):
    """Format a time value from Excel to HH:MM string.
    Handles datetime.time objects and string values.
    """
    if not val:
        return ''
    import datetime
    if isinstance(val, datetime.time):
        return val.strftime('%H:%M')
    val_str = str(val).strip()
    # Already in HH:MM format
    if ':' in val_str:
        parts = val_str.split(':')
        try:
            return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
        except (ValueError, IndexError):
            pass
    return val_str
