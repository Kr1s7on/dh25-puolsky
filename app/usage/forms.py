from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from ..models import Resident, InventoryItem, UsageStatus


class UsageLogForm(FlaskForm):
    """Form for creating a usage log entry."""
    resident = QuerySelectField('Resident', 
                              validators=[DataRequired()],
                              query_factory=lambda: Resident.query.all(),
                              get_label='name')
    inventory_item = QuerySelectField('Medication/Supply',
                                    validators=[DataRequired()],
                                    query_factory=lambda: InventoryItem.query.all(),
                                    get_label='name')
    status = SelectField('Status',
                       validators=[DataRequired()],
                       choices=[(status.name, status.value.title()) for status in UsageStatus])
    scheduled_time = StringField('Scheduled Time (e.g. 08:00)', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    voice_note = FileField('Voice Note', validators=[
        Optional(),
        FileAllowed(['mp3', 'wav'], 'Audio files only!')
    ])
    submit = SubmitField('Log')
