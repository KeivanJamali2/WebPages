"""
Analytics routes - data analysis and charts (boss only).
"""
from flask import Blueprint, render_template, request, session, jsonify
from datetime import datetime, timedelta, date
from utils.auth import login_required, boss_required, get_current_user
from models import db, User, Project, DailyFormSubmission
from models import HumanResource, ToolEquipment, ConstructionOperation, Safety
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/')
@boss_required
def index():
    """Main analytics dashboard."""
    lang = session.get('lang', 'en')
    
    projects = Project.query.filter_by(status='active').all()
    employees = User.query.filter_by(role='employee').all()
    
    return render_template('analytics/dashboard.html', lang=lang, 
                          projects=projects, employees=employees)


@analytics_bp.route('/api/overview')
@boss_required
def api_overview():
    """Get overview statistics."""
    # Date filters
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    project_id = request.args.get('project_id', type=int)
    
    query = DailyFormSubmission.query.filter_by(status='approved')
    
    if from_date:
        query = query.filter(DailyFormSubmission.form_date >= from_date)
    if to_date:
        query = query.filter(DailyFormSubmission.form_date <= to_date)
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    total_forms = query.count()
    
    # Get unique dates for average calculation
    dates = db.session.query(
        func.count(func.distinct(DailyFormSubmission.form_date))
    ).filter(DailyFormSubmission.status == 'approved').scalar()
    
    return jsonify({
        'total_forms': total_forms,
        'total_days': dates or 1,
        'avg_forms_per_day': round(total_forms / (dates or 1), 2)
    })


@analytics_bp.route('/api/forms-by-date')
@boss_required
def api_forms_by_date():
    """Get forms count grouped by date."""
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    project_id = request.args.get('project_id', type=int)
    
    # Default to last 30 days
    if not from_date:
        from_date = (date.today() - timedelta(days=30)).isoformat()
    if not to_date:
        to_date = date.today().isoformat()
    
    query = db.session.query(
        DailyFormSubmission.form_date,
        func.count(DailyFormSubmission.id)
    ).filter(
        DailyFormSubmission.status == 'approved',
        DailyFormSubmission.form_date >= from_date,
        DailyFormSubmission.form_date <= to_date
    )
    
    if project_id:
        query = query.filter(DailyFormSubmission.project_id == project_id)
    
    results = query.group_by(DailyFormSubmission.form_date).order_by(
        DailyFormSubmission.form_date
    ).all()
    
    labels = [r[0].isoformat() for r in results]
    data = [r[1] for r in results]
    
    return jsonify({'labels': labels, 'data': data})


@analytics_bp.route('/api/forms-by-project')
@boss_required
def api_forms_by_project():
    """Get forms count grouped by project."""
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    query = db.session.query(
        Project.name,
        func.count(DailyFormSubmission.id)
    ).join(DailyFormSubmission).filter(
        DailyFormSubmission.status == 'approved'
    )
    
    if from_date:
        query = query.filter(DailyFormSubmission.form_date >= from_date)
    if to_date:
        query = query.filter(DailyFormSubmission.form_date <= to_date)
    
    results = query.group_by(Project.id, Project.name).all()
    
    labels = [r[0] for r in results]
    data = [r[1] for r in results]
    
    return jsonify({'labels': labels, 'data': data})


@analytics_bp.route('/api/forms-by-employee')
@boss_required
def api_forms_by_employee():
    """Get forms count grouped by employee."""
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    project_id = request.args.get('project_id', type=int)
    
    query = db.session.query(
        User.username,
        func.count(DailyFormSubmission.id)
    ).join(DailyFormSubmission, User.id == DailyFormSubmission.submitted_by).filter(
        DailyFormSubmission.status == 'approved'
    )
    
    if from_date:
        query = query.filter(DailyFormSubmission.form_date >= from_date)
    if to_date:
        query = query.filter(DailyFormSubmission.form_date <= to_date)
    if project_id:
        query = query.filter(DailyFormSubmission.project_id == project_id)
    
    results = query.group_by(User.id, User.username).all()
    
    labels = [r[0] for r in results]
    data = [r[1] for r in results]
    
    return jsonify({'labels': labels, 'data': data})


@analytics_bp.route('/api/equipment-hours')
@boss_required
def api_equipment_hours():
    """Get total equipment working hours."""
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    project_id = request.args.get('project_id', type=int)
    
    query = db.session.query(
        ToolEquipment.equipment_name,
        func.sum(ToolEquipment.working_hours)
    ).join(DailyFormSubmission).filter(
        DailyFormSubmission.status == 'approved'
    )
    
    if from_date:
        query = query.filter(DailyFormSubmission.form_date >= from_date)
    if to_date:
        query = query.filter(DailyFormSubmission.form_date <= to_date)
    if project_id:
        query = query.filter(DailyFormSubmission.project_id == project_id)
    
    results = query.group_by(ToolEquipment.equipment_name).order_by(
        func.sum(ToolEquipment.working_hours).desc()
    ).limit(15).all()
    
    labels = [r[0] for r in results]
    data = [float(r[1] or 0) for r in results]
    
    return jsonify({'labels': labels, 'data': data})


