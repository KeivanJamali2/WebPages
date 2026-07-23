"""
Boss Dashboard Routes
======================

Provides:
- Project selection dashboard
- Per‑project analysis page (placeholder — analysis to be rebuilt)
- API: data availability check
- API: raw data endpoint (returns all daily‑form data as JSON)

All routes require boss authentication.
"""

from flask import Blueprint, render_template, request, session, jsonify
from utils.auth import boss_required
from models import db, Project, User, DailyFormSubmission, Comment
from Projects.project_configurations import load_project_config
from analysis import AnalysisEngine, DataService
from analysis.analysis_activities_roadmap import ActivitiesRoadmapAnalysis
from analysis.analysis_human_resources import HumanResourcesAnalysis
from analysis.analysis_tools_equipment import ToolsEquipmentAnalysis
from analysis.analysis_materials import MaterialsAnalysis
from analysis.analysis_problems_safety import ProblemsAnalysis
from analysis.analysis_weather_climate import WeatherAnalysis

boss_bp = Blueprint('boss', __name__, url_prefix='/boss')


def get_project_config(project_id):
    """Load project configuration by project ID."""
    project = Project.query.get(project_id)
    if not project:
        return {}
    project_code = getattr(project, 'project_code', None)
    if project_code:
        try:
            return load_project_config(project_code)
        except FileNotFoundError:
            return {}
    return {}


# =========================================================================
# Pages
# =========================================================================

@boss_bp.route('/dashboard')
@boss_required
def dashboard():
    """Main boss dashboard — project selection."""
    lang = session.get('lang', 'en')
    projects = Project.query.filter_by(status='active').all()
    return render_template('boss/dashboard.html', lang=lang, projects=projects)


@boss_bp.route('/analysis/<int:project_id>')
@boss_required
def analysis(project_id):
    """Analysis page for a specific project."""
    lang = session.get('lang', 'en')
    project = Project.query.get_or_404(project_id)
    config = get_project_config(project_id)

    engine = AnalysisEngine(db, project_id, config)
    availability = engine.check_data_availability()

    return render_template('boss/analysis.html',
                           lang=lang,
                           project=project,
                           config=config,
                           has_data=availability['has_data'],
                           form_count=availability['form_count'])


# =========================================================================
# API Routes
# =========================================================================

@boss_bp.route('/api/<int:project_id>/availability')
@boss_required
def api_availability(project_id):
    """Check data availability for analysis."""
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config)
    return jsonify(engine.check_data_availability())


@boss_bp.route('/api/<int:project_id>/raw-data')
@boss_required
def api_raw_data(project_id):
    """
    Return ALL daily‑form data for a project as JSON.

    Query params (all optional):
        status    — form status filter (default: approved)
        from_date — start date (YYYY-MM-DD)
        to_date   — end date (YYYY-MM-DD)
        section   — return only one section:
                     forms, human_resources, tools_equipment,
                     construction_operations, incoming_materials,
                     climate_conditions, project_issues,
                     safety_records, events

    Examples:
        /boss/api/1/raw-data
        /boss/api/1/raw-data?section=human_resources
        /boss/api/1/raw-data?from_date=2025-01-01&to_date=2025-12-31
    """
    from datetime import date as _date

    status = request.args.get('status', 'approved')
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')
    section = request.args.get('section')

    from_date = _date.fromisoformat(from_date_str) if from_date_str else None
    to_date = _date.fromisoformat(to_date_str) if to_date_str else None

    ds = DataService(db, project_id, status=status,
                     from_date=from_date, to_date=to_date)

    if section:
        getter = getattr(ds, f'get_{section}', None)
        if getter is None:
            return jsonify({'success': False,
                            'error': f'Unknown section: {section}'}), 400
        return jsonify({'success': True, 'data': getter()})

    return jsonify({'success': True, 'data': ds.get_all_data()})


