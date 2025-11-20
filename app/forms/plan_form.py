# app/forms/plan_form.py
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    DateField,
    IntegerField,
    SelectMultipleField,
    widgets,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class PlanCreateForm(FlaskForm):
    # 行先
    destination = StringField(
        "行先",
        validators=[
            DataRequired(message="行先は必須です。"),
            Length(max=255),
        ],
    )

    # 出発地
    departure = StringField(
        "出発地",
        validators=[
            DataRequired(message="出発地は必須です。"),
            Length(max=255),
        ],
    )

    # 開始日
    start_date = DateField(
        "開始日",
        format="%Y-%m-%d",            # <input type="date"> ならこれでOK
        validators=[DataRequired(message="開始日は必須です。")],
    )

    # 日数
    days = IntegerField(
        "日数",
        validators=[
            DataRequired(message="日数は必須です。"),
            NumberRange(min=1, max=30, message="日数は1〜30日の範囲で入力してください。"),
        ],
    )

    # 目的（JSON カラムになる予定） → Pythonでは list[str] で受ける
    purposes_raw = TextAreaField(
        "旅行の目的（カンマ or 改行区切り）",
        validators=[
            Optional(), Length(max=500)
        ],
    )

    # オプション（これも JSON カラム）
    options = SelectMultipleField(
        "オプション",
        choices=[
            ("with_hotel",    "ホテルも一緒に押さえる"),
            ("with_flight",   "飛行機付き"),
            ("with_rental",   "レンタカー利用"),
            ("early_morning", "早朝出発OK"),
            ("late_return",   "遅めの帰宅OK"),
        ],
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False),
    )