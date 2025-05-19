from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

class ChatForm(FlaskForm):
    """Form for chatbot interactions."""
    message = StringField('Your Question', validators=[DataRequired(), Length(1, 500)])
    submit = SubmitField('Send')
