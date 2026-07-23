"""
Boss Dashboard Routes - Comprehensive Analysis Panel
======================================================

This module provides routes for the boss analysis dashboard with three tabs:
- Overview: Executive summary for presenting to project owners
- Summary: Aggregated metrics and trends
- Details: Detailed charts and data

All routes require boss authentication.
"""

from flask import Blueprint, render_template, request, session, jsonify
from datetime import datetime, timedelta
from utils.auth import boss_required
from models import db, Project, DailyFormSubmission
from Projects.project_configurations import load_project_config
from analysis import AnalysisEngine
from analysis.detailed_analysis import DetailedAnalysisEngine

boss_bp = Blueprint('boss', __name__, url_prefix='/boss')


def get_project_config(project_id):
    """Load project configuration by project ID."""
    project = Project.query.get(project_id)
    if not project:
        return {}
    
    # Try to get the project code from database
    project_code = getattr(project, 'project_code', None)
    if project_code:
        return load_project_config(project_code)
    
    # Fallback: Try Project_01, Project_02, etc.
    return load_project_config(f'Project_{str(project_id).zfill(2)}')


@boss_bp.route('/dashboard')
@boss_required
def dashboard():
    """Main boss dashboard with project selection."""
    lang = session.get('lang', 'en')
    projects = Project.query.filter_by(status='active').all()
    
    return render_template('boss/dashboard.html', 
                          lang=lang, 
                          projects=projects)


@boss_bp.route('/analysis/<int:project_id>')
@boss_required
def analysis(project_id):
    """Analysis dashboard for a specific project."""
    lang = session.get('lang', 'en')
    project = Project.query.get_or_404(project_id)
    
    # Load project config
    config = get_project_config(project_id)
    
    # Initialize analysis engine
    engine = AnalysisEngine(db, project_id, config)
    
    # Check data availability
    availability = engine.check_data_availability()
    
    return render_template('boss/analysis.html',
                          lang=lang,
                          project=project,
                          config=config,
                          has_data=availability['has_data'],
                          form_count=availability['form_count'])


# =============================================================================
# API Routes for Dashboard Data
# =============================================================================

@boss_bp.route('/api/<int:project_id>/availability')
@boss_required
def api_availability(project_id):
    """Check data availability for analysis."""
    lang = session.get('lang', 'en')
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config, lang)
    return jsonify(engine.check_data_availability())