@boss_bp.route('/api/<int:project_id>/summary-counts')
@boss_required
def api_summary_counts(project_id):
    """Quick record counts per section."""
    ds = DataService(db, project_id)
    return jsonify({'success': True, 'data': ds.get_summary_counts()})


# =========================================================================
# Activities & Roadmap Analysis — API
# =========================================================================

@boss_bp.route('/api/convert-date', methods=['POST'])
@boss_required
def api_convert_date():
    """
    Convert Jalali (Persian) date to Gregorian ISO format.
    
    POST data (JSON):
        jy (int): Jalali year
        jm (int): Jalali month
        jd (int): Jalali day
    
    Returns: {"success": true, "gregorian": "YYYY-MM-DD"}
    """
    import jdatetime
    
    try:
        data = request.get_json()
        jy = int(data.get('jy'))
        jm = int(data.get('jm'))
        jd = int(data.get('jd'))
        
        # Convert using jdatetime (verified working)
        j = jdatetime.date(jy, jm, jd)
        gregorian = j.togregorian().isoformat()
        
        return jsonify({'success': True, 'gregorian': gregorian})
    except (ValueError, TypeError, KeyError) as e:
        return jsonify({'success': False, 'error': f'Invalid date: {e}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@boss_bp.route('/api/<int:project_id>/activities')
@boss_required
def api_activities(project_id):
    """
    Return all activities analysis data as JSON.

    Query params:
        unit      — per_day | per_week | per_month | per_hour (default: per_day)
        from_date — YYYY-MM-DD
        to_date   — YYYY-MM-DD
    """
    from datetime import date as _date

    unit = request.args.get('unit', 'per_day')
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')

    try:
        from_date = _date.fromisoformat(from_date_str) if from_date_str else None
        to_date = _date.fromisoformat(to_date_str) if to_date_str else None
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'error': f'Invalid date format: {e}'}), 400

    try:
        config = get_project_config(project_id)
        ds = DataService(db, project_id, status='approved',
                         from_date=from_date, to_date=to_date)
        analyzer = ActivitiesRoadmapAnalysis(ds, config)
        return jsonify({'success': True, 'data': analyzer.get_all(unit)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =========================================================================
# Human Resources Analysis — API
# =========================================================================

@boss_bp.route('/api/<int:project_id>/human-resources')
@boss_required
def api_human_resources(project_id):
    """
    Return all human resources analysis data as JSON.

    Query params:
        unit      — per_day | per_week | per_month | per_hour (default: per_day)
        from_date — YYYY-MM-DD
        to_date   — YYYY-MM-DD
    """
    from datetime import date as _date

    unit = request.args.get('unit', 'per_day')
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')

    try:
        from_date = _date.fromisoformat(from_date_str) if from_date_str else None
        to_date = _date.fromisoformat(to_date_str) if to_date_str else None
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'error': f'Invalid date format: {e}'}), 400

    try:
        config = get_project_config(project_id)
        ds = DataService(db, project_id, status='approved',
                         from_date=from_date, to_date=to_date)
        analyzer = HumanResourcesAnalysis(ds, config)
        return jsonify({'success': True, 'data': analyzer.get_all(unit)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =========================================================================
# Tools & Equipment Analysis — API
# =========================================================================

@boss_bp.route('/api/<int:project_id>/tools-equipment')
@boss_required
def api_tools_equipment(project_id):
    """Return tools & equipment analysis data as JSON."""
    from datetime import date as _date

    unit = request.args.get('unit', 'per_day')
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')

    try:
        from_date = _date.fromisoformat(from_date_str) if from_date_str else None
        to_date = _date.fromisoformat(to_date_str) if to_date_str else None
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'error': f'Invalid date format: {e}'}), 400

    try:
        config = get_project_config(project_id)
        ds = DataService(db, project_id, status='approved',
                         from_date=from_date, to_date=to_date)
        analyzer = ToolsEquipmentAnalysis(ds, config)
        return jsonify({'success': True, 'data': analyzer.get_all(unit)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =========================================================================
# Materials & Resources Analysis — API
# =========================================================================

@boss_bp.route('/api/<int:project_id>/materials')
@boss_required
def api_materials(project_id):
    """Return materials analysis data as JSON."""
    from datetime import date as _date

    unit = request.args.get('unit', 'per_day')
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')

    try:
        from_date = _date.fromisoformat(from_date_str) if from_date_str else None
        to_date = _date.fromisoformat(to_date_str) if to_date_str else None
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'error': f'Invalid date format: {e}'}), 400

    try:
        config = get_project_config(project_id)
        ds = DataService(db, project_id, status='approved',
                         from_date=from_date, to_date=to_date)
        analyzer = MaterialsAnalysis(ds, config)
        return jsonify({'success': True, 'data': analyzer.get_all(unit)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =========================================================================
# Problems & Safety Analysis — API
# =========================================================================

@boss_bp.route('/api/<int:project_id>/problems-safety')
@boss_required
def api_problems_safety(project_id):
    """Return problems & safety analysis data as JSON."""
    from datetime import date as _date

    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')

    try:
        from_date = _date.fromisoformat(from_date_str) if from_date_str else None
        to_date = _date.fromisoformat(to_date_str) if to_date_str else None
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'error': f'Invalid date format: {e}'}), 400

    try:
        config = get_project_config(project_id)
        ds = DataService(db, project_id, status='approved',
                         from_date=from_date, to_date=to_date)
        analyzer = ProblemsAnalysis(ds, config)
        return jsonify({'success': True, 'data': analyzer.get_all()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =========================================================================
# Weather & Climate Analysis — API
# =========================================================================

@boss_bp.route('/api/<int:project_id>/weather')
@boss_required
def api_weather(project_id):
    """Return weather & climate analysis data as JSON."""
    from datetime import date as _date

    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')

    try:
        from_date = _date.fromisoformat(from_date_str) if from_date_str else None
        to_date = _date.fromisoformat(to_date_str) if to_date_str else None
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'error': f'Invalid date format: {e}'}), 400

    try:
        config = get_project_config(project_id)
        ds = DataService(db, project_id, status='approved',
                         from_date=from_date, to_date=to_date)
        analyzer = WeatherAnalysis(ds, config)
        return jsonify({'success': True, 'data': analyzer.get_all()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =========================================================================
# Employee Performance — API
# =========================================================================

@boss_bp.route('/api/<int:project_id>/employees')
@boss_required
def api_employees(project_id):
    """Return list of employees who have submitted forms for this project."""
    lang = session.get('lang', 'en')
    
    employees = (
        db.session.query(User)
        .join(DailyFormSubmission, DailyFormSubmission.submitted_by == User.id)
        .filter(DailyFormSubmission.project_id == project_id)
        .distinct()
        .all()
    )
    
    result = []
    for emp in employees:
        result.append({
            'id': emp.id,
            'username': emp.username,
            'display_name': emp.get_display_name(lang),
        })
    
    return jsonify({'success': True, 'employees': result})


@boss_bp.route('/api/<int:project_id>/employee-performance/<int:employee_id>')
@boss_required
def api_employee_performance(project_id, employee_id):
    """
    Return detailed performance data for a specific employee on a project.
    
    Returns:
    - stats: overall counts (approved, pending, draft, total, rejection_count)
    - forms: list of forms with status, dates, review info, comments
    - monthly: monthly submission breakdown for charting
    """
    import jdatetime
    lang = session.get('lang', 'en')
    
    # Get all forms by this employee for this project
    forms = (
        DailyFormSubmission.query
        .filter_by(project_id=project_id, submitted_by=employee_id)
        .order_by(DailyFormSubmission.form_date.desc())
        .all()
    )
    
    # Get all rejection comments for these forms
    form_ids = [f.id for f in forms]
    rejection_comments = (
        Comment.query
        .filter(Comment.daily_form_id.in_(form_ids))
        .filter_by(comment_type='rejection')
        .order_by(Comment.created_at.desc())
        .all()
    ) if form_ids else []
    
    # Group comments by form_id
    comments_by_form = {}
    for c in rejection_comments:
        if c.daily_form_id not in comments_by_form:
            comments_by_form[c.daily_form_id] = []
        comments_by_form[c.daily_form_id].append({
            'id': c.id,
            'content': c.content,
            'username': c.user.get_display_name(lang) if c.user else '?',
            'created_at': c.created_at.isoformat() if c.created_at else None,
            'comment_type': c.comment_type,
        })
    
    # Stats
    approved = sum(1 for f in forms if f.status == 'approved')
    pending = sum(1 for f in forms if f.status == 'pending')
    draft = sum(1 for f in forms if f.status == 'draft')
    total = len(forms)
    total_rejections = len(rejection_comments)
    approval_rate = round(approved / total * 100, 1) if total > 0 else 0
    
    # Monthly breakdown (Jalali months)
    monthly = {}
    for f in forms:
        if f.form_date:
            try:
                jd = jdatetime.date.fromgregorian(date=f.form_date)
                month_key = f'{jd.year}/{jd.month:02d}'
            except Exception:
                month_key = f.form_date.strftime('%Y/%m')
        else:
            month_key = 'unknown'
        
        if month_key not in monthly:
            monthly[month_key] = {'approved': 0, 'pending': 0, 'draft': 0, 'rejected': 0}
        
        monthly[month_key][f.status] = monthly[month_key].get(f.status, 0) + 1
        
        # Count rejections for this form (returned then re-submitted)
        if f.id in comments_by_form:
            monthly[month_key]['rejected'] += len(comments_by_form[f.id])
    
    monthly_sorted = [
        {'month': k, **v}
        for k, v in sorted(monthly.items())
    ]
    
    # Build form details
    form_list = []
    for f in forms:
        # Convert dates to Jalali for display
        form_date_j = None
        submitted_at_j = None
        reviewed_at_j = None
        
        if f.form_date:
            try:
                jd = jdatetime.date.fromgregorian(date=f.form_date)
                form_date_j = f'{jd.year}/{jd.month:02d}/{jd.day:02d}'
            except Exception:
                form_date_j = str(f.form_date)
        
        if f.submitted_at:
            try:
                jdt = jdatetime.datetime.fromgregorian(datetime=f.submitted_at)
                submitted_at_j = f'{jdt.year}/{jdt.month:02d}/{jdt.day:02d} {jdt.hour:02d}:{jdt.minute:02d}'
            except Exception:
                submitted_at_j = str(f.submitted_at)
        
        if f.reviewed_at:
            try:
                jdt = jdatetime.datetime.fromgregorian(datetime=f.reviewed_at)
                reviewed_at_j = f'{jdt.year}/{jdt.month:02d}/{jdt.day:02d} {jdt.hour:02d}:{jdt.minute:02d}'
            except Exception:
                reviewed_at_j = str(f.reviewed_at)
        
        reviewer_name = None
        if f.reviewer:
            reviewer_name = f.reviewer.get_display_name(lang)
        
        form_list.append({
            'id': f.id,
            'document_code': f.document_code,
            'form_date': form_date_j,
            'status': f.status,
            'submitted_at': submitted_at_j,
            'reviewed_at': reviewed_at_j,
            'reviewer': reviewer_name,
            'review_comment': f.review_comment,
            'rejection_count': len(comments_by_form.get(f.id, [])),
            'comments': comments_by_form.get(f.id, []),
        })
    
    return jsonify({
        'success': True,
        'data': {
            'stats': {
                'approved': approved,
                'pending': pending,
                'draft': draft,
                'total': total,
                'rejection_count': total_rejections,
                'approval_rate': approval_rate,
            },
            'forms': form_list,
            'monthly': monthly_sorted,
        }
    })
