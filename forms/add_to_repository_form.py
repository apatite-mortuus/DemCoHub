from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class AddToRepository(FlaskForm):
    login = StringField("Никнейм/почта", validators=[DataRequired()])
    submit = SubmitField("Добавить")
