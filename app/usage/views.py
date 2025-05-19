from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

from . import usage
from .. import db
from ..models import UsageLog, Resident, InventoryItem, UsageStatus
from ..models.notification import Notification, NotificationType
from ..models.user import User
from ..notifications.sms import send_sms_alert
from ..decorators import admin_required, caregiver_required
from .forms import UsageLogForm


@usage.route('/')
@login_required
def index():
    """View all usage logs."""
    # Get all residents the current user has access to
    if current_user.is_admin():
        residents = Resident.query.all()
    else:
        residents = current_user.residents.all()
    
    # Get the selected resident or default to the first one
    resident_id = request.args.get('resident_id', None, type=int)
    selected_resident = None
    
    if resident_id:
        selected_resident = Resident.query.get_or_404(resident_id)
        # Check if caregiver has access to this resident
        if not current_user.is_admin() and selected_resident not in current_user.residents.all():
            flash('You do not have access to this resident', 'error')
            return redirect(url_for('usage.index'))
    elif residents:
        selected_resident = residents[0]
    
    # Get usage logs for the selected resident
    usage_logs = []
    if selected_resident:
        usage_logs = UsageLog.query.filter_by(resident_id=selected_resident.id).order_by(UsageLog.timestamp.desc()).all()
    
    return render_template('usage/index.html', 
                           residents=residents, 
                           selected_resident=selected_resident, 
                           usage_logs=usage_logs,
                           show_sidebar=True)


@usage.route('/new', methods=['GET', 'POST'])
@login_required
@caregiver_required
def new_log():
    """Create a new usage log."""
    form = UsageLogForm()
    
    # If caregiver, limit resident choices to assigned residents
    if not current_user.is_admin():
        form.resident.query = current_user.residents
    
    # Handle resident_id from query parameter
    resident_id = request.args.get('resident_id', None, type=int)
    if resident_id:
        resident = Resident.query.get_or_404(resident_id)
        form.resident.data = resident
        
        # Filter inventory items for this resident
        form.inventory_item.query = InventoryItem.query.filter_by(resident_id=resident_id)
    
    if form.validate_on_submit():
        # Handle voice note upload
        voice_note_url = None
        if form.voice_note.data:
            filename = secure_filename(form.voice_note.data.filename)
            voice_note_path = os.path.join('app', 'static', 'voice_notes', filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(voice_note_path), exist_ok=True)
            
            form.voice_note.data.save(voice_note_path)
            voice_note_url = url_for('static', filename=f'voice_notes/{filename}')
        
        # Create usage log
        log = UsageLog(
            status=form.status.data,
            scheduled_time=form.scheduled_time.data,
            notes=form.notes.data,
            voice_note_url=voice_note_url,
            inventory_item_id=form.inventory_item.data.id,
            resident_id=form.resident.data.id,
            caregiver_id=current_user.id
        )
        
        # Update inventory quantity if medication was taken
        if form.status.data == UsageStatus.TAKEN:
            inventory_item = form.inventory_item.data
            # Decrease quantity by 1 unit (or other amount if configured)
            if inventory_item.quantity > 0:
                inventory_item.quantity -= 1
        
        db.session.add(log)
        db.session.commit()
        # Missed-dose notification logic
        if form.status.data == UsageStatus.MISSED:
            caregivers = User.query.filter(User.residents.any(id=form.resident.data.id), User.sms_opt_in==True, User.phone_number!=None).all()
            for caregiver in caregivers:
                notif = Notification(
                    type=NotificationType.MISSED_DOSE,
                    message=f"Missed dose: {form.inventory_item.data.name} for resident {form.resident.data.name} at {form.scheduled_time.data}",
                    user_id=caregiver.id,
                    resident_id=form.resident.data.id,
                    inventory_item_id=form.inventory_item.data.id
                )
                db.session.add(notif)
                try:
                    send_sms_alert(caregiver.phone_number, f"DoseDash: Missed dose alert for {form.inventory_item.data.name} (resident: {form.resident.data.name}) at {form.scheduled_time.data}")
                except Exception as e:
                    pass
            db.session.commit()
        # Overdue-dose notification logic (simple: if log is created >1hr after scheduled_time and not TAKEN)
        if form.status.data != UsageStatus.TAKEN and form.scheduled_time.data:
            try:
                scheduled_dt = datetime.combine(datetime.now().date(), datetime.strptime(form.scheduled_time.data, '%H:%M').time())
                if datetime.now() > scheduled_dt + timedelta(hours=1):
                    caregivers = User.query.filter(User.residents.any(id=form.resident.data.id), User.sms_opt_in==True, User.phone_number!=None).all()
                    for caregiver in caregivers:
                        notif = Notification(
                            type=NotificationType.OVERDUE_DOSE,
                            message=f"Overdue dose: {form.inventory_item.data.name} for resident {form.resident.data.name} (scheduled {form.scheduled_time.data})",
                            user_id=caregiver.id,
                            resident_id=form.resident.data.id,
                            inventory_item_id=form.inventory_item.data.id
                        )
                        db.session.add(notif)
                        try:
                            send_sms_alert(caregiver.phone_number, f"DoseDash: Overdue dose alert for {form.inventory_item.data.name} (resident: {form.resident.data.name}) scheduled {form.scheduled_time.data}")
                        except Exception as e:
                            pass
                    db.session.commit()
            except Exception:
                pass
        flash('Usage log created successfully', 'success')
        
        # Redirect back to the usage log for this resident
        return redirect(url_for('usage.index', resident_id=form.resident.data.id))
    
    return render_template('usage/new.html', form=form)


@usage.route('/<int:log_id>')
@login_required
def view_log(log_id):
    """View a specific usage log."""
    log = UsageLog.query.get_or_404(log_id)
    
    # Check if user has access to this resident
    if not current_user.is_admin() and log.resident not in current_user.residents.all():
        flash('You do not have access to this log', 'error')
        return redirect(url_for('usage.index'))
    
    return render_template('usage/view.html', log=log)


@usage.route('/<int:log_id>/delete')
@login_required
@caregiver_required
def delete_log(log_id):
    """Delete a usage log."""
    log = UsageLog.query.get_or_404(log_id)
    
    # Check if user has access to this resident
    if not current_user.is_admin() and log.resident not in current_user.residents.all():
        flash('You do not have access to this log', 'error')
        return redirect(url_for('usage.index'))
    
    resident_id = log.resident_id
    db.session.delete(log)
    db.session.commit()
    flash('Usage log deleted successfully', 'success')
    
    # Redirect back to the usage log for this resident
    return redirect(url_for('usage.index', resident_id=resident_id))
