"""
Forms routes - daily form CRUD operations.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from datetime import datetime, date
from utils.auth import login_required, admin_required, get_current_user, can_view_form, can_edit_form
from utils.jalali import parse_jalali_date, jalali_to_gregorian, get_jalali_weekday
from models import db, User, Project, DailyFormSubmission, Notification
from models import HumanResource, ToolEquipment, ConstructionOperation, IncomingMaterial
from models import ClimateCondition, ProjectIssue, Safety, Event, Comment
from utils.helpers import generate_document_code, safe_int, safe_float
from translations import get_translation

forms_bp = Blueprint('forms', __name__)


@forms_bp.route('/my-forms')
@login_required
def my_forms():
    """List employee's own forms."""
    user = get_current_user()
    lang = session.get('lang', 'en')
    
    db_user = User.query.filter_by(username=user['username']).first()
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = DailyFormSubmission.query.filter_by(submitted_by=db_user.id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    forms = query.order_by(DailyFormSubmission.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('forms/list.html', forms=forms, lang=lang, page_title='my_forms')


@forms_bp.route('/all')
@login_required
def all_forms():
    """List all forms (admin/boss only)."""
    user = get_current_user()
    lang = session.get('lang', 'en')
    
    if user['role'] == 'employee':
        return redirect(url_for('forms.my_forms'))
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    project_filter = request.args.get('project', '', type=int)
    employee_filter = request.args.get('employee', '', type=int)
    
    query = DailyFormSubmission.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if project_filter:
        query = query.filter_by(project_id=project_filter)
    if employee_filter:
        query = query.filter_by(submitted_by=employee_filter)
    
    forms = query.order_by(DailyFormSubmission.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    projects = Project.query.filter_by(is_active=True).all()
    employees = User.query.filter_by(role='employee').all()
    
    return render_template('forms/list.html', forms=forms, lang=lang, 
                          projects=projects, employees=employees, page_title='all_forms')


@forms_bp.route('/pending')
@admin_required
def pending_forms():
    """List pending forms for review (admin only)."""
    lang = session.get('lang', 'en')
    
    page = request.args.get('page', 1, type=int)
    
    forms = DailyFormSubmission.query.filter_by(status='pending').order_by(
        DailyFormSubmission.submitted_at.asc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('forms/list.html', forms=forms, lang=lang, page_title='pending_forms')


@forms_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_form():
    """Create new daily form."""
    user = get_current_user()
    lang = session.get('lang', 'en')
    
    db_user = User.query.filter_by(username=user['username']).first()
    projects = Project.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        return save_form(request, db_user, None)
    
    # Get form configuration for positions and equipment
    from forms.daily_form_configuration import configuration
    
    return render_template('forms/form.html', lang=lang, projects=projects, 
                          form=None, configuration=configuration, mode='new')


@forms_bp.route('/new/choose-method')
@login_required
def choose_form_method():
    """Choose method for filling the daily form (manual or Excel upload)."""
    lang = session.get('lang', 'en')
    return render_template('forms/choose_method.html', lang=lang)


@forms_bp.route('/template/download')
@login_required
def download_template():
    """Download the Excel template for daily form."""
    from utils.excel_template import create_daily_form_template
    
    output = create_daily_form_template()
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='daily_form_template.xlsx'
    )


@forms_bp.route('/new/upload', methods=['GET', 'POST'])
@login_required
def upload_excel_form():
    """Upload Excel file to fill the daily form."""
    user = get_current_user()
    lang = session.get('lang', 'en')
    t = lambda key: get_translation(key, lang)
    projects = Project.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        if 'excel_file' not in request.files:
            flash(t('no_file_uploaded'), 'danger')
            return redirect(request.url)
        
        file = request.files['excel_file']
        if file.filename == '':
            flash(t('no_file_selected'), 'danger')
            return redirect(request.url)
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            flash(t('excel_files_only'), 'danger')
            return redirect(request.url)
            return redirect(request.url)
        
        try:
            from utils.excel_template import parse_daily_form_excel
            excel_data = parse_daily_form_excel(file)
            
            # Store parsed data in session to use in form
            session['excel_form_data'] = excel_data
            
            # Get form configuration
            from forms.daily_form_configuration import configuration
            
            return render_template('forms/form.html', lang=lang, projects=projects, 
                                  form=None, configuration=configuration, mode='new',
                                  excel_data=excel_data)
        except Exception as e:
            flash(f'{t("excel_parse_error")}: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('forms/upload_excel.html', lang=lang)


@forms_bp.route('/<int:form_id>')
@login_required
def view_form(form_id):
    """View a daily form."""
    user = get_current_user()
    lang = session.get('lang', 'en')
    
    form = DailyFormSubmission.query.get_or_404(form_id)
    
    # Check permission
    db_user = User.query.filter_by(username=user['username']).first()
    if not can_view_form(form, user):
        t = lambda key: get_translation(key, lang)
        flash(t('access_denied'), 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('forms/view.html', form=form, lang=lang)


@forms_bp.route('/<int:form_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_form(form_id):
    """Edit a daily form (only draft or rejected)."""
    user = get_current_user()
    lang = session.get('lang', 'en')
    
    form = DailyFormSubmission.query.get_or_404(form_id)
    db_user = User.query.filter_by(username=user['username']).first()
    
    if not can_edit_form(form, user):
        t = lambda key: get_translation(key, lang)
        flash(t('cannot_edit_form'), 'danger')
        return redirect(url_for('forms.view_form', form_id=form_id))
    
    projects = Project.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        return save_form(request, db_user, form)
    
    from forms.daily_form_configuration import configuration
    
    return render_template('forms/form.html', lang=lang, projects=projects, 
                          form=form, configuration=configuration, mode='edit')


@forms_bp.route('/<int:form_id>/review', methods=['GET', 'POST'])
@admin_required
def review_form(form_id):
    """Review and approve/reject a form."""
    user = get_current_user()
    lang = session.get('lang', 'en')
    
    form = DailyFormSubmission.query.get_or_404(form_id)
    db_user = User.query.filter_by(username=user['username']).first()
    
    if form.status != 'pending':
        t = lambda key: get_translation(key, lang)
        flash(t('form_not_pending'), 'warning')
        return redirect(url_for('forms.view_form', form_id=form_id))
    
    if request.method == 'POST':
        action = request.form.get('action')
        comment = request.form.get('comment', '').strip()
        
        if action == 'approve':
            form.approve(db_user.id, comment)
            
            # Create notification for employee
            notification = Notification.create_form_approved_notification(form)
            db.session.add(notification)
            
            t = lambda key: get_translation(key, lang)
            flash(t('form_approved'), 'success')
            
        elif action == 'reject':
            if not comment:
                t = lambda key: get_translation(key, lang)
                flash(t('rejection_reason_required'), 'danger')
                return render_template('forms/review.html', form=form, lang=lang)
            
            form.reject(db_user.id, comment)
            
            # Create notification for employee
            notification = Notification.create_form_rejected_notification(form, comment)
            db.session.add(notification)
            
            # Add comment
            review_comment = Comment(
                daily_form_id=form.id,
                user_id=db_user.id,
                content=comment,
                comment_type='rejection'
            )
            db.session.add(review_comment)
            
            t = lambda key: get_translation(key, lang)
            flash(t('form_rejected'), 'info')
        
        db.session.commit()
        return redirect(url_for('forms.pending_forms'))
    
    return render_template('forms/review.html', form=form, lang=lang)


@forms_bp.route('/<int:form_id>/delete', methods=['POST'])
@login_required
def delete_form(form_id):
    """Delete a form (only draft)."""
    user = get_current_user()
    lang = session.get('lang', 'en')
    t = lambda key: get_translation(key, lang)
    
    form = DailyFormSubmission.query.get_or_404(form_id)
    
    if form.submitted_by_user.username != user['username']:
        flash(t('access_denied'), 'danger')
        return redirect(url_for('main.dashboard'))
    
    if form.status != 'draft':
        flash(t('only_draft_can_delete'), 'warning')
        return redirect(url_for('forms.view_form', form_id=form_id))
    
    db.session.delete(form)
    db.session.commit()
    
    flash(t('form_deleted'), 'success')
    return redirect(url_for('forms.my_forms'))


def save_form(request, db_user, existing_form=None):
    """Save form data (create or update)."""
    action = request.form.get('action', 'draft')
    
    # Basic form data
    project_id = request.form.get('project_id', type=int)
    form_date_str = request.form.get('form_date')
    day_of_week = request.form.get('day_of_week')
    work_shift = request.form.get('work_shift')
    
    if not project_id or not form_date_str:
        lang = session.get('lang', 'en')
        t = lambda key: get_translation(key, lang)
        flash(t('project_date_required'), 'danger')
        return redirect(request.url)
    
    try:
        # Parse Jalali date and convert to Gregorian for storage
        j_date = parse_jalali_date(form_date_str)
        form_date = jalali_to_gregorian(j_date)
        
        # Auto-set day of week if not provided
        if not day_of_week:
            lang = session.get('lang', 'fa')
            day_of_week = get_jalali_weekday(form_date, lang)
    except Exception as e:
        lang = session.get('lang', 'en')
        t = lambda key: get_translation(key, lang)
        flash(t('invalid_date_format'), 'danger')
        return redirect(request.url)
    
    # Create or update form
    if existing_form:
        form = existing_form
        form.project_id = project_id
        form.form_date = form_date
        form.day_of_week = day_of_week
        form.work_shift = work_shift
        
        # Clear existing section data
        HumanResource.query.filter_by(daily_form_id=form.id).delete()
        ToolEquipment.query.filter_by(daily_form_id=form.id).delete()
        ConstructionOperation.query.filter_by(daily_form_id=form.id).delete()
        IncomingMaterial.query.filter_by(daily_form_id=form.id).delete()
        ClimateCondition.query.filter_by(daily_form_id=form.id).delete()
        ProjectIssue.query.filter_by(daily_form_id=form.id).delete()
        Safety.query.filter_by(daily_form_id=form.id).delete()
        Event.query.filter_by(daily_form_id=form.id).delete()
    else:
        # Generate document code
        project = Project.query.get(project_id)
        existing_count = DailyFormSubmission.query.filter_by(
            project_id=project_id,
            form_date=form_date
        ).count()
        doc_code = generate_document_code(project.project_code, form_date, existing_count + 1)
        
        form = DailyFormSubmission(
            document_code=doc_code,
            project_id=project_id,
            form_date=form_date,
            day_of_week=day_of_week,
            work_shift=work_shift,
            submitted_by=db_user.id,
            status='draft'
        )
        db.session.add(form)
        db.session.flush()  # Get the form ID
    
    # Save Human Resources
    hr_posts = request.form.getlist('hr_post[]')
    hr_count = request.form.getlist('hr_count[]')
    hr_hours = request.form.getlist('hr_hours[]')
    hr_notes = request.form.getlist('hr_notes[]')
    
    for i in range(len(hr_posts)):
        if hr_posts[i]:
            hr = HumanResource(
                daily_form_id=form.id,
                post=hr_posts[i],
                count=safe_int(hr_count[i] if i < len(hr_count) else 0),
                working_hours=safe_float(hr_hours[i] if i < len(hr_hours) else 0),
                notes=hr_notes[i] if i < len(hr_notes) else ''
            )
            db.session.add(hr)
    
    # Save Tools and Equipment
    eq_names = request.form.getlist('eq_name[]')
    eq_active = request.form.getlist('eq_active[]')
    eq_hours = request.form.getlist('eq_hours[]')
    eq_situation = request.form.getlist('eq_situation[]')
    eq_reason = request.form.getlist('eq_reason[]')
    
    for i in range(len(eq_names)):
        if eq_names[i]:
            eq = ToolEquipment(
                daily_form_id=form.id,
                equipment_name=eq_names[i],
                count_active=safe_int(eq_active[i] if i < len(eq_active) else 0),
                working_hours=safe_float(eq_hours[i] if i < len(eq_hours) else 0),
                situation=eq_situation[i] if i < len(eq_situation) else '',
                inactivity_reason=eq_reason[i] if i < len(eq_reason) else ''
            )
            db.session.add(eq)
    
    # Save Construction Operations
    op_types = request.form.getlist('op_type[]')
    op_start = request.form.getlist('op_start[]')
    op_end = request.form.getlist('op_end[]')
    op_unit = request.form.getlist('op_unit[]')
    op_progress = request.form.getlist('op_progress[]')
    op_map = request.form.getlist('op_map[]')
    
    for i in range(len(op_types)):
        if op_types[i]:
            op = ConstructionOperation(
                daily_form_id=form.id,
                operation_type=op_types[i],
                start_km=safe_float(op_start[i] if i < len(op_start) else None),
                end_km=safe_float(op_end[i] if i < len(op_end) else None),
                unit=op_unit[i] if i < len(op_unit) else '',
                progress=safe_float(op_progress[i] if i < len(op_progress) else 0),
                map_number=op_map[i] if i < len(op_map) else ''
            )
            db.session.add(op)
    
    # Save Incoming Materials
    mat_types = request.form.getlist('mat_type[]')
    mat_incoming = request.form.getlist('mat_incoming[]')
    mat_cum_in = request.form.getlist('mat_cum_in[]')
    mat_used = request.form.getlist('mat_used[]')
    mat_cum_used = request.form.getlist('mat_cum_used[]')
    mat_storage = request.form.getlist('mat_storage[]')
    mat_waybill = request.form.getlist('mat_waybill[]')
    
    for i in range(len(mat_types)):
        if mat_types[i]:
            mat = IncomingMaterial(
                daily_form_id=form.id,
                material_type=mat_types[i],
                incoming_amount=safe_float(mat_incoming[i] if i < len(mat_incoming) else 0),
                cumulative_incoming=safe_float(mat_cum_in[i] if i < len(mat_cum_in) else 0),
                used_amount=safe_float(mat_used[i] if i < len(mat_used) else 0),
                cumulative_used=safe_float(mat_cum_used[i] if i < len(mat_cum_used) else 0),
                storage_place=mat_storage[i] if i < len(mat_storage) else '',
                waybill_number=mat_waybill[i] if i < len(mat_waybill) else ''
            )
            db.session.add(mat)
    
    # Save Climate Condition
    climate = ClimateCondition(
        daily_form_id=form.id,
        min_temperature=safe_float(request.form.get('min_temp')),
        max_temperature=safe_float(request.form.get('max_temp')),
        humidity=safe_float(request.form.get('humidity')),
        weather_type=request.form.get('weather_type', ''),
        wind_speed=request.form.get('wind_speed', ''),
        climate_effect=request.form.get('climate_effect', ''),
        is_clear=request.form.get('weather_type') == 'clear',
        is_cloudy=request.form.get('weather_type') == 'cloudy',
        is_rainy=request.form.get('weather_type') == 'rainy',
        is_foggy=request.form.get('weather_type') == 'foggy',
        is_snowy=request.form.get('weather_type') == 'snowy'
    )
    db.session.add(climate)
    
    # Save Project Issues
    issue_types = request.form.getlist('issue_type[]')
    issue_effects = request.form.getlist('issue_effect[]')
    issue_locations = request.form.getlist('issue_location[]')
    issue_notes = request.form.getlist('issue_notes[]')
    
    for i in range(len(issue_types)):
        if issue_types[i]:
            issue = ProjectIssue(
                daily_form_id=form.id,
                issue_type=issue_types[i],
                effect=issue_effects[i] if i < len(issue_effects) else '',
                location_km=safe_float(issue_locations[i] if i < len(issue_locations) else None),
                notes=issue_notes[i] if i < len(issue_notes) else ''
            )
            db.session.add(issue)
    
    # Save Safety
    safety = Safety(
        daily_form_id=form.id,
        safety_situation=request.form.get('safety_situation', ''),
        safety_inspection='safety_inspection' in request.form,
        incident_occurred='incident_occurred' in request.form,
        incident_explanation=request.form.get('incident_explanation', '')
    )
    db.session.add(safety)
    
    # Save Events
    event_names = request.form.getlist('event_name[]')
    event_explanations = request.form.getlist('event_explanation[]')
    
    for i in range(len(event_names)):
        if event_names[i]:
            event = Event(
                daily_form_id=form.id,
                event_name=event_names[i],
                explanation=event_explanations[i] if i < len(event_explanations) else ''
            )
            db.session.add(event)
    
    # Submit if requested
    if action == 'submit':
        form.submit()
        
        # Notify admins
        admins = User.query.filter_by(role='admin').all()
        notifications = Notification.create_form_submitted_notification(admins, form)
        for notif in notifications:
            db.session.add(notif)
        
        lang = session.get('lang', 'en')
        t = lambda key: get_translation(key, lang)
        flash(t('form_submitted'), 'success')
    else:
        lang = session.get('lang', 'en')
        t = lambda key: get_translation(key, lang)
        flash(t('form_saved_draft'), 'success')
    
    db.session.commit()
    
    return redirect(url_for('forms.view_form', form_id=form.id))
