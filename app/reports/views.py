import datetime
import io
from flask import render_template, request, url_for, redirect, flash, send_file
from flask_login import login_required, current_user

from . import reports
from app.models import Resident, InventoryItem, UsageLog, Notification
from app import db

from weasyprint import HTML


def generate_pdf(html_content):
    """Generate PDF from HTML content."""
    pdf_file = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_file)
    pdf_file.seek(0)
    return pdf_file


@reports.route('/')
@login_required
def index():
    """Reports landing page."""
    residents = Resident.query.all()
    return render_template('reports/index.html', residents=residents, show_sidebar=True)


@reports.route('/usage/<int:resident_id>')
@login_required
def usage_report(resident_id):
    """Generate usage report for a resident."""
    resident = Resident.query.get_or_404(resident_id)
    
    # Get date range
    days = int(request.args.get('days', 7))  # Default to 7 days
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=days)
    
    # Get usage logs
    logs = UsageLog.query.filter_by(resident_id=resident_id)\
                        .filter(UsageLog.timestamp.between(start_date, end_date))\
                        .order_by(UsageLog.timestamp.desc()).all()
    
    # For HTML view
    if request.args.get('format', 'html') == 'html':
        return render_template('reports/usage_report.html', 
                            resident=resident, 
                            logs=logs,
                            start_date=start_date,
                            end_date=end_date,
                            days=days,
                            show_sidebar=True)
    
    # For PDF download
    pdf_html = render_template('reports/usage_report_pdf.html', 
                            resident=resident, 
                            logs=logs,
                            start_date=start_date,
                            end_date=end_date,
                            days=days)
    
    pdf = generate_pdf(pdf_html)
    return send_file(
        pdf,
        download_name=f"usage_report_{resident.name}_{start_date.date()}_{end_date.date()}.pdf",
        mimetype='application/pdf'
    )


@reports.route('/stock/<int:resident_id>')
@login_required
def stock_report(resident_id):
    """Generate stock level report for a resident."""
    resident = Resident.query.get_or_404(resident_id)
    
    # Get all inventory items
    items = InventoryItem.query.filter_by(resident_id=resident_id).all()
    
    # For HTML view
    if request.args.get('format', 'html') == 'html':
        return render_template('reports/stock_report.html', 
                            resident=resident, 
                            items=items,
                            date=datetime.datetime.now(),
                            show_sidebar=True)
    
    # For PDF download
    pdf_html = render_template('reports/stock_report_pdf.html', 
                            resident=resident, 
                            items=items,
                            date=datetime.datetime.now())
    
    pdf = generate_pdf(pdf_html)
    return send_file(
        pdf,
        download_name=f"stock_report_{resident.name}_{datetime.datetime.now().date()}.pdf",
        mimetype='application/pdf'
    )


@reports.route('/alerts/<int:resident_id>')
@login_required
def alerts_report(resident_id):
    """Generate alerts history report for a resident."""
    resident = Resident.query.get_or_404(resident_id)
    
    # Get date range
    days = int(request.args.get('days', 30))  # Default to 30 days
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=days)
    
    # Get alerts
    alerts = Notification.query.filter_by(resident_id=resident_id)\
                            .filter(Notification.timestamp.between(start_date, end_date))\
                            .order_by(Notification.timestamp.desc()).all()
    
    # For HTML view
    if request.args.get('format', 'html') == 'html':
        return render_template('reports/alerts_report.html', 
                            resident=resident, 
                            alerts=alerts,
                            start_date=start_date,
                            end_date=end_date,
                            days=days,
                            show_sidebar=True)
    
    # For PDF download
    pdf_html = render_template('reports/alerts_report_pdf.html', 
                            resident=resident, 
                            alerts=alerts,
                            start_date=start_date,
                            end_date=end_date,
                            days=days)
    
    pdf = generate_pdf(pdf_html)
    return send_file(
        pdf,
        download_name=f"alerts_report_{resident.name}_{start_date.date()}_{end_date.date()}.pdf",
        mimetype='application/pdf'
    )


@reports.route('/email/<report_type>/<int:resident_id>')
@login_required
def email_report(report_type, resident_id):
    """Email a report to the current user."""
    from app.email import send_email
    
    resident = Resident.query.get_or_404(resident_id)
    days = int(request.args.get('days', 7))  # Default to 7 days
    
    if report_type == 'usage':
        # Generate usage report PDF
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        pdf_html = render_template('reports/usage_report_pdf.html', 
                                resident=resident, 
                                logs=UsageLog.query.filter_by(resident_id=resident_id)
                                        .filter(UsageLog.timestamp.between(start_date, end_date))
                                        .order_by(UsageLog.timestamp.desc()).all(),
                                start_date=start_date,
                                end_date=end_date,
                                days=days)
        
        report_name = f"Usage Report for {resident.name}"
        pdf_attachment = generate_pdf(pdf_html)
        
    elif report_type == 'stock':
        # Generate stock report PDF
        pdf_html = render_template('reports/stock_report_pdf.html', 
                                resident=resident, 
                                items=InventoryItem.query.filter_by(resident_id=resident_id).all(),
                                date=datetime.datetime.now())
        
        report_name = f"Stock Level Report for {resident.name}"
        pdf_attachment = generate_pdf(pdf_html)
        
    elif report_type == 'alerts':
        # Generate alerts report PDF
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        pdf_html = render_template('reports/alerts_report_pdf.html', 
                                resident=resident, 
                                alerts=Notification.query.filter_by(resident_id=resident_id)
                                            .filter(Notification.timestamp.between(start_date, end_date))
                                            .order_by(Notification.timestamp.desc()).all(),
                                start_date=start_date,
                                end_date=end_date,
                                days=days)
        
        report_name = f"Alerts History Report for {resident.name}"
        pdf_attachment = generate_pdf(pdf_html)
    
    else:
        flash('Invalid report type.', 'error')
        return redirect(url_for('reports.index'))
    
    # Email the report
    send_email(
        current_user.email,
        f'DoseDash: {report_name}',
        'reports/email/report',
        user=current_user,
        resident=resident,
        report_name=report_name,
        date=datetime.datetime.now(),
        pdf_attachment=pdf_attachment
    )
    
    flash(f'Report has been emailed to {current_user.email}.', 'success')
    return redirect(url_for('reports.index'))
