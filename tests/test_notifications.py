import unittest
from flask import current_app
from app import create_app, db
from app.models.notification import Notification, NotificationType, NotificationStatus
from app.models.user import User, Role
from app.models.resident import Resident
from app.models.inventory_item import InventoryItem
from app.tasks.alerts import check_inventory_thresholds
from datetime import datetime, timedelta

class NotificationSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def test_notification_creation(self):
        # Create test data
        caregiver_role = Role.query.filter_by(name='Caregiver').first()
        caregiver = User(
            email='caregiver@example.com',
            password='password',
            confirmed=True,
            role=caregiver_role,
            first_name='Test',
            last_name='Caregiver'
        )
        db.session.add(caregiver)
        
        resident = Resident(
            first_name='John',
            last_name='Doe',
            date_of_birth=datetime(1950, 1, 1)
        )
        db.session.add(resident)
        resident.caregivers.append(caregiver)
        
        # Create inventory item with quantity below threshold
        item = InventoryItem(
            name='Test Medication',
            type='Medication',
            quantity=5,
            threshold=10,
            unit_type='pills',
            daily_usage=1,
            resident=resident
        )
        db.session.add(item)
        db.session.commit()
        
        # Run threshold check
        with self.app.test_request_context():
            check_inventory_thresholds()
            
        # Verify notification was created
        notification = Notification.query.filter_by(
            type=NotificationType.LOW_STOCK,
            user=caregiver
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.status, NotificationStatus.UNREAD)
        self.assertEqual(notification.inventory_item, item)
        self.assertEqual(notification.resident, resident)
        
    def test_notification_snooze(self):
        # Create a notification
        caregiver_role = Role.query.filter_by(name='Caregiver').first()
        caregiver = User(
            email='caregiver2@example.com',
            password='password',
            confirmed=True,
            role=caregiver_role,
            first_name='Test',
            last_name='Caregiver'
        )
        db.session.add(caregiver)
        db.session.commit()
        
        notification = Notification(
            type=NotificationType.MISSED_DOSE,
            message='Test notification',
            user=caregiver
        )
        db.session.add(notification)
        db.session.commit()
        
        # Test snoozing notification
        notification.snooze(hours=2)
        db.session.commit()
        
        self.assertEqual(notification.status, NotificationStatus.SNOOZED)
        self.assertTrue(notification.snoozed_until > datetime.utcnow())
        self.assertTrue(notification.snoozed_until < datetime.utcnow() + timedelta(hours=3))
