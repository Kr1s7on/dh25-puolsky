#!/usr/bin/env python
# filepath: /Users/puolsky/Downloads/GitHub/dh25-puolsky/tests/test_reports.py
import unittest
from flask import url_for
from app import create_app, db
from app.models import User, Role, Resident, InventoryItem, UsageLog
from app.models.notification import Notification


class ReportsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)
        
        # Create test user and data
        caregiver_role = Role.query.filter_by(name='caregiver').first()
        self.user = User(
            email='test@example.com',
            password='password',
            first_name='Test',
            last_name='User',
            role=caregiver_role,
            confirmed=True
        )
        
        self.resident = Resident(
            name='Test Resident',
            date_of_birth='1950-01-01',
            photo_url='/static/images/default-profile.png'
        )
        
        self.user.residents.append(self.resident)
        
        db.session.add(self.user)
        db.session.add(self.resident)
        db.session.commit()
        
        # Login
        response = self.client.post(
            url_for('account.login'),
            data={
                'email': 'test@example.com',
                'password': 'password'
            },
            follow_redirects=True
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_reports_page(self):
        response = self.client.get(url_for('reports.index'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Reports' in response.data)
        self.assertTrue(b'Test Resident' in response.data)
    
    def test_usage_report(self):
        response = self.client.get(url_for('reports.usage_report', resident_id=self.resident.id))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Usage Report for Test Resident' in response.data)
    
    def test_stock_report(self):
        response = self.client.get(url_for('reports.stock_report', resident_id=self.resident.id))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Stock Level Report for Test Resident' in response.data)
    
    def test_alerts_report(self):
        response = self.client.get(url_for('reports.alerts_report', resident_id=self.resident.id))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Alerts History Report for Test Resident' in response.data)
    
    def test_pdf_download(self):
        # Test downloading a PDF report
        response = self.client.get(
            url_for('reports.usage_report', resident_id=self.resident.id, format='pdf')
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')

if __name__ == '__main__':
    unittest.main()
