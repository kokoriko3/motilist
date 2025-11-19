# user.py
from app.extensions import db
from flask_login import UserMixin

class User(UserMixin,db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    anonymous_id = db.Column(db.String(64), index=True)
    display_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, index=True)
    passwordHash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    # Plan / Template / ShareLink は plan.py 側にある
    plans = db.relationship(
        "Plan",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    templates = db.relationship(
        "Template",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    created_share_links = db.relationship(
        "ShareLink",
        back_populates="createdBy",
    )