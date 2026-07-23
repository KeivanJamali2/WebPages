"""
Projects routes - project management (boss only).
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
from utils.auth import login_required, boss_required, get_current_user
from models import db, Project
from translations import get_translation
from utils.jalali import jalali_to_gregorian, parse_jalali_date

projects_bp = Blueprint('projects', __name__)


@projects_bp.route('/')
@boss_required
def list_projects():
    """List all projects."""
    lang = session.get('lang', 'en')
    
    page = request.args.get('page', 1, type=int)
    active_only = request.args.get('active', 'true') == 'true'
    
    query = Project.query
    if active_only:
        query = query.filter_by(is_active=True)
    
    projects = query.order_by(Project.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('projects/list.html', projects=projects, lang=lang, active_only=active_only)


@projects_bp.route('/new', methods=['GET', 'POST'])
@boss_required
def new_project():
    """Create a new project."""
    lang = session.get('lang', 'en')
    
    if request.method == 'POST':
        project_code = request.form.get('project_code', '').strip()
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        contract_number = request.form.get('contract_number', '').strip()
        start_date_str = request.form.get('start_date', '')
        end_date_str = request.form.get('end_date', '')
        is_ongoing = 'is_ongoing' in request.form
        budget = request.form.get('budget', type=float)
        owner = request.form.get('owner', '').strip()
        manager = request.form.get('manager', '').strip()
        description = request.form.get('description', '').strip()
        
        # Validate
        if not project_code or not name:
            t = lambda key: get_translation(key, lang)
            flash(t('project_code_name_required'), 'danger')
            return render_template('projects/form.html', lang=lang, project=None, mode='new')
        
        # Check if project code exists
        if Project.query.filter_by(project_code=project_code).first():
            t = lambda key: get_translation(key, lang)
            flash(t('project_code_exists'), 'danger')
            return render_template('projects/form.html', lang=lang, project=None, mode='new')
        
        # Parse Jalali dates and convert to Gregorian
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                j_date = parse_jalali_date(start_date_str)
                start_date = jalali_to_gregorian(j_date)
            except:
                pass
        
        if end_date_str and not is_ongoing:
            try:
                j_date = parse_jalali_date(end_date_str)
                end_date = jalali_to_gregorian(j_date)
            except:
                pass
        
        project = Project(
            project_code=project_code,
            name=name,
            location=location,
            contract_number=contract_number,
            start_date=start_date,
            end_date=end_date,
            is_ongoing=is_ongoing,
            budget=budget,
            owner=owner,
            manager=manager,
            description=description
        )
        
        db.session.add(project)
        db.session.commit()
        
        # Update project_configuration.py
        update_project_config(project)
        
        t = lambda key: get_translation(key, lang)
        flash(t('project_created'), 'success')
        return redirect(url_for('projects.view_project', project_id=project.id))
    
    return render_template('projects/form.html', lang=lang, project=None, mode='new')


@projects_bp.route('/<int:project_id>')
@boss_required
def view_project(project_id):
    """View project details."""
    lang = session.get('lang', 'en')
    
    project = Project.query.get_or_404(project_id)
    
    # Get project statistics
    from models import DailyFormSubmission
    stats = {
        'total_forms': project.daily_forms.count(),
        'approved_forms': project.daily_forms.filter_by(status='approved').count(),
        'pending_forms': project.daily_forms.filter_by(status='pending').count()
    }
    
    recent_forms = project.daily_forms.order_by(
        DailyFormSubmission.form_date.desc()
    ).limit(10).all()
    
    return render_template('projects/view.html', project=project, stats=stats, 
                          recent_forms=recent_forms, lang=lang)


@projects_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@boss_required
def edit_project(project_id):
    """Edit a project."""
    lang = session.get('lang', 'en')
    
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        project.name = request.form.get('name', '').strip()
        project.location = request.form.get('location', '').strip()
        project.contract_number = request.form.get('contract_number', '').strip()
        project.is_ongoing = 'is_ongoing' in request.form
        project.budget = request.form.get('budget', type=float)
        project.owner = request.form.get('owner', '').strip()
        project.manager = request.form.get('manager', '').strip()
        project.description = request.form.get('description', '').strip()
        
        # Parse Jalali dates and convert to Gregorian
        start_date_str = request.form.get('start_date', '')
        end_date_str = request.form.get('end_date', '')
        
        if start_date_str:
            try:
                j_date = parse_jalali_date(start_date_str)
                project.start_date = jalali_to_gregorian(j_date)
            except:
                pass
        
        if end_date_str and not project.is_ongoing:
            try:
                j_date = parse_jalali_date(end_date_str)
                project.end_date = jalali_to_gregorian(j_date)
            except:
                pass
        elif project.is_ongoing:
            project.end_date = None
        
        db.session.commit()
        
        # Update project_configuration.py
        update_project_config(project)
        
        t = lambda key: get_translation(key, lang)
        flash(t('project_updated'), 'success')
        return redirect(url_for('projects.view_project', project_id=project.id))
    
    return render_template('projects/form.html', lang=lang, project=project, mode='edit')


@projects_bp.route('/<int:project_id>/toggle-active', methods=['POST'])
@boss_required
def toggle_project_active(project_id):
    """Toggle project active status."""
    project = Project.query.get_or_404(project_id)
    project.is_active = not project.is_active
    db.session.commit()
    
    status = 'activated' if project.is_active else 'deactivated'
    flash(f'Project {status}.', 'success')
    
    return redirect(url_for('projects.list_projects'))


def update_project_config(project):
    """Update the project_configuration.py file."""
    import os
    from flask import current_app
    
    config_path = os.path.join(current_app.config['BASE_DIR'], 'Projects', 'project_configuration.py')
    
    # Read existing configuration
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        content = "projects = {\n}\n"
    
    # This is a simplified approach - in production you'd want proper Python AST manipulation
    # For now, we'll regenerate the entire file
    all_projects = Project.query.all()
    
    lines = ["projects = {"]
    for p in all_projects:
        end_date_str = p.end_date.strftime('%Y-%m-%d') if p.end_date else 'On-Going'
        start_date_str = p.start_date.strftime('%Y-%m-%d') if p.start_date else ''
        
        lines.append(f'    "{p.project_code}": {{')
        lines.append(f'        "name": "{p.name}",')
        lines.append(f'        "location": "{p.location or ""}",')
        lines.append(f'        "contract_number": "{p.contract_number or ""}",')
        lines.append(f'        "start_date": "{start_date_str}",')
        lines.append(f'        "end_date": "{end_date_str}",')
        lines.append(f'        "budget": {p.budget or 0},')
        lines.append(f'        "Owner": "{p.owner or ""}",')
        lines.append(f'        "manager": "{p.manager or ""}"')
        lines.append('    },')
    
    lines.append("}")
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
