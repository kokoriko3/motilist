# app/models/plan.py
from datetime import datetime
from app.extensions import db

class Plan(db.Model):
    __tablename__ = 'plans'

    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    
    title = db.Column(db.String(255), nullable=False, default="無題のプラン")
    destination = db.Column(db.String(255), nullable=False)
    departure = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    days = db.Column(db.Integer, nullable=False)
    companion_count = db.Column(db.Integer, nullable=False, default=1)
    purpose = db.Column(db.Text, nullable=True)
    options = db.Column(db.JSON, nullable=True)
    
    transit = db.Column(db.JSON, nullable=True)
    hotel = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーション
    user = db.relationship("User", back_populates="plans")
    
    transport_candidates = db.relationship('TransportSnapshot', backref='plan', lazy=True, cascade="all, delete-orphan")
    schedules = db.relationship('Schedule', backref='plan', lazy=True, cascade="all, delete-orphan")
    hotel_candidates = db.relationship('HotelSnapshot', backref='plan', lazy=True, cascade="all, delete-orphan")
    
    # ▼▼▼ 追加: Checklistとのリレーション（Checklistモデルは別ファイルだが文字列指定でOK） ▼▼▼
    checklists = db.relationship("Checklist", back_populates="plan", cascade="all, delete-orphan")

class Template(db.Model):
    __tablename__ = 'templates'
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    user = db.relationship("User", back_populates="templates")

    publish_status = db.Column(db.String(50), default="private")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    shares = db.relationship("Share", back_populates="template", cascade="all, delete-orphan")

class Share(db.Model):
    __tablename__ = "shares"
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), nullable=False)
    
    issuer_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    createdBy = db.relationship("User", back_populates="created_shares")
    
    template = db.relationship("Template", back_populates="shares")
    
    url_token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TransportSnapshot(db.Model):
    __tablename__ = 'transport_snapshots'
    id = db.Column(db.Integer, primary_key=True)
    
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    
    type = db.Column(db.String(50))
    transport_method = db.Column(db.String(255))
    cost = db.Column(db.Integer)
    duration = db.Column(db.Integer)
    transit_count = db.Column(db.Integer)
    departure_time = db.Column(db.String(50))
    arrival_time = db.Column(db.String(50))
    
    is_selected = db.Column(db.Boolean, default=False, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    daily_plan_json = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HotelSnapshot(db.Model):
    __tablename__ = 'hotel_snapshots'
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    
    hotel_no = db.Column(db.String(50))
    name = db.Column(db.String(255))
    url = db.Column(db.Text)
    image_url = db.Column(db.Text)
    price = db.Column(db.Integer)
    address = db.Column(db.String(255))
    review = db.Column(db.String(10))

    is_selected = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)