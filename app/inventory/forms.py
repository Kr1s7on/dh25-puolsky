from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FloatField, DateField, SubmitField, TextAreaField, FieldList
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from ..models import Resident, Frequency, MealRelation


class InventoryItemForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(1, 128)])
    type = SelectField('Type', validators=[DataRequired()],
                      choices=[('medication', 'Medication'), ('supply', 'Supply')])
    quantity = FloatField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    threshold = FloatField('Threshold for Low Stock Alert', validators=[DataRequired(), NumberRange(min=0)])
    daily_usage = FloatField('Expected Daily Usage', validators=[DataRequired(), NumberRange(min=0)])
    expiration_date = DateField('Expiration Date', validators=[Optional()])
    
    # Scheduling fields
    schedule_times = FieldList(StringField('Schedule Times'), min_entries=1)
    frequency = SelectField('Frequency', validators=[Optional()],
                          choices=[(freq.name, freq.value.title()) for freq in Frequency])
    relation_to_meals = SelectField('Relation to Meals', validators=[Optional()],
                                  choices=[(rel.name, rel.value.replace('_', ' ').title()) for rel in MealRelation])
    
    resident_id = QuerySelectField('Resident', validators=[DataRequired()],
                                 query_factory=lambda: Resident.query.all(),
                                 get_label='name',
                                 get_pk=lambda r: r.id)
    
    submit = SubmitField('Submit')
