#!/usr/bin/env python
# filepath: /Users/puolsky/Downloads/GitHub/dh25-puolsky/test_emails.py

import os
import datetime
from app import create_app, db
from app.models import Resident, InventoryItem, UsageLog, User, Role
from app.models.inventory_item import UsageStatus

def test_email_templates():
    """Test rendering the email templates with sample data."""
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    
    with app.app_context():
        print("Testing email template rendering...")
        
        # Get sample data from the database
        residents = Resident.query.limit(2).all()
        items = InventoryItem.query.limit(5).all()
        logs = UsageLog.query.filter_by(status=UsageStatus.MISSED).limit(5).all()
        caregiver = User.query.filter(
            User.role == Role.query.filter_by(name='Caregiver').first()
        ).first()
        
        if not residents or not items or not logs or not caregiver:
            print("❌ Not enough sample data in database. Please make sure you have residents, items, and logs.")
            return
        
        # 1. Test low stock template
        print("\n---- Testing Low Stock Summary Template ----")
        low_stock_items = [item for item in items if item.quantity <= item.threshold]
        if not low_stock_items:
            print("No low stock items found. Setting some items to low stock for testing...")
            for item in items[:2]:  # Make the first two items low stock
                item.quantity = item.threshold * 0.5
                db.session.add(item)
            db.session.commit()
            low_stock_items = items[:2]
        
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
        
        with open('test_low_stock_email.html', 'w') as f:
            rendered = app.jinja_env.get_template('notifications/email/low_stock_summary.html').render(
                grouped_items=grouped_items.values()
            )
            f.write(rendered)
        
        print("✅ Low stock email template rendered to test_low_stock_email.html")
        
        # 2. Test missed dose template
        print("\n---- Testing Missed Dose Summary Template ----")
        missed_doses = logs
        
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
        
        with open('test_missed_dose_email.html', 'w') as f:
            rendered = app.jinja_env.get_template('notifications/email/missed_dose_summary.html').render(
                grouped_doses=grouped_doses.values()
            )
            f.write(rendered)
        
        print("✅ Missed dose email template rendered to test_missed_dose_email.html")
        
        # 3. Test weekly digest template
        print("\n---- Testing Weekly Digest Template ----")
        
        # Create digest data for testing
        digest_data = []
        for resident in residents:
            resident_items = [item for item in items if item.resident_id == resident.id]
            low_stock = [item for item in resident_items if item.quantity <= item.threshold]
            
            # Get missed doses for these items
            missed_by_item = {}
            for item in resident_items:
                item_logs = [log for log in logs if log.inventory_item_id == item.id]
                if item_logs:
                    missed_by_item[item.id] = {
                        'item': item,
                        'count': len(item_logs)
                    }
            
            digest_data.append({
                'resident': resident,
                'low_stock': low_stock,
                'missed_doses': missed_by_item.values()
            })
        
        with open('test_weekly_digest_email.html', 'w') as f:
            rendered = app.jinja_env.get_template('notifications/email/weekly_digest.html').render(
                caregiver=caregiver,
                digest_data=digest_data,
                start_date=datetime.datetime.now().strftime('%B %d, %Y'),
                end_date=(datetime.datetime.now() + datetime.timedelta(days=7)).strftime('%B %d, %Y')
            )
            f.write(rendered)
        
        print("✅ Weekly digest email template rendered to test_weekly_digest_email.html")
        
        print("\nAll email template tests completed. Check the generated HTML files.")

if __name__ == '__main__':
    test_email_templates()
