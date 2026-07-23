"""
Forms Routes

Handles form listing, display, submission, and validation.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from utils.decorators import require_login
from utils.i18n import translate as _, get_locale
from forms.registry import get_registry
from models.form_submission import create_submission
from models.project import get_all_projects
from datetime import datetime

# Create blueprint
forms_bp = Blueprint('forms', __name__, url_prefix='/forms')


@forms_bp.route('/')
@require_login
def form_list():
    """
    Display list of available forms.
    """
    user_role = session.get('user_role', 'employee')
    locale = get_locale()
    
    # Get form registry
    registry = get_registry()
    
    # Get forms accessible to user's role
    forms = registry.get_form_list(user_role=user_role, locale=locale)
    
    return render_template(
        'forms/form_list.html',
        forms=forms,
        total_forms=len(forms)
    )


@forms_bp.route('/<form_id>')
@require_login
def show_form(form_id):
    """
    Display a specific form.
    
    Args:
        form_id: Form identifier
    """
    user_role = session.get('user_role', 'employee')
    locale = get_locale()
    
    # Get form registry
    registry = get_registry()
    
    # Get form instance
    form = registry.create_form_instance(form_id)
    
    if not form:
        flash(_('messages.form_not_found'), 'danger')
        return redirect(url_for('forms.form_list'))
    
    # Check access permission
    if not form.can_access(user_role):
        flash(_('messages.form_access_denied'), 'danger')
        return redirect(url_for('forms.form_list'))
    
    # Get form data for display
    form_data = form.to_dict(locale)
    
    # Get projects if form requires project selection
    projects = []
    if form.requires_project:
        db = current_app.config['db']
        all_projects = get_all_projects(db)
        
        # Filter active projects
        projects = [
            {
                'project_id': p.project_id,
                'name': p.name,
                'status': p.status
            }
            for p in all_projects
            if p.status == 'active'
        ]
    
    return render_template(
        'forms/dynamic_form.html',
        form=form_data,
        projects=projects,
        locale=locale
    )


@forms_bp.route('/<form_id>/submit', methods=['POST'])
@require_login
def submit_form(form_id):
    """
    Handle form submission.
    
    Args:
        form_id: Form identifier
    """
    user_id = session.get('user_id')
    user_role = session.get('user_role', 'employee')
    locale = get_locale()
    
    # Get form registry
    registry = get_registry()
    
    # Get form instance
    form = registry.create_form_instance(form_id)
    
    if not form:
        flash(_('messages.form_not_found'), 'danger')
        return redirect(url_for('forms.form_list'))
    
    # Check access permission
    if not form.can_access(user_role):
        flash(_('messages.form_access_denied'), 'danger')
        return redirect(url_for('forms.form_list'))
    
    # Get form data
    form_data = {}
    for field in form.fields:
        field_name = field['name']
        field_type = field['type']
        
        if field_type == 'checkbox':
            # Checkbox returns value only if checked
            form_data[field_name] = field_name in request.form
        elif field_type == 'file':
            # Handle file uploads
            files = request.files.getlist(field_name)
            if files:
                # In a real application, save files and store paths
                form_data[field_name] = [f.filename for f in files if f.filename]
            else:
                form_data[field_name] = []
        else:
            # Regular fields
            form_data[field_name] = request.form.get(field_name, '').strip()
    
    # Get project ID if required
    project_id = None
    if form.requires_project:
        project_id = request.form.get('project_id', '').strip()
        
        if not project_id:
            flash(_('messages.project_required'), 'danger')
            return redirect(url_for('forms.show_form', form_id=form_id))
    
    # Validate submission
    is_valid, errors = form.validate_submission(form_data)
    
    if not is_valid:
        # Show validation errors
        for error in errors:
            flash(error, 'danger')
        
        return redirect(url_for('forms.show_form', form_id=form_id))
    
    # Process submission (custom logic)
    try:
        processed_data = form.process_submission(form_data, user_id, project_id)
    except Exception as e:
        flash(f"Error processing form: {str(e)}", 'danger')
        return redirect(url_for('forms.show_form', form_id=form_id))
    
    # Save to database
    db = current_app.config['db']
    
    try:
        submission = create_submission(
            db=db,
            user_id=user_id,
            project_id=project_id,
            form_type=form_id,
            data=processed_data
        )
        
        if submission:
            flash(_('messages.form_submitted_success'), 'success')
            return redirect(url_for('dashboard.home'))
        else:
            flash(_('messages.form_submit_failed'), 'danger')
            return redirect(url_for('forms.show_form', form_id=form_id))
    
    except Exception as e:
        flash(f"Error saving form: {str(e)}", 'danger')
        return redirect(url_for('forms.show_form', form_id=form_id))


@forms_bp.route('/my-submissions')
@require_login
def my_submissions():
    """
    Display user's form submissions.
    """
    user_id = session.get('user_id')
    db = current_app.config['db']
    
    # Get user's submissions
    from models.form_submission import get_user_submissions
    submissions = get_user_submissions(db, user_id)
    
    return render_template(
        'forms/my_submissions.html',
        submissions=submissions
    )
