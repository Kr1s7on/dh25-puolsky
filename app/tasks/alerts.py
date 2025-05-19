import os
from datetime import datetime, timedelta

from flask import current_app, render_template
from flask_mail import Message
from flask_rq import get_queue
from twilio.rest import Client

from app import db, mail
from app.models import NotificationType, NotificationStatus, Notification, InventoryItem, User, Role, UsageLog, Resident
from app.models.user import caregiver_resident_association
from app.models.inventory_item import UsageStatus
from app.notifications.sms import send_sms_alert

def check_inventory_thresholds():
    """
    Check inventory items that are below threshold and create notifications.
    """
    # Find all items where quantity is below threshold
    low_stock_items = InventoryItem.query.filter(
        InventoryItem.quantity <= InventoryItem.threshold
    ).all()
    
    for item in low_stock_items:
        # Check if there's already an active notification for this item
        existing_notification = Notification.query.filter(
            Notification.inventory_item_id == item.id,
            Notification.type == NotificationType.LOW_STOCK,
            Notification.status.in_([NotificationStatus.UNREAD, NotificationStatus.SNOOZED])
        ).first()
        
        if existing_notification and existing_notification.status == NotificationStatus.SNOOZED:
            # Skip if notification is snoozed and snooze period hasn't expired
            if existing_notification.snoozed_until and existing_notification.snoozed_until > datetime.utcnow():
                continue
        
        if not existing_notification:
            # Create notifications for all caregivers of the resident
            caregivers = item.resident.caregivers
            
            for caregiver in caregivers:
                notification = Notification(
                    type=NotificationType.LOW_STOCK,
                    message=f"Low stock alert: {item.name} for {item.resident.full_name} is below threshold. Current quantity: {item.quantity} {item.unit_type}",
                    user=caregiver,
                    resident=item.resident,
                    inventory_item=item
                )
                db.session.add(notification)
                
                # If caregiver has opted in for SMS alerts, queue SMS
                if caregiver.sms_enabled and caregiver.phone:
                    get_queue().enqueue(
                        send_sms_alert,
                        phone=caregiver.phone,
                        message=notification.message
                    )
            
    db.session.commit()

def check_missed_doses():
    """
    Check for missed or overdue doses and create notifications.
    """
    # Get all usage logs from the past 24 hours with missed status
    yesterday = datetime.utcnow() - timedelta(days=1)
    missed_doses = UsageLog.query.filter(
        UsageLog.timestamp >= yesterday,
        UsageLog.status == UsageStatus.MISSED
    ).all()
    
    # Group by resident and item to avoid duplicate notifications
    processed = set()
    
    for dose in missed_doses:
        item = dose.inventory_item
        resident = item.resident
        key = (resident.id, item.id)
        
        if key in processed:
            continue
        
        processed.add(key)
        
        # Check if there's already an active notification for this missed dose
        existing_notification = Notification.query.filter(
            Notification.inventory_item_id == item.id,
            Notification.resident_id == resident.id,
            Notification.type == NotificationType.MISSED_DOSE,
            Notification.status.in_([NotificationStatus.UNREAD, NotificationStatus.SNOOZED]),
            Notification.created_at >= yesterday
        ).first()
        
        if existing_notification and existing_notification.status == NotificationStatus.SNOOZED:
            # Skip if notification is snoozed and snooze period hasn't expired
            if existing_notification.snoozed_until and existing_notification.snoozed_until > datetime.utcnow():
                continue
        
        if not existing_notification:
            # Create notifications for all caregivers of the resident
            caregivers = resident.caregivers
            
            for caregiver in caregivers:
                notification = Notification(
                    type=NotificationType.MISSED_DOSE,
                    message=f"Missed dose alert: {resident.full_name} missed a dose of {item.name}",
                    user=caregiver,
                    resident=resident,
                    inventory_item=item
                )
                db.session.add(notification)
                
                # If caregiver has opted in for SMS alerts, queue SMS
                if caregiver.sms_opt_in and caregiver.phone_number:
                    get_queue().enqueue(
                        send_sms_alert,
                        to_number=caregiver.phone_number,
                        message_body=f"Missed dose alert: {resident.full_name} missed a dose of {item.name}"
                    )
    
    db.session.commit()

