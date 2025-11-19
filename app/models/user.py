# user.py
from app.extensions import db
from flask_login import UserMixin

class User(UserMixin,db.Model):
    __tablename__ = "users"

    userId = db.Column(db.Integer, primary_key=True)
    anonymousId = db.Column(db.String(64), index=True)
    displayName = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, index=True)
    passwordHash = db.Column(db.String(255), nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    plans = db.relationship("Plan", back_populates="user", cascade="all, delete-orphan")
    templates = db.relationship("Template", back_populates="user", cascade="all, delete-orphan")
    created_share_links = db.relationship("ShareLink", back_populates="createdBy")
    
    def get_id(self):
        """Flask-Login 用"""
        return str(self.userId)