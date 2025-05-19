from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField

from ..models import User

class ResidentForm(FlaskForm):
    """Form for creating and editing residents."""
    name = StringField('Name', validators=[DataRequired(), Length(1, 64)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    photo = FileField('Resident Photo', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    caregivers = QuerySelectMultipleField('Assigned Caregivers',
                                      validators=[Optional()],
                                      query_factory=lambda: User.query.filter_by(role_id=2).all(),  # Role ID 2 is for Caregiver
                                      get_label=lambda user: f"{user.first_name} {user.last_name}")
    submit = SubmitField('Submit')
