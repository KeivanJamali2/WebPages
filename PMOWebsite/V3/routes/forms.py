"""
Forms routes - daily form CRUD operations.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from datetime import datetime, date
from utils.auth import login_required, admin_required, get_current_user, can_view_form, can_edit_form
from utils.jalali import parse_jalali_date, jalali_to_gregorian, get_jalali_weekday
from utils.documents import save_form_documents, delete_form_documents, get_documents_full_path, list_documents_in_zip, format_file_size, get_zip_file_size
from models import db, User, Project, DailyFormSubmission, Notification
from models import HumanResource, ToolEquipment, ConstructionOperation, IncomingMaterial
from models import ClimateCondition, ProjectIssue, Safety, Event, Comment
from utils.helpers import generate_document_code, safe_int, safe_float
from translations import get_translation
import os

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
    
    projects = Project.query.filter_by(status='active').all()
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
    projects = Project.query.filter_by(status='active').all()
    
    if request.method == 'POST':
        return save_form(request, db_user, None)
    
    # Get form configuration for positions and equipment
    from forms.daily_form_configuration import configuration, get_configuration_for_project
    
    # Build configurations for all projects (for JavaScript)
    project_configs = {}
    for project in projects:
        project_configs[project.id] = get_configuration_for_project(project.project_code)
    
    return render_template('forms/form.html', lang=lang, projects=projects, 
                          form=None, configuration=configuration, 
                          project_configs=project_configs, mode='new')


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
    from forms.daily_form_configuration import get_configuration_for_project
    
    project_id = request.args.get('project_id', type=int)
    project_name = None
    project_code = "daily_form"
    config = None
    
    if project_id:
        project = Project.query.get(project_id)
        if project:
            config = get_configuration_for_project(project.project_code)
            project_name = project.name
            project_code = project.project_code
    
    output = create_daily_form_template(config, project_name)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'{project_code}_template.xlsx'
    )


@forms_bp.route('/new/upload', methods=['GET', 'POST'])
@login_required
def upload_excel_form():
    """Upload Excel file to fill the daily form."""
    user = get_current_user()
    lang = session.get('lang', 'en')
    t = lambda key: get_translation(key, lang)
    projects = Project.query.filter_by(status='active').all()
    
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
        
        try:
            from utils.excel_template import parse_daily_form_excel
            excel_data = parse_daily_form_excel(file)
            
            # Store parsed data in session to use in form
            session['excel_form_data'] = excel_data
            
            # Get form configuration based on selected project
            from forms.daily_form_configuration import configuration as default_configuration, get_configuration_for_project
            
            # Use the project selected by the user in the upload form
            config_to_use = default_configuration
            selected_project_id = request.form.get('project_id')
            selected_project = None
            
            if selected_project_id:
                selected_project = Project.query.get(int(selected_project_id))
                if selected_project and selected_project.project_code:
                    project_config = get_configuration_for_project(selected_project.project_code)
                    if project_config:
                        config_to_use = project_config
            
            # Build configurations for all projects (for JavaScript)
            project_configs = {}
            for project in projects:
                project_configs[project.id] = get_configuration_for_project(project.project_code)
            
            return render_template('forms/form.html', lang=lang, projects=projects, 
                                  form=None, configuration=config_to_use, 
                                  project_configs=project_configs, mode='new',
                                  excel_data=excel_data, selected_project=selected_project)
        except Exception as e:
            flash(f'{t("excel_parse_error")}: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('forms/upload_excel.html', lang=lang, projects=projects)


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
    
    projects = Project.query.filter_by(status='active').all()
    
    if request.method == 'POST':
        return save_form(request, db_user, form)
    
    from forms.daily_form_configuration import configuration as default_configuration, get_configuration_for_project
    
    # Use project-specific configuration for the form being edited
    config_to_use = default_configuration
    if form.project and form.project.project_code:
        project_config = get_configuration_for_project(form.project.project_code)
        if project_config:
            config_to_use = project_config
    
    # Build configurations for all projects (for JavaScript)
    project_configs = {}
    for project in projects:
        project_configs[project.id] = get_configuration_for_project(project.project_code)
    
    return render_template('forms/form.html', lang=lang, projects=projects, 
                          form=form, configuration=config_to_use,
                          project_configs=project_configs, mode='edit')


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


@forms_bp.route('/<int:form_id>/submit', methods=['POST'])
@login_required
def submit_draft(form_id):
    """Submit a draft form for review."""
    user = get_current_user()
    lang = session.get('lang', 'en')
    t = lambda key: get_translation(key, lang)
    
    form = DailyFormSubmission.query.get_or_404(form_id)
    
    # Check ownership
    if form.submitted_by_user.username != user['username']:
        flash(t('access_denied'), 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Check if form can be submitted (only draft forms can be submitted)
    if form.status != 'draft':
        flash(t('form_already_submitted'), 'warning')
        return redirect(url_for('forms.view_form', form_id=form_id))
    
    # Submit the form
    form.submit()
    
    # Notify admins
    admins = User.query.filter_by(role='admin').all()
    notifications = Notification.create_form_submitted_notification(admins, form)
    for notif in notifications:
        db.session.add(notif)
    
    db.session.commit()
    
    flash(t('form_submitted'), 'success')
    return redirect(url_for('forms.view_form', form_id=form_id))


@forms_bp.route('/<int:form_id>/send-back', methods=['POST'])
@admin_required
def send_back_form(form_id):
    """Send back an approved form for revision (admin only)."""
    user = get_current_user()
    lang = session.get('lang', 'en')
    t = lambda key: get_translation(key, lang)
    
    form = DailyFormSubmission.query.get_or_404(form_id)
    db_user = User.query.filter_by(username=user['username']).first()
    
    # Check if form can be sent back
    if form.status != 'approved':
        flash(t('form_not_approved'), 'warning')
        return redirect(url_for('forms.view_form', form_id=form_id))
    
    comment = request.form.get('comment', '').strip()
    if not comment:
        flash(t('reason_required'), 'danger')
        return redirect(url_for('forms.view_form', form_id=form_id))
    
    # Reject the form (send back for revision)
    form.reject(db_user.id, comment)
    
    # Create notification for employee
    notification = Notification.create_form_rejected_notification(form, comment)
    db.session.add(notification)
    
    # Add comment
    review_comment = Comment(
        daily_form_id=form.id,
        user_id=db_user.id,
        content=comment,
        comment_type='send_back'
    )
    db.session.add(review_comment)
    
    db.session.commit()
    
    flash(t('form_sent_back'), 'success')
    return redirect(url_for('forms.view_form', form_id=form_id))


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
        
        # Store existing event document filenames before clearing
        existing_event_docs = {}
        for i, event in enumerate(form.events.all()):
            if event.document_filename:
                existing_event_docs[i] = event.document_filename
        
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
        existing_event_docs = {}
        # Generate document code including project, user, date, and sequence
        project = Project.query.get(project_id)
        # Count existing forms by this user for this project on this date
        existing_count = DailyFormSubmission.query.filter_by(
            project_id=project_id,
            submitted_by=db_user.id,
            form_date=form_date
        ).count()
        doc_code = generate_document_code(
            project.project_code, 
            db_user.username, 
            form_date, 
            existing_count + 1
        )
        
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
    eq_types = request.form.getlist('eq_type[]')
    eq_models = request.form.getlist('eq_model[]')
    eq_active = request.form.getlist('eq_active[]')
    eq_hours = request.form.getlist('eq_hours[]')
    eq_situation = request.form.getlist('eq_situation[]')
    eq_reason = request.form.getlist('eq_reason[]')
    
    for i in range(len(eq_types)):
        if eq_types[i]:
            eq = ToolEquipment(
                daily_form_id=form.id,
                equipment_type=eq_types[i],
                equipment_model=eq_models[i] if i < len(eq_models) and eq_models[i] else None,
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
    op_amount = request.form.getlist('op_amount[]')
    
    for i in range(len(op_types)):
        if op_types[i]:
            op = ConstructionOperation(
                daily_form_id=form.id,
                operation_type=op_types[i],
                start_station=op_start[i] if i < len(op_start) else '',
                end_station=op_end[i] if i < len(op_end) else '',
                unit=op_unit[i] if i < len(op_unit) else '',
                amount=safe_float(op_amount[i] if i < len(op_amount) else 0)
            )
            db.session.add(op)
    
    # Save Incoming Materials
    mat_types = request.form.getlist('mat_type[]')
    mat_units = request.form.getlist('mat_unit[]')
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
                material_unit=mat_units[i] if i < len(mat_units) else '',
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
    event_types = request.form.getlist('event_type[]')
    event_names = request.form.getlist('event_name[]')
    event_explanations = request.form.getlist('event_explanation[]')
    
    # Collect event documents
    event_files = {}
    for i in range(len(event_names)):
        # Check for event document (by index)
        event_doc = request.files.get(f'event_document_{i}')
        if event_doc and event_doc.filename:
            event_files[i] = event_doc
    
    # Also check for any event documents with numeric index (for dynamically added rows)
    for key in request.files:
        if key.startswith('event_document_'):
            try:
                idx = int(key.replace('event_document_', ''))
                file = request.files[key]
                if file and file.filename and idx not in event_files:
                    event_files[idx] = file
            except ValueError:
                pass
    
    event_objects = []
    for i in range(len(event_names)):
        if event_names[i]:
            # Preserve existing document filename if no new file uploaded for this event
            preserved_doc = existing_event_docs.get(i) if i not in event_files else None
            event = Event(
                daily_form_id=form.id,
                event_type=event_types[i] if i < len(event_types) else '',
                event_name=event_names[i],
                explanation=event_explanations[i] if i < len(event_explanations) else '',
                document_filename=preserved_doc  # Will be updated if new file uploaded
            )
            db.session.add(event)
            event_objects.append((i, event))
    
    # Handle document uploads (including event documents)
    try:
        uploaded_files = request.files.getlist('form_documents[]')
        has_main_docs = uploaded_files and any(f.filename for f in uploaded_files)
        has_event_docs = bool(event_files)
        existing_path = existing_form.documents_path if existing_form else None
        
        # Always call save_form_documents - it will preserve existing files if no new uploads
        if has_main_docs or has_event_docs or existing_path:
            # Get project for folder structure
            project = Project.query.get(project_id)
            
            # Save documents (main + events), preserving existing if no new files
            documents_path = save_form_documents(
                uploaded_files if has_main_docs else [],
                project.project_code,
                form_date,
                form.document_code,
                event_files=event_files if has_event_docs else None,
                existing_path=existing_path
            )
            
            if documents_path:
                form.documents_path = documents_path
                
                # Update event document filenames for new uploads
                for idx, event in event_objects:
                    if idx in event_files:
                        from werkzeug.utils import secure_filename
                        event.document_filename = secure_filename(event_files[idx].filename)
    except ValueError as e:
        # Size limit exceeded
        lang = session.get('lang', 'en')
        t = lambda key: get_translation(key, lang)
        flash(str(e), 'danger')
        return redirect(request.url)
    except Exception as e:
        # Other upload error - log it for debugging
        import traceback
        print(f"Document upload error: {e}")
        print(traceback.format_exc())
        lang = session.get('lang', 'en')
        t = lambda key: get_translation(key, lang)
        flash(f"{t('document_upload_error')}: {str(e)}", 'danger')
    
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


@forms_bp.route('/api/previous-form')
@login_required
def get_previous_form():
    """API endpoint to get the user's last submitted form data."""
    user = get_current_user()
    db_user = User.query.filter_by(username=user['username']).first()
    
    # Get optional project_id filter
    project_id = request.args.get('project_id', type=int)
    
    # Find the user's last form (pending or approved, excluding drafts and rejected)
    query = DailyFormSubmission.query.filter_by(submitted_by=db_user.id)
    query = query.filter(DailyFormSubmission.status.in_(['pending', 'approved']))
    
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    last_form = query.order_by(DailyFormSubmission.created_at.desc()).first()
    
    if not last_form:
        return jsonify({'success': False, 'message': 'no_previous_form'}), 404
    
    # Build the response with all form data
    form_data = {
        'success': True,
        'form_date': last_form.form_date.isoformat() if last_form.form_date else None,
        'day_of_week': last_form.day_of_week,
        'work_shift': last_form.work_shift,
        'project_id': last_form.project_id,
        
        # Climate
        'climate': None,
        
        # Human Resources
        'human_resources': [],
        
        # Tools and Equipment
        'tools_equipment': [],
        
        # Construction Operations
        'operations': [],
        
        # Incoming Materials
        'materials': [],
        
        # Project Issues
        'issues': [],
        
        # Safety
        'safety': None,
        
        # Events
        'events': []
    }
    
    # Get climate data
    climate = last_form.climate_conditions.first()
    if climate:
        form_data['climate'] = {
            'min_temperature': climate.min_temperature,
            'max_temperature': climate.max_temperature,
            'humidity': climate.humidity,
            'weather_type': climate.weather_type,
            'wind_speed': climate.wind_speed,
            'climate_effect': climate.climate_effect
        }
    
    # Get human resources
    for hr in last_form.human_resources:
        form_data['human_resources'].append({
            'post': hr.post,
            'count': hr.count,
            'working_hours': hr.working_hours,
            'notes': hr.notes or ''
        })
    
    # Get tools and equipment
    for eq in last_form.tools_equipments:
        form_data['tools_equipment'].append({
            'equipment_name': eq.equipment_name,
            'count_active': eq.count_active,
            'working_hours': eq.working_hours,
            'situation': eq.situation,
            'inactivity_reason': eq.inactivity_reason or ''
        })
    
    # Get construction operations
    for op in last_form.construction_operations:
        form_data['operations'].append({
            'operation_type': op.operation_type,
            'start_km': op.start_km,
            'end_km': op.end_km,
            'unit': op.unit,
            'progress': op.progress,
            'map_number': op.map_number or ''
        })
    
    # Get incoming materials
    for mat in last_form.incoming_materials:
        form_data['materials'].append({
            'material_type': mat.material_type,
            'incoming_amount': mat.incoming_amount,
            'cumulative_incoming': mat.cumulative_incoming,
            'used_amount': mat.used_amount,
            'cumulative_used': mat.cumulative_used,
            'storage_place': mat.storage_place or '',
            'waybill_number': mat.waybill_number or ''
        })
    
    # Get project issues
    for issue in last_form.project_issues:
        form_data['issues'].append({
            'issue_type': issue.issue_type,
            'effect': issue.effect or '',
            'location_km': issue.location_km,
            'notes': issue.notes or ''
        })
    
    # Get safety data
    safety = last_form.safety_records.first()
    if safety:
        form_data['safety'] = {
            'safety_situation': safety.safety_situation,
            'safety_inspection': safety.safety_inspection,
            'incident_occurred': safety.incident_occurred,
            'incident_explanation': safety.incident_explanation or ''
        }
    
    # Get events
    for event in last_form.events:
        form_data['events'].append({
            'event_name': event.event_name,
            'explanation': event.explanation or ''
        })
    
    return jsonify(form_data)


@forms_bp.route('/<int:form_id>/documents/download')
@login_required
def download_form_documents(form_id):
    """Download the documents zip file for a form."""
    user = get_current_user()
    form = DailyFormSubmission.query.get_or_404(form_id)
    
    # Check permission
    if not can_view_form(form, user):
        lang = session.get('lang', 'en')
        t = lambda key: get_translation(key, lang)
        flash(t('access_denied'), 'danger')
        return redirect(url_for('forms.my_forms'))
    
    if not form.documents_path:
        lang = session.get('lang', 'en')
        t = lambda key: get_translation(key, lang)
        flash(t('no_documents_attached'), 'warning')
        return redirect(url_for('forms.view_form', form_id=form_id))
    
    full_path = get_documents_full_path(form.documents_path)
    
    if not full_path or not os.path.exists(full_path):
        lang = session.get('lang', 'en')
        t = lambda key: get_translation(key, lang)
        flash(t('documents_not_found'), 'danger')
        return redirect(url_for('forms.view_form', form_id=form_id))
    
    # Get filename for download
    download_name = f"{form.document_code}_documents.zip"
    
    return send_file(
        full_path,
        mimetype='application/zip',
        as_attachment=True,
        download_name=download_name
    )


@forms_bp.route('/<int:form_id>/documents/info')
@login_required
def form_documents_info(form_id):
    """API endpoint to get info about form documents."""
    user = get_current_user()
    form = DailyFormSubmission.query.get_or_404(form_id)
    
    # Check permission
    if not can_view_form(form, user):
        return jsonify({'success': False, 'message': 'access_denied'}), 403
    
    if not form.documents_path:
        return jsonify({
            'success': True,
            'has_documents': False,
            'files': [],
            'total_size': 0,
            'formatted_size': '0 B'
        })
    
    files_info = list_documents_in_zip(form.documents_path)
    zip_size = get_zip_file_size(form.documents_path)
    
    return jsonify({
        'success': True,
        'has_documents': True,
        'files': files_info,
        'file_count': len(files_info),
        'total_size': zip_size,
        'formatted_size': format_file_size(zip_size)
    })


