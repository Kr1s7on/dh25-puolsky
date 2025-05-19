from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from . import notifications
from .. import db
from ..models.notification import Notification, NotificationStatus, NotificationType
from ..decorators import admin_required, caregiver_required
from .forms import NotificationFilterForm

@notifications.route('/')
@login_required
def index():
    """View all notifications for the current user."""
    form = NotificationFilterForm()
    
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    type_filter = request.args.get('type', 'all')
    
    # Base query - get notifications for current user
    query = Notification.query.filter_by(user_id=current_user.id)
    
    # Apply status filter if not 'all'
    if status_filter != 'all':
        status_enum = NotificationStatus[status_filter.upper()]
        query = query.filter_by(status=status_enum)
    
    # Apply type filter if not 'all'
    if type_filter != 'all':
        type_enum = NotificationType[type_filter.upper()]
        query = query.filter_by(type=type_enum)
    
    # Order by creation date, newest first
    notifications_list = query.order_by(Notification.created_at.desc()).all()
    
    return render_template('notifications/index.html', 
                          notifications=notifications_list,
                          form=form,
                          status_filter=status_filter,
                          type_filter=type_filter,
                          show_sidebar=True)

@notifications.route('/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark a notification as read."""
    notification = Notification.query.get_or_404(notification_id)
    
    # Verify notification belongs to current user
    if notification.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('notifications.index'))
    
    notification.mark_as_read()
    db.session.commit()
    
    flash('Notification marked as read.', 'success')
    return redirect(url_for('notifications.index'))

@notifications.route('/snooze/<int:notification_id>', methods=['POST'])
@login_required
def snooze(notification_id):
    """Snooze a notification for a specified time."""
    notification = Notification.query.get_or_404(notification_id)
    hours = int(request.form.get('hours', 1))
    
    # Verify notification belongs to current user
    if notification.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('notifications.index'))
    
    notification.snooze(hours=hours)
    db.session.commit()
    
    flash(f'Notification snoozed for {hours} hour(s).', 'success')
    return redirect(url_for('notifications.index'))

@notifications.route('/acknowledge/<int:notification_id>', methods=['POST'])
@login_required
def acknowledge(notification_id):
    """Acknowledge a notification."""
    notification = Notification.query.get_or_404(notification_id)
    
    # Verify notification belongs to current user
    if notification.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('notifications.index'))
    
    notification.acknowledge()
    db.session.commit()
    
    flash('Notification acknowledged.', 'success')
    return redirect(url_for('notifications.index'))
