"""
Notifications routes.
"""
from flask import Blueprint, render_template, request, session, jsonify, flash, redirect, url_for
from utils.auth import login_required, get_current_user
from models import db, User, Notification
from translations import get_translation

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/')
@login_required
def list_notifications():
    """List all notifications for the current user."""
    user = get_current_user()
    lang = session.get('lang', 'en')
    
    db_user = User.query.filter_by(username=user['username']).first()
    
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', 'all')  # all, unread, starred
    
    # Base query
    query = Notification.query.filter_by(user_id=db_user.id)
    
    # Apply filter
    if filter_type == 'unread':
        query = query.filter_by(is_read=False)
    elif filter_type == 'starred':
        query = query.filter_by(is_starred=True)
    
    notifications = query.order_by(
        Notification.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    # Get counts for tabs
    all_count = Notification.query.filter_by(user_id=db_user.id).count()
    unread_count = Notification.query.filter_by(user_id=db_user.id, is_read=False).count()
    starred_count = Notification.query.filter_by(user_id=db_user.id, is_starred=True).count()
    
    return render_template('notifications/list.html', 
                          notifications=notifications, 
                          lang=lang,
                          filter_type=filter_type,
                          all_count=all_count,
                          unread_count=unread_count,
                          starred_count=starred_count)


@notifications_bp.route('/count')
@login_required
def get_count():
    """Get unread notification count."""
    user = get_current_user()
    db_user = User.query.filter_by(username=user['username']).first()
    
    count = Notification.query.filter_by(user_id=db_user.id, is_read=False).count()
    
    return jsonify({'count': count})


@notifications_bp.route('/recent')
@login_required
def get_recent():
    """Get recent notifications for dropdown."""
    user = get_current_user()
    db_user = User.query.filter_by(username=user['username']).first()
    
    notifications = Notification.query.filter_by(user_id=db_user.id).order_by(
        Notification.created_at.desc()
    ).limit(10).all()
    
    return jsonify({
        'notifications': [n.to_dict() for n in notifications]
    })


@notifications_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark a notification as read."""
    user = get_current_user()
    db_user = User.query.filter_by(username=user['username']).first()
    
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=db_user.id
    ).first_or_404()
    
    notification.mark_as_read()
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    return redirect(url_for('notifications.list_notifications'))


@notifications_bp.route('/mark-unread/<int:notification_id>', methods=['POST'])
@login_required
def mark_unread(notification_id):
    """Mark a notification as unread."""
    user = get_current_user()
    db_user = User.query.filter_by(username=user['username']).first()
    
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=db_user.id
    ).first_or_404()
    
    notification.mark_as_unread()
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    return redirect(url_for('notifications.list_notifications'))


@notifications_bp.route('/toggle-star/<int:notification_id>', methods=['POST'])
@login_required
def toggle_star(notification_id):
    """Toggle star status of a notification."""
    user = get_current_user()
    db_user = User.query.filter_by(username=user['username']).first()
    
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=db_user.id
    ).first_or_404()
    
    notification.toggle_star()
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'is_starred': notification.is_starred})
    
    return redirect(url_for('notifications.list_notifications'))


@notifications_bp.route('/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Delete a notification."""
    user = get_current_user()
    db_user = User.query.filter_by(username=user['username']).first()
    
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=db_user.id
    ).first_or_404()
    
    db.session.delete(notification)
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    lang = session.get('lang', 'en')
    t = lambda key: get_translation(key, lang)
    flash(t('notification_deleted'), 'success')
    return redirect(url_for('notifications.list_notifications'))


@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read."""
    user = get_current_user()
    db_user = User.query.filter_by(username=user['username']).first()
    
    Notification.query.filter_by(
        user_id=db_user.id, 
        is_read=False
    ).update({'is_read': True})
    
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    lang = session.get('lang', 'en')
    t = lambda key: get_translation(key, lang)
    flash(t('all_notifications_read'), 'success')
    return redirect(url_for('notifications.list_notifications'))


@notifications_bp.route('/delete-all-read', methods=['POST'])
@login_required
def delete_all_read():
    """Delete all read notifications."""
    user = get_current_user()
    db_user = User.query.filter_by(username=user['username']).first()
    
    Notification.query.filter_by(
        user_id=db_user.id, 
        is_read=True
    ).delete()
    
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    lang = session.get('lang', 'en')
    t = lambda key: get_translation(key, lang)
    flash(t('all_read_notifications_deleted'), 'success')
    return redirect(url_for('notifications.list_notifications'))