def check_overdue_doses():
    """
    Check for scheduled doses that haven't been marked as taken or missed.
    """
    # Define what "overdue" means in terms of hours
    grace_period_hours = 2
    
    # Calculate the cutoff time (now minus the grace period)
    cutoff_time = datetime.utcnow() - timedelta(hours=grace_period_hours)
    
    # Get all inventory items with schedules
    scheduled_items = InventoryItem.query.filter(
        InventoryItem.schedule_times != None, 
        InventoryItem.schedule_times != ''
    ).all()
    
    for item in scheduled_items:
        resident = item.resident
        
        # Check each scheduled time
        if item.schedule_times:
            for scheduled_time_str in item.schedule_times:
                # Parse the time string (format depends on your application)
                try:
                    # Assuming schedule_times are stored as "HH:MM" strings
                    hour, minute = map(int, scheduled_time_str.split(':'))
                    
                    # Create datetime for today with that time
                    today = datetime.today()
                    scheduled_datetime = datetime(today.year, today.month, today.day, hour, minute)
                    
                    # If scheduled time + grace period has passed
                    if scheduled_datetime < cutoff_time:
                        # Check if there's a usage log for this item/time today
                        today_start = datetime(today.year, today.month, today.day)
                        tomorrow_start = today_start + timedelta(days=1)
                        
                        usage_log = UsageLog.query.filter(
                            UsageLog.inventory_item_id == item.id,
                            UsageLog.scheduled_time == scheduled_time_str,
                            UsageLog.timestamp >= today_start,
                            UsageLog.timestamp < tomorrow_start
                        ).first()
                        
                        # If no log exists, this dose is overdue
                        if not usage_log:
                            # Check if there's already a notification for this overdue dose
                            existing_notification = Notification.query.filter(
                                Notification.inventory_item_id == item.id,
                                Notification.resident_id == resident.id,
                                Notification.type == NotificationType.OVERDUE_DOSE,
                                Notification.status.in_([NotificationStatus.UNREAD, NotificationStatus.SNOOZED]),
                                Notification.created_at >= today_start
                            ).first()
                            
                            if existing_notification and existing_notification.status == NotificationStatus.SNOOZED:
                                # Skip if notification is snoozed and snooze period hasn't expired
                                if existing_notification.snoozed_until and existing_notification.snoozed_until > datetime.utcnow():
                                    continue
                            
                            if not existing_notification:
                                # Create notifications for all caregivers
                                caregivers = resident.caregivers
                                
                                for caregiver in caregivers:
                                    notification = Notification(
                                        type=NotificationType.OVERDUE_DOSE,
                                        message=f"Overdue dose: {resident.full_name} has an overdue dose of {item.name} scheduled for {scheduled_time_str}",
                                        user=caregiver,
                                        resident=resident,
                                        inventory_item=item
                                    )
                                    db.session.add(notification)
                                    
                                    # If caregiver has opted in for SMS alerts, queue SMS
                                    if caregiver.sms_opt_in and caregiver.phone_number:
                                        get_queue().enqueue(
                                            send_sms_alert,
                                            to_number=caregiver.phone_number,
                                            message_body=f"Overdue dose: {resident.full_name} has an overdue dose of {item.name} scheduled for {scheduled_time_str}"
                                        )
                except (ValueError, TypeError):
                    # Skip invalid schedule times
                    continue
    
    db.session.commit()

