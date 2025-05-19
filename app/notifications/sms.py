import os
from twilio.rest import Client
from flask import current_app

def send_sms_alert(to_number, message_body):
    """Send an SMS alert using Twilio."""
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID') or getattr(current_app.config, 'TWILIO_ACCOUNT_SID', None)
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN') or getattr(current_app.config, 'TWILIO_AUTH_TOKEN', None)
    from_number = os.environ.get('TWILIO_FROM_NUMBER') or getattr(current_app.config, 'TWILIO_FROM_NUMBER', None)
    if not (account_sid and auth_token and from_number):
        raise RuntimeError('Twilio credentials not configured')
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=message_body,
        from_=from_number,
        to=to_number
    )
    return message.sid
