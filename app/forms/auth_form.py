from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    email = StringField("メールアドレス", validators=[DataRequired(), Email(message="有効なメールアドレスを入力してください。")])
    password = PasswordField("パスワード", validators=[DataRequired()])