@boss_bp.route('/api/<int:project_id>/overview')
@boss_required
def api_overview(project_id):
    """Get overview data for executive summary."""
    lang = session.get('lang', 'en')
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config, lang)
    
    # Check data availability first
    availability = engine.check_data_availability()
    if not availability['has_data']:
        msg = 'هنوز فرم روزانه‌ای ثبت نشده است.' if lang == 'fa' else 'No daily forms submitted yet. Add data to see analysis.'
        return jsonify({
            'success': False,
            'no_data': True,
            'error': msg,
            'form_count': 0
        })
    
    try:
        dashboard = engine.get_boss_dashboard()
        return jsonify({
            'success': True,
            'data': dashboard['overview']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@boss_bp.route('/api/<int:project_id>/summary')
@boss_required
def api_summary(project_id):
    """Get summary data with aggregated metrics."""
    lang = session.get('lang', 'en')
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config, lang)
    
    # Check data availability first
    availability = engine.check_data_availability()
    if not availability['has_data']:
        msg = 'هنوز فرم روزانه‌ای ثبت نشده است.' if lang == 'fa' else 'No daily forms submitted yet. Add data to see analysis.'
        return jsonify({
            'success': False,
            'no_data': True,
            'error': msg,
            'form_count': 0
        })
    
    try:
        dashboard = engine.get_boss_dashboard()
        return jsonify({
            'success': True,
            'data': dashboard['summary']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@boss_bp.route('/api/<int:project_id>/details')
@boss_required
def api_details(project_id):
    """Get detailed data for charts and plots."""
    lang = session.get('lang', 'en')
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config, lang)
    
    # Check data availability first
    availability = engine.check_data_availability()
    if not availability['has_data']:
        msg = 'هنوز فرم روزانه‌ای ثبت نشده است.' if lang == 'fa' else 'No daily forms submitted yet. Add data to see analysis.'
        return jsonify({
            'success': False,
            'no_data': True,
            'error': msg,
            'form_count': 0
        })
    
    try:
        dashboard = engine.get_boss_dashboard()
        return jsonify({
            'success': True,
            'data': dashboard['details']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@boss_bp.route('/api/<int:project_id>/full-report')
@boss_required
def api_full_report(project_id):
    """Get complete analysis report."""
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config)
    
    try:
        report = engine.get_full_report()
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# Individual Analysis API Routes
# =============================================================================

@boss_bp.route('/api/<int:project_id>/progress')
@boss_required
def api_progress(project_id):
    """Get physical progress analysis."""
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config)
    
    try:
        return jsonify({
            'success': True,
            'data': engine.physical_progress.get_summary()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@boss_bp.route('/api/<int:project_id>/financial')
@boss_required
def api_financial(project_id):
    """Get financial analysis."""
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config)
    
    try:
        return jsonify({
            'success': True,
            'data': engine.financial.get_summary()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@boss_bp.route('/api/<int:project_id>/resources')
@boss_required
def api_resources(project_id):
    """Get resource utilization analysis."""
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config)
    
    try:
        return jsonify({
            'success': True,
            'data': engine.resources.get_summary()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@boss_bp.route('/api/<int:project_id>/materials')
@boss_required
def api_materials(project_id):
    """Get material analysis."""
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config)
    
    try:
        return jsonify({
            'success': True,
            'data': engine.materials.get_summary()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@boss_bp.route('/api/<int:project_id>/schedule')
@boss_required
def api_schedule(project_id):
    """Get schedule analysis."""
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config)
    
    try:
        return jsonify({
            'success': True,
            'data': engine.schedule.get_summary()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@boss_bp.route('/api/<int:project_id>/safety')
@boss_required
def api_safety(project_id):
    """Get safety analysis."""
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config)
    
    try:
        return jsonify({
            'success': True,
            'data': engine.safety.get_summary()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@boss_bp.route('/api/<int:project_id>/issues')
@boss_required
def api_issues(project_id):
    """Get issues analysis."""
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config)
    
    try:
        return jsonify({
            'success': True,
            'data': engine.issues.get_summary()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@boss_bp.route('/api/<int:project_id>/kpi')
@boss_required
def api_kpi(project_id):
    """Get KPI analysis."""
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config)
    
    try:
        return jsonify({
            'success': True,
            'data': engine.kpi.get_summary()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@boss_bp.route('/api/<int:project_id>/comparative')
@boss_required
def api_comparative(project_id):
    """Get comparative analysis."""
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config)
    
    try:
        return jsonify({
            'success': True,
            'data': engine.comparative.get_summary()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# Plot Data API Routes
# =============================================================================

@boss_bp.route('/api/<int:project_id>/plot/<plot_type>')
@boss_required
def api_plot_data(project_id, plot_type):
    """Get data for a specific plot type."""
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config)
    
    try:
        data = engine.get_plot_data(plot_type)
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@boss_bp.route('/api/<int:project_id>/progress-trend')
@boss_required
def api_progress_trend(project_id):
    """Get progress trend data."""
    days = request.args.get('days', 30, type=int)
    interval = request.args.get('interval', 'daily')
    
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config)
    
    try:
        data = engine.physical_progress.get_progress_trend(days, interval)
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@boss_bp.route('/api/<int:project_id>/weekly-report')
@boss_required
def api_weekly_report(project_id):
    """Get weekly performance report."""
    weeks = request.args.get('weeks', 4, type=int)
    
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config)
    
    try:
        data = engine.comparative.get_weekly_report(weeks)
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@boss_bp.route('/api/<int:project_id>/monthly-comparison')
@boss_required
def api_monthly_comparison(project_id):
    """Get month-over-month comparison."""
    months = request.args.get('months', 6, type=int)
    
    config = get_project_config(project_id)
    engine = AnalysisEngine(db, project_id, config)
    
    try:
        data = engine.comparative.get_month_over_month(months)
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# Detailed Analysis Routes (40+ Individual Analyses)
# =============================================================================

@boss_bp.route('/detailed-analysis/<int:project_id>')
@boss_required
def detailed_analysis(project_id):
    """Detailed analysis page with all individual analyses."""
    lang = session.get('lang', 'en')
    project = Project.query.get_or_404(project_id)
    
    # Load project config
    config = get_project_config(project_id)
    
    # Initialize detailed analysis engine
    engine = DetailedAnalysisEngine(db, project_id, config, lang)
    
    # Get analysis categories
    categories = engine.get_analysis_categories()
    
    # Check data availability
    base_engine = AnalysisEngine(db, project_id, config, lang)
    availability = base_engine.check_data_availability()
    
    return render_template('boss/detailed_analysis.html',
                          lang=lang,
                          project=project,
                          categories=categories,
                          has_data=availability['has_data'],
                          form_count=availability['form_count'])


@boss_bp.route('/api/<int:project_id>/analysis-categories')
@boss_required
def api_analysis_categories(project_id):
    """Get all analysis categories and their analyses."""
    lang = session.get('lang', 'en')
    config = get_project_config(project_id)
    engine = DetailedAnalysisEngine(db, project_id, config, lang)
    
    return jsonify({
        'success': True,
        'data': engine.get_analysis_categories()
    })


@boss_bp.route('/api/<int:project_id>/detailed/<analysis_id>')
@boss_required
def api_detailed_analysis(project_id, analysis_id):
    """Get a specific detailed analysis by ID."""
    lang = session.get('lang', 'en')
    config = get_project_config(project_id)
    engine = DetailedAnalysisEngine(db, project_id, config, lang)
    
    try:
        result = engine.get_analysis(analysis_id)
        return jsonify({
            'success': result.get('success', False),
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