@forms_bp.route('/<int:form_id>/documents/delete', methods=['POST'])
@login_required
def delete_documents(form_id):
    """Delete documents from a form."""
    user = get_current_user()
    form = DailyFormSubmission.query.get_or_404(form_id)
    
    # Check permission - only form owner or admin can delete
    db_user = User.query.filter_by(username=user['username']).first()
    if form.submitted_by != db_user.id and user['role'] != 'admin':
        return jsonify({'success': False, 'message': 'access_denied'}), 403
    
    # Can only delete documents from draft forms
    if form.status != 'draft':
        lang = session.get('lang', 'en')
        t = lambda key: get_translation(key, lang)
        return jsonify({'success': False, 'message': t('cannot_delete_documents')}), 400
    
    if form.documents_path:
        delete_form_documents(form.documents_path)
        form.documents_path = None
        
        # Also clear event document filenames since they were in the ZIP
        for event in form.events:
            event.document_filename = None
        
        db.session.commit()
    
    return jsonify({'success': True})


@forms_bp.route('/api/project-roadmap/<int:project_id>')
@login_required
def get_project_roadmap(project_id):
    """API endpoint to get all historical operations for a project's roadmap."""
    
    # Get all approved and pending forms for this project, ordered by date
    forms = DailyFormSubmission.query.filter_by(project_id=project_id)\
        .filter(DailyFormSubmission.status.in_(['approved', 'pending']))\
        .order_by(DailyFormSubmission.form_date.asc())\
        .all()
    
    if not forms:
        return jsonify({
            'success': True,
            'operations': [],
            'activities': {},
            'total_length': 0
        })
    
    # Collect all operations grouped by activity type
    activities = {}  # {activity_name: {segments: [], total_length: 0, unit: ''}}
    all_operations = []
    
    for form in forms:
        for op in form.construction_operations:
            if op.operation_type and op.start_station and op.end_station:
                start_meters = op.start_meters
                end_meters = op.end_meters
                
                if start_meters is not None and end_meters is not None and start_meters < end_meters:
                    segment = {
                        'start_station': op.start_station,
                        'end_station': op.end_station,
                        'start_meters': start_meters,
                        'end_meters': end_meters,
                        'length': end_meters - start_meters,
                        'amount': op.amount or 0,
                        'unit': op.unit or '',
                        'form_date': form.form_date.isoformat() if form.form_date else None
                    }
                    
                    all_operations.append({
                        'activity': op.operation_type,
                        **segment
                    })
                    
                    # Group by activity
                    if op.operation_type not in activities:
                        activities[op.operation_type] = {
                            'segments': [],
                            'total_length': 0,
                            'total_amount': 0,
                            'unit': op.unit or ''
                        }
                    
                    activities[op.operation_type]['segments'].append(segment)
                    activities[op.operation_type]['total_length'] += segment['length']
                    activities[op.operation_type]['total_amount'] += segment['amount']
    
    # Calculate overall totals
    total_length = sum(act['total_length'] for act in activities.values())
    
    return jsonify({
        'success': True,
        'operations': all_operations,
        'activities': activities,
        'total_length': total_length
    })

