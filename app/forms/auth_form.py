from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    email = StringField(
        "メールアドレス", 
        validators=[
            DataRequired(message="メールアドレスを入力してください"), 
            Email(message="メールアドレスの形式が正しくありません")
        ])
    
    password = PasswordField(
        "パスワード", 
        validators=[
            DataRequired(message="パスワードを入力してください"),
        ])
    
    # 試し（フィールド用に個別のルールを設定できる）
    def validate_email(self, field):
        if field.data.endswith("@icloud.com"):
            raise ValidationError("このドメインのメールは利用できません（試験用）")
