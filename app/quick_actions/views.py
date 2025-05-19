from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.decorators import caregiver_required
from app.models import Resident, InventoryItem, UsageLog
from app.models.usage_log import UsageStatus  # Import UsageStatus from the correct module
from app import db
from datetime import datetime
import json

quick_actions = Blueprint('quick_actions', __name__)

@quick_actions.route('/')
@login_required
@caregiver_required
def index():
    """Quick Actions Dashboard for caregivers."""
    print("Starting quick_actions.index route")
    
    # Get all residents assigned to this caregiver
    residents = current_user.residents.all()
    print(f"Found {len(residents)} residents for caregiver {current_user.id}")
    
    # Dictionary to store medication data by resident
    residents_data = []
    
    for resident in residents:
        # Get scheduled medications for this resident with pending doses
        scheduled_items = InventoryItem.query.filter_by(
            resident_id=resident.id
        ).filter(
            InventoryItem.schedule_times.isnot(None)
        ).all()
        
        # Debug info
        print(f"Found {len(scheduled_items) if scheduled_items else 0} scheduled items for resident {resident.id}")
        
        # Get current time info to determine which items need action now
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        today = datetime.today()
        today_start = datetime(today.year, today.month, today.day)
        
        # Keep track of active medications (due now or upcoming)
        active_items = []
        
        for item in scheduled_items:
            # Debug: Print the type and value of schedule_times
            print(f"Item {item.id}: schedule_times type = {type(item.schedule_times)}, value = {item.schedule_times}")
            
            # Safety check to handle any None values
            if item.schedule_times is None:
                print(f"Schedule times is None for item {item.id}")
                continue
                
            # Convert to list if it's a string or other iterable but not a list
            if isinstance(item.schedule_times, str):
                try:
                    # Try to parse as JSON string
                    import json
                    item.schedule_times = json.loads(item.schedule_times)
                except (json.JSONDecodeError, TypeError):
                    # If can't parse as JSON, skip this item
                    print(f"Error parsing schedule_times for item {item.id}")
                    continue
            
            # Ensure schedule_times is not empty
            if not item.schedule_times:
                print(f"Schedule times is empty for item {item.id}")
                continue
                
            # Ensure schedule_times is a list, tuple, or can be converted to one
            if not isinstance(item.schedule_times, (list, tuple)):
                # If it's a callable (builtin_function_or_method), try to convert it to a list
                try:
                    if callable(item.schedule_times):
                        print(f"schedule_times for item {item.id} is callable, attempting to convert")
                        item.schedule_times = list(item.schedule_times())
                    else:
                        print(f"schedule_times for item {item.id} is not a list or tuple: {type(item.schedule_times)}")
                        continue
                except Exception as e:
                    print(f"Error converting schedule_times for item {item.id}: {e}")
                    continue
                
            # Ensure schedule_times contains valid values
            try:
                schedule_count = len(item.schedule_times)
                print(f"Item {item.id} has {schedule_count} scheduled times")
            except TypeError as e:
                print(f"TypeError when getting length of schedule_times for item {item.id}: {e}")
                continue
            
            for scheduled_time in item.schedule_times:
                # Check if this dose has already been logged today
                usage_log = UsageLog.query.filter(
                    UsageLog.inventory_item_id == item.id,
                    UsageLog.scheduled_time == scheduled_time,
                    UsageLog.timestamp >= today_start
                ).first()
                
                # If no log exists for this scheduled time, add to active items
                if not usage_log:
                    # Calculate time difference to determine status
                    hour, minute = map(int, scheduled_time.split(':'))
                    scheduled_datetime = datetime(today.year, today.month, today.day, hour, minute)
                    
                    # Status: due now (within 1 hour), upcoming, or overdue
                    time_diff = (scheduled_datetime - now).total_seconds() / 3600  # hours
                    
                    status = "upcoming"
                    if abs(time_diff) <= 1:  # Within 1 hour window
                        status = "due_now"
                    elif time_diff < -1:  # More than 1 hour past
                        status = "overdue"
                    
                    # Safely handle the relation_to_meals enum value
                    relation_to_meals = None
                    if item.relation_to_meals:
                        try:
                            relation_to_meals = item.relation_to_meals.value  # Use .value for Enum
                        except (AttributeError, TypeError):
                            # If there's an issue, just use None
                            print(f"Error accessing relation_to_meals for item {item.id}")
                            
                    active_items.append({
                        'id': item.id,
                        'name': item.name,
                        'type': item.type,
                        'scheduled_time': scheduled_time,
                        'status': status,
                        'relation_to_meals': relation_to_meals
                    })
        
        # Sort items: overdue first, then due now, then upcoming
        active_items.sort(key=lambda x: (
            0 if x['status'] == 'overdue' else 
            1 if x['status'] == 'due_now' else 2,
            x['scheduled_time']
        ))
        
        if active_items:
            residents_data.append({
                'id': resident.id,
                'name': resident.name,
                'photo_url': resident.photo_url,
                'items': active_items
            })
    
    return render_template('quick_actions/index.html', residents_data=residents_data, show_sidebar=True)


@quick_actions.route('/log-medication', methods=['POST'])
@login_required
@caregiver_required
def log_medication():
    """Log a medication as either taken or missed."""
    data = request.json
    item_id = data.get('item_id')
    scheduled_time = data.get('scheduled_time')
    status = data.get('status')  # 'taken' or 'missed'
    
    if not all([item_id, scheduled_time, status]) or status not in ['taken', 'missed']:
        return jsonify({'success': False, 'message': 'Invalid input'}), 400
    
    # Get the inventory item
    item = InventoryItem.query.get_or_404(item_id)
    
    # Create a new usage log
    log = UsageLog(
        timestamp=datetime.now(),
        scheduled_time=scheduled_time,
        status=UsageStatus.TAKEN if status == 'taken' else UsageStatus.MISSED,
        inventory_item=item,
        resident=item.resident,
        caregiver=current_user
    )
    
    # If medication was taken, reduce the inventory quantity
    if status == 'taken':
        # Default to reducing by 1 unit
        used_quantity = 1
        if item.quantity >= used_quantity:
            item.quantity -= used_quantity
        else:
            # Don't allow negative quantities
            item.quantity = 0
    
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f"Medication {item.name} marked as {status}",
        'new_quantity': item.quantity
    })
