import io
import datetime
from flask import render_template, current_app
from flask_mail import Message

from app import db, mail
from app.models import Resident, InventoryItem, UsageLog, Notification, User, Role
from weasyprint import HTML

def generate_pdf(html_content):
    """Generate PDF from HTML content."""
    pdf_file = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_file)
    pdf_file.seek(0)
    return pdf_file

def send_weekly_reports():
    """
    Generate and send weekly reports for all residents to their caregivers.
    This is scheduled to run once a week.
    """
    # Get all residents
    residents = Resident.query.all()
    # Get admin emails for receiving all reports
    admin_role = Role.query.filter_by(name='admin').first()
    admin_emails = [user.email for user in User.query.filter_by(role=admin_role).all()]
    
    # Date range for reports (last 7 days)
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=7)
    
    for resident in residents:
        # 1. Generate Usage Report PDF
        usage_logs = UsageLog.query.filter_by(resident_id=resident.id)\
                                .filter(UsageLog.timestamp.between(start_date, end_date))\
                                .order_by(UsageLog.timestamp.desc()).all()
        
        usage_pdf_html = render_template('reports/usage_report_pdf.html',
                                    resident=resident,
                                    logs=usage_logs,
                                    start_date=start_date,
                                    end_date=end_date,
                                    days=7)
        
        usage_pdf = generate_pdf(usage_pdf_html)
        
        # 2. Generate Stock Report PDF
        inventory_items = InventoryItem.query.filter_by(resident_id=resident.id).all()
        stock_pdf_html = render_template('reports/stock_report_pdf.html',
                                    resident=resident,
                                    items=inventory_items,
                                    date=datetime.datetime.now())
        
        stock_pdf = generate_pdf(stock_pdf_html)
        
        # 3. Generate Alerts Report PDF
        alerts = Notification.query.filter_by(resident_id=resident.id)\
                                .filter(Notification.timestamp.between(start_date, end_date))\
                                .order_by(Notification.timestamp.desc()).all()
        
        alerts_pdf_html = render_template('reports/alerts_report_pdf.html',
                                    resident=resident,
                                    alerts=alerts,
                                    start_date=start_date,
                                    end_date=end_date,
                                    days=7)
        
        alerts_pdf = generate_pdf(alerts_pdf_html)
        
        # Get caregivers for this resident
        caregivers = resident.caregivers
        
        # Send emails to caregivers with all reports
        for caregiver in caregivers:
            # Create the email message
            msg = Message(f'DoseDash: Weekly Reports for {resident.name}',
                        recipients=[caregiver.email] + admin_emails)
            
            # Create filenames
            usage_filename = f"usage_report_{resident.name}_{start_date.date()}_{end_date.date()}.pdf"
            stock_filename = f"stock_report_{resident.name}_{end_date.date()}.pdf"
            alerts_filename = f"alerts_report_{resident.name}_{start_date.date()}_{end_date.date()}.pdf"
            
            # Add attachments
            msg.attach(usage_filename,
                    'application/pdf',
                    usage_pdf.getvalue())
            
            msg.attach(stock_filename,
                    'application/pdf',
                    stock_pdf.getvalue())
            
            msg.attach(alerts_filename,
                    'application/pdf',
                    alerts_pdf.getvalue())
            
            # Add HTML content
            msg.html = render_template('reports/email/weekly_digest.html',
                                    user=caregiver,
                                    resident=resident,
                                    start_date=start_date,
                                    end_date=end_date)
            
            # Add plain text content
            msg.body = render_template('reports/email/weekly_digest.txt',
                                    user=caregiver,
                                    resident=resident,
                                    start_date=start_date,
                                    end_date=end_date)
            
            # Send the email
            mail.send(msg)
            
            current_app.logger.info(f"Weekly reports sent to {caregiver.email} for resident {resident.name}")
