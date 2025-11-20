from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    email = StringField("メールアドレス", validators=[DataRequired(), Email()])
    password = PasswordField("パスワード", validators=[DataRequired()])
