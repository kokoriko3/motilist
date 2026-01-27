# app/forms/register_form.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class RegisterForm(FlaskForm):
    displayName = StringField(
        "表示名",
        validators=[DataRequired(message="表示名を入力してください。")]
    )

    email = EmailField(
        "メールアドレス",
        validators=[
            DataRequired(message="メールアドレスを入力してください。"),
            Email(message="メールアドレスを正しく入力してください。")
        ]
    )

    password = PasswordField(
        "パスワード",
        validators=[
            DataRequired(message="パスワードを入力してください。"),
            Length(min=8, message="パスワードは8文字以上で入力してください。")
        ]
    )

    password_confirm = PasswordField(
        "パスワード（確認）",
        validators=[
            DataRequired(message="確認用パスワードを入力してください。"),
            EqualTo("password", message="確認用パスワードを正しく入力してください。")
        ]
    )
