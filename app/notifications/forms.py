from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired

class NotificationFilterForm(FlaskForm):
    """Form for filtering notifications."""
    status = SelectField('Status', 
                       choices=[
                           ('all', 'All'),
                           ('unread', 'Unread'),
                           ('snoozed', 'Snoozed'),
                           ('acknowledged', 'Acknowledged')
                       ],
                       default='all')
    type = SelectField('Type',
                      choices=[
                          ('all', 'All'),
                          ('low_stock', 'Low Stock'),
                          ('missed_dose', 'Missed Dose'),
                          ('overdue_dose', 'Overdue Dose')
                      ],
                      default='all')
    submit = SubmitField('Apply Filter')
