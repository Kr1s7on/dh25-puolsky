import os

from flask import render_template
from flask_mail import Message

from app import create_app
from app import mail


def send_email(recipient, subject, template, **kwargs):
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    with app.app_context():
        msg = Message(
            app.config['EMAIL_SUBJECT_PREFIX'] + ' ' + subject,
            sender=app.config['EMAIL_SENDER'],
            recipients=[recipient])
        msg.body = render_template(template + '.txt', **kwargs)
        msg.html = render_template(template + '.html', **kwargs)
        
        # Handle PDF attachment if provided
        if 'pdf_attachment' in kwargs:
            pdf = kwargs['pdf_attachment']
            filename = kwargs.get('pdf_filename', 'report.pdf')
            msg.attach(filename, 'application/pdf', pdf.getvalue())
            
        mail.send(msg)