@analytics_bp.route('/api/human-resources')
@boss_required
def api_human_resources():
    """Get human resources summary."""
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    project_id = request.args.get('project_id', type=int)
    
    query = db.session.query(
        HumanResource.post,
        func.sum(HumanResource.present),
        func.sum(HumanResource.vacation)
    ).join(DailyFormSubmission).filter(
        DailyFormSubmission.status == 'approved'
    )
    
    if from_date:
        query = query.filter(DailyFormSubmission.form_date >= from_date)
    if to_date:
        query = query.filter(DailyFormSubmission.form_date <= to_date)
    if project_id:
        query = query.filter(DailyFormSubmission.project_id == project_id)
    
    results = query.group_by(HumanResource.post).order_by(
        func.sum(HumanResource.present).desc()
    ).limit(15).all()
    
    labels = [r[0] for r in results]
    present_data = [int(r[1] or 0) for r in results]
    vacation_data = [int(r[2] or 0) for r in results]
    
    return jsonify({
        'labels': labels, 
        'present': present_data,
        'vacation': vacation_data
    })


@analytics_bp.route('/api/safety-incidents')
@boss_required
def api_safety_incidents():
    """Get safety incidents summary."""
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    project_id = request.args.get('project_id', type=int)
    
    # Count incidents
    query = db.session.query(
        func.count(Safety.id)
    ).join(DailyFormSubmission).filter(
        DailyFormSubmission.status == 'approved',
        Safety.incident_occurred == True
    )
    
    if from_date:
        query = query.filter(DailyFormSubmission.form_date >= from_date)
    if to_date:
        query = query.filter(DailyFormSubmission.form_date <= to_date)
    if project_id:
        query = query.filter(DailyFormSubmission.project_id == project_id)
    
    incidents = query.scalar() or 0
    
    # Count inspections
    inspections_query = db.session.query(
        func.count(Safety.id)
    ).join(DailyFormSubmission).filter(
        DailyFormSubmission.status == 'approved',
        Safety.safety_inspection == True
    )
    
    if from_date:
        inspections_query = inspections_query.filter(DailyFormSubmission.form_date >= from_date)
    if to_date:
        inspections_query = inspections_query.filter(DailyFormSubmission.form_date <= to_date)
    if project_id:
        inspections_query = inspections_query.filter(DailyFormSubmission.project_id == project_id)
    
    inspections = inspections_query.scalar() or 0
    
    # Safety situation breakdown
    situation_query = db.session.query(
        Safety.safety_situation,
        func.count(Safety.id)
    ).join(DailyFormSubmission).filter(
        DailyFormSubmission.status == 'approved'
    )
    
    if from_date:
        situation_query = situation_query.filter(DailyFormSubmission.form_date >= from_date)
    if to_date:
        situation_query = situation_query.filter(DailyFormSubmission.form_date <= to_date)
    if project_id:
        situation_query = situation_query.filter(DailyFormSubmission.project_id == project_id)
    
    situations = situation_query.group_by(Safety.safety_situation).all()
    
    situation_labels = [s[0] or 'Unknown' for s in situations]
    situation_data = [s[1] for s in situations]
    
    return jsonify({
        'total_incidents': incidents,
        'total_inspections': inspections,
        'situation_labels': situation_labels,
        'situation_data': situation_data
    })


@analytics_bp.route('/api/progress-summary')
@boss_required
def api_progress_summary():
    """Get construction progress summary."""
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    project_id = request.args.get('project_id', type=int)
    
    query = db.session.query(
        ConstructionOperation.operation_type,
        func.sum(ConstructionOperation.progress),
        ConstructionOperation.unit
    ).join(DailyFormSubmission).filter(
        DailyFormSubmission.status == 'approved'
    )
    
    if from_date:
        query = query.filter(DailyFormSubmission.form_date >= from_date)
    if to_date:
        query = query.filter(DailyFormSubmission.form_date <= to_date)
    if project_id:
        query = query.filter(DailyFormSubmission.project_id == project_id)
    
    results = query.group_by(
        ConstructionOperation.operation_type,
        ConstructionOperation.unit
    ).order_by(func.sum(ConstructionOperation.progress).desc()).limit(10).all()
    
    data = [{
        'operation': r[0],
        'progress': float(r[1] or 0),
        'unit': r[2] or ''
    } for r in results]
    
    return jsonify({'data': data})
