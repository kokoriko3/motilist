# app/models/plan.py
from datetime import datetime
from app.extensions import db
from sqlalchemy.ext.mutable import MutableDict

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
    
    # AI生成結果の一時保存用
    transit = db.Column(db.JSON, nullable=True)
    hotel = db.Column(MutableDict.as_mutable(db.JSON), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーション
    user = db.relationship("User", back_populates="plans")
    # ★これを追加
    templates = db.relationship("Template", back_populates="plan", cascade="all, delete-orphan")
    
    transport_candidates = db.relationship('TransportSnapshot', backref='plan', lazy=True, cascade="all, delete-orphan")
    schedules = db.relationship('Schedule', backref='plan', lazy=True, cascade="all, delete-orphan")
    hotel_candidates = db.relationship('HotelSnapshot', backref='plan', lazy=True, cascade="all, delete-orphan")
    
    # Checklistモデルは checklist.py に定義されていますが、文字列参照でリレーション可能です
    checklists = db.relationship("Checklist", back_populates="plan", cascade="all, delete-orphan")

class Template(db.Model):
    __tablename__ = 'templates'

    # 定義書 No.1: templateId
    template_id = db.Column(db.Integer, primary_key=True)
    
    # 定義書 No.2: userID
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    user = db.relationship("User", back_populates="templates")

    # アプリ仕様上のリンク（プランからテンプレート化する場合用）
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    plan = db.relationship("Plan", back_populates="templates")

    # 定義書 No.3: publicTitle
    public_title = db.Column(db.String(255), nullable=False)

    # 定義書 No.4: shortNote
    short_note = db.Column(db.String(255))

    # 定義書 No.5: itineraryOutlineJson (日程要約)
    itinerary_outline_json = db.Column(db.JSON, nullable=False)

    # 定義書 No.6: checklistSummaryJson (持ち物要約)
    checklist_summary_json = db.Column(db.JSON, nullable=False)

    # 定義書 No.7: days
    days = db.Column(db.Integer)

    # 定義書 No.8: itemsCount
    items_count = db.Column(db.Integer)

    # 定義書 No.9: essentialRatio
    essential_ratio = db.Column(db.Integer) 

    # 定義書 No.10: tags
    tags = db.Column(db.String(255))

    # 定義書 No.11: visibility (旧 publish_status)
    visibility = db.Column(db.String(50), default="private", nullable=False)

    # 追加: 保存先/オプション/公開日
    storage = db.Column(db.String(20))
    flag_a = db.Column(db.Boolean, default=False)
    flag_b = db.Column(db.Boolean, default=False)
    publish_date = db.Column(db.Date)

    # 定義書 No.12: displayVersion
    display_version = db.Column(db.Integer, default=1, nullable=False)

    # 定義書 No.13: createdAt
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # 定義書 No.14: updateAt
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    shares = db.relationship("Share", back_populates="template", cascade="all, delete-orphan")

class Share(db.Model):
    __tablename__ = "shares"
    id = db.Column(db.Integer, primary_key=True)
    
    # template_id を参照するように修正
    template_id = db.Column(db.Integer, db.ForeignKey('templates.template_id'), nullable=False)
    
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
