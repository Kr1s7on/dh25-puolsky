from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from . import inventory
from .. import db
from ..models import InventoryItem, Resident
from ..models.notification import Notification, NotificationType
from ..models.user import User
from ..notifications.sms import send_sms_alert
from ..decorators import admin_required, caregiver_required
from .forms import InventoryItemForm


@inventory.route('/')
@login_required
def index():
    """View all inventory items."""
    inventory_items = InventoryItem.query.all()
    return render_template('inventory/index.html', inventory_items=inventory_items, show_sidebar=True)


@inventory.route('/new', methods=['GET', 'POST'])
@login_required
@caregiver_required
def new_item():
    """Create a new inventory item."""
    form = InventoryItemForm()
    if form.validate_on_submit():
        # Process schedule_times from FieldList to a standard list
        schedule_times = [entry.data for entry in form.schedule_times.entries if entry.data]
        
        item = InventoryItem(
            name=form.name.data,
            type=form.type.data,
            quantity=form.quantity.data,
            threshold=form.threshold.data,
            daily_usage=form.daily_usage.data,
            expiration_date=form.expiration_date.data,
            schedule_times=schedule_times,
            frequency=form.frequency.data,
            relation_to_meals=form.relation_to_meals.data,
            resident_id=form.resident_id.data.id  # Get the id from the resident object
        )
        db.session.add(item)
        db.session.commit()
        # Low-stock notification logic
        if item.quantity < item.threshold:
            caregivers = User.query.filter(User.residents.any(id=item.resident_id), User.sms_opt_in==True, User.phone_number!=None).all()
            for caregiver in caregivers:
                notif = Notification(
                    type=NotificationType.LOW_STOCK,
                    message=f"Low stock: {item.name} for resident {item.resident.name}",
                    user_id=caregiver.id,
                    resident_id=item.resident_id,
                    inventory_item_id=item.id
                )
                db.session.add(notif)
                # Send SMS if opted in
                try:
                    send_sms_alert(caregiver.phone_number, f"DoseDash: Low stock alert for {item.name} (resident: {item.resident.name})")
                except Exception as e:
                    pass  # Optionally log error
            db.session.commit()
        flash('Inventory item {} successfully created'.format(item.name), 'success')
        return redirect(url_for('inventory.index'))
    return render_template('inventory/new.html', form=form)


@inventory.route('/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
@caregiver_required
def edit_item(item_id):
    """Edit an inventory item."""
    item = InventoryItem.query.get_or_404(item_id)
    # Populate the form with existing data
    form = InventoryItemForm()
    if request.method == 'GET':
        form.name.data = item.name
        form.type.data = item.type
        form.quantity.data = item.quantity
        form.threshold.data = item.threshold
        form.daily_usage.data = item.daily_usage
        form.expiration_date.data = item.expiration_date
        
        # Handle schedule_times which is stored as JSON but needs to be a list for FieldList
        if item.schedule_times and isinstance(item.schedule_times, list):
            # Clear default entries and add actual times
            while len(form.schedule_times) > 0:
                form.schedule_times.pop_entry()
            for time in item.schedule_times:
                form.schedule_times.append_entry(time)
        
        form.frequency.data = item.frequency.name if item.frequency else None
        form.relation_to_meals.data = item.relation_to_meals.name if item.relation_to_meals else None
        form.resident_id.data = item.resident
    if form.validate_on_submit():
        item.name = form.name.data
        item.type = form.type.data
        item.quantity = form.quantity.data
        item.threshold = form.threshold.data
        item.daily_usage = form.daily_usage.data
        item.expiration_date = form.expiration_date.data
        
        # Process schedule_times from FieldList to a standard list
        item.schedule_times = [entry.data for entry in form.schedule_times.entries if entry.data]
        
        item.frequency = form.frequency.data
        item.relation_to_meals = form.relation_to_meals.data
        item.resident_id = form.resident_id.data.id  # Get the id from the resident object
        db.session.add(item)
        db.session.commit()
        # Low-stock notification logic
        if item.quantity < item.threshold:
            caregivers = User.query.filter(User.residents.any(id=item.resident_id), User.sms_opt_in==True, User.phone_number!=None).all()
            for caregiver in caregivers:
                notif = Notification(
                    type=NotificationType.LOW_STOCK,
                    message=f"Low stock: {item.name} for resident {item.resident.name}",
                    user_id=caregiver.id,
                    resident_id=item.resident_id,
                    inventory_item_id=item.id
                )
                db.session.add(notif)
                # Send SMS if opted in
                try:
                    send_sms_alert(caregiver.phone_number, f"DoseDash: Low stock alert for {item.name} (resident: {item.resident.name})")
                except Exception as e:
                    pass  # Optionally log error
            db.session.commit()
        flash('Inventory item {} successfully updated'.format(item.name), 'success')
        return redirect(url_for('inventory.index'))
    return render_template('inventory/edit.html', form=form, item=item)


@inventory.route('/<int:item_id>/delete')
@login_required
@caregiver_required
def delete_item(item_id):
    """Delete an inventory item."""
    item = InventoryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Inventory item {} successfully deleted'.format(item.name), 'success')
    return redirect(url_for('inventory.index'))