def send_weekly_digest():
    """
    Send weekly digest emails to all caregivers.
    """
    # Get all caregivers
    caregiver_role = Role.query.filter_by(name='Caregiver').first()
    if not caregiver_role:
        return
        
    caregivers = User.query.filter_by(role_id=caregiver_role.id).all()
    
    # Calculate date range for the digest (past week)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    for caregiver in caregivers:
        # Skip if no email
        if not caregiver.email:
            continue
            
        # Get residents assigned to this caregiver
        assigned_residents = caregiver.residents.all()
        
        if not assigned_residents:
            continue
            
        # Compile digest data for each resident
        digest_data = []
        
        for resident in assigned_residents:
            # Get inventory items for this resident
            items = InventoryItem.query.filter_by(resident_id=resident.id).all()
            
            # Get low stock items
            low_stock = [item for item in items if item.quantity <= item.threshold]
            
            # Get missed doses in the past week
            missed_doses = UsageLog.query.filter(
                UsageLog.inventory_item_id.in_([item.id for item in items]),
                UsageLog.status == UsageStatus.MISSED,
                UsageLog.timestamp >= start_date,
                UsageLog.timestamp <= end_date
            ).all()
            
            # Group missed doses by item
            missed_by_item = {}
            for dose in missed_doses:
                item = dose.inventory_item
                if item.id not in missed_by_item:
                    missed_by_item[item.id] = {
                        'item': item,
                        'count': 0
                    }
                missed_by_item[item.id]['count'] += 1
            
            # Add to digest data
            digest_data.append({
                'resident': resident,
                'low_stock': low_stock,
                'missed_doses': missed_by_item.values()
            })
        
        # Queue email with digest
        get_queue().enqueue(
            send_digest_email,
            recipient=caregiver.email,
            caregiver=caregiver,
            digest_data=digest_data,
            start_date=start_date,
            end_date=end_date
        )

def send_digest_email(recipient, caregiver, digest_data, start_date, end_date):
    """
    Send a weekly digest email to a caregiver.
    """
    app = current_app._get_current_object()
    with app.app_context():
        msg = Message(
            app.config['EMAIL_SUBJECT_PREFIX'] + ' Weekly Caregiver Digest',
            sender=app.config['EMAIL_SENDER'],
            recipients=[recipient]
        )
        
        # Format dates for display
        start_date_str = start_date.strftime('%B %d, %Y')
        end_date_str = end_date.strftime('%B %d, %Y')
        
        msg.body = render_template(
            'notifications/email/weekly_digest.txt',
            caregiver=caregiver,
            digest_data=digest_data,
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        msg.html = render_template(
            'notifications/email/weekly_digest.html',
            caregiver=caregiver,
            digest_data=digest_data,
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        mail.send(msg)

def send_low_stock_email(recipient, low_stock_items):
    """
    Send an email with low stock summary.
    """
    app = current_app._get_current_object()
    with app.app_context():
        msg = Message(
            app.config['EMAIL_SUBJECT_PREFIX'] + ' Low Stock Alert Summary',
            sender=app.config['EMAIL_SENDER'],
            recipients=[recipient]
        )
        
        # Group items by resident
        grouped_items = {}
        for item in low_stock_items:
            resident_id = item.resident_id
            if resident_id not in grouped_items:
                grouped_items[resident_id] = {
                    'resident': item.resident,
                    'items': []
                }
            grouped_items[resident_id]['items'].append(item)
        
        msg.body = render_template(
            'notifications/email/low_stock_summary.txt',
            grouped_items=grouped_items.values()
        )
        
        msg.html = render_template(
            'notifications/email/low_stock_summary.html',
            grouped_items=grouped_items.values()
        )
        
        mail.send(msg)

def send_missed_dose_email(recipient, missed_doses):
    """
    Send an email with missed dose summary.
    """
    app = current_app._get_current_object()
    with app.app_context():
        msg = Message(
            app.config['EMAIL_SUBJECT_PREFIX'] + ' Missed/Overdue Dose Summary',
            sender=app.config['EMAIL_SENDER'],
            recipients=[recipient]
        )
        
        # Group doses by resident
        grouped_doses = {}
        for dose in missed_doses:
            resident_id = dose.inventory_item.resident_id
            if resident_id not in grouped_doses:
                grouped_doses[resident_id] = {
                    'resident': dose.inventory_item.resident,
                    'doses': []
                }
            grouped_doses[resident_id]['doses'].append(dose)
        
        msg.body = render_template(
            'notifications/email/missed_dose_summary.txt',
            grouped_doses=grouped_doses.values()
        )
        
        msg.html = render_template(
            'notifications/email/missed_dose_summary.html',
            grouped_doses=grouped_doses.values()
        )
        
        mail.send(msg)