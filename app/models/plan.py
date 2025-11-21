from app.extensions import db


class Plan(db.Model):
    __tablename__ = "plans"

    plan_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True)  # 
    anonymous_id = db.Column(db.String(64), index=True)  # 
    departure = db.Column(db.String(255), nullable=False)  # 
    destination = db.Column(db.String(255), nullable=False)  # 
    start_date = db.Column(db.Date, nullable=False)  # 
    days = db.Column(db.Integer, nullable=False)  # 
    purpose = db.Column(db.JSON, nullable=True)  # 
    options = db.Column(db.JSON, nullable=True)  # 
    companion_count = db.Column(db.Integer, default=0, nullable=False)  # 
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)  # [cite: 7]
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)  # [cite: 7]

    user = db.relationship("User", back_populates="plans")
    template = db.relationship(
        "Template",
        back_populates="plan",
        cascade="all, delete-orphan",
    )
    transport_snapshots = db.relationship(
        "TransportSnapshot",
        back_populates="plan",
        cascade="all, delete-orphan",
    )
    # "LodgingSnapshot" -> "StaySnapshot" に修正
    stay_snapshots = db.relationship(
        "StaySnapshot",
        back_populates="plan",
        cascade="all, delete-orphan",
    )
    # "Itinerary" -> "Schedule" に修正
    schedules = db.relationship(
        "Schedule",
        back_populates="plan",
        cascade="all, delete-orphan",
    )
    checklists = db.relationship(
        "Checklist",
        back_populates="plan",
        cascade="all, delete-orphan",
    )


class TransportSnapshot(db.Model):
    __tablename__ = "transport_snapshots"

    transport_snapshot_id = db.Column(db.Integer, primary_key=True)  # 
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.plan_id"), nullable=False, index=True)  # 
    api_source = db.Column(db.String(80), nullable=False)  # 
    compare_key = db.Column(db.String(80))  # 
    transport_mode = db.Column(db.String(40))  # 
    title_and_section = db.Column(db.Text)  # 
    duration_minutes = db.Column(db.Integer)  # 
    transfer_count = db.Column(db.Integer)  # 
    price = db.Column(db.Integer)  # 
    currency = db.Column(db.String(8))  # 
    departure_time = db.Column(db.Time)  # 
    departure_time_band = db.Column(db.String(40))  # 
    arrival_time = db.Column(db.Time)  # [cite: 11]
    arrival_time_band = db.Column(db.String(40))  # [cite: 11]
    fetched_at = db.Column(db.DateTime)  # [cite: 11]
    note = db.Column(db.Text)  # [cite: 11]
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)  # [cite: 12]
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)  # [cite: 12]

    plan = db.relationship("Plan", back_populates="transport_snapshots")


# クラス名を StaySnapshot に修正
class StaySnapshot(db.Model):
    # テーブル名を "lodging_snapshots" -> "stay_snapshots" に修正
    __tablename__ = "stay_snapshots"

    stay_snapshot_id = db.Column(db.Integer, primary_key=True)  # 
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.plan_id"), nullable=False, index=True)  # 
    api_source = db.Column(db.String(80), nullable=False)  # 
    fetched_at = db.Column(db.DateTime)  # 
    hotel_id = db.Column(db.String(64), index=True)  # [cite: 14]
    title = db.Column(db.String(255))  # [cite: 14]
    area = db.Column(db.String(120))  # [cite: 14]
    address = db.Column(db.String(255))  # [cite: 14]
    price_range_text = db.Column(db.String(40))  # [cite: 15]
    image_url = db.Column(db.String(512))  # [cite: 15]
    booking_url = db.Column(db.String(512))  # [cite: 15]
    features = db.Column(db.JSON)  # [cite: 16]
    review_score = db.Column(db.Integer)  # [cite: 15]
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)  # [cite: 16]
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)  # [cite: 16]

    # back_populates を "lodging_snapshots" -> "stay_snapshots" に修正
    plan = db.relationship("Plan", back_populates="stay_snapshots")


# クラス名を Schedule に修正
class Schedule(db.Model):
    # テーブル名を "itineraries" -> "schedules" に修正
    __tablename__ = "schedules"

    schedule_id = db.Column(db.Integer, primary_key=True)  # 
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.plan_id"), nullable=False, index=True)  # 
    title = db.Column(db.String(255), nullable=False)  # 
    daily_plan_json = db.Column(db.JSON)  # 
    generated_by = db.Column(db.String(80))  # 
    version = db.Column(db.Integer, default=1, nullable=False)  # 
    is_editable = db.Column(db.Boolean, default=True, nullable=False)  # 
    status = db.Column(db.String(40), default="draft", nullable=False)  # [cite: 19]
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)  # [cite: 19]
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)  # [cite: 19]

    # back_populates を "itineraries" -> "schedules" に修正
    plan = db.relationship("Plan", back_populates="schedules")
    # relationship名 "slots" -> "schedule_details" に修正
    # back_populates を "itinerary" -> "schedule" に修正
    schedule_details = db.relationship(
        "ScheduleDetail",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )


# クラス名を ItinerarySlot -> ScheduleDetail に修正
class ScheduleDetail(db.Model):
    # テーブル名を "itinerary_slots" -> "schedule_details" に修正
    __tablename__ = "schedule_details"

    schedule_detail_id = db.Column(db.Integer, primary_key=True)  # 
    schedule_id = db.Column(db.Integer, db.ForeignKey("schedules.schedule_id"), nullable=False, index=True)  # [cite: 20, 17]
    date = db.Column(db.Integer, nullable=False)  #  (元の "day" から "date" に変更)
    slot_type = db.Column(db.String(40), nullable=False)  # 
    title = db.Column(db.String(255))  # 
    place_name = db.Column(db.String(255))  # 
    start_time = db.Column(db.Time)  # 
    end_time = db.Column(db.Time)  # 
    relative_time = db.Column(db.Integer)  #  (元の "durationMin" から変更)
    move_mode = db.Column(db.String(40))  # 
    packing_note = db.Column(db.Text)  # [cite: 23]
    sort_order = db.Column(db.Integer, default=0, nullable=False)  # [cite: 23]
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)  # [cite: 23]
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)  # [cite: 23]

    # relationship名 "itinerary" -> "schedule" に修正
    # back_populates を "slots" -> "schedule_details" に修正
    schedule = db.relationship("Schedule", back_populates="schedule_details")


class Template(db.Model):
    __tablename__ = "templates"

    template_id = db.Column(db.Integer, primary_key=True)  # 
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True)  # [cite: 36, 2]
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.plan_id"), nullable=False, index=True)
    public_title = db.Column(db.String(255), nullable=False)  # 
    note = db.Column(db.Text)  # 
    schedule_summary_json = db.Column(db.JSON)  # 
    checklist_summary_json = db.Column(db.JSON)  # 
    days = db.Column(db.Integer)  # 
    total_items = db.Column(db.Integer)  # 
    required_ratio = db.Column(db.Float)  # 
    search_tags = db.Column(db.JSON)  # 
    publish_status = db.Column(db.String(40), default="private", nullable=False)  # 
    display_version = db.Column(db.Integer, default=1, nullable=False)  # 
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)  # 
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)  # 

    user = db.relationship("User", back_populates="templates")
    plan = db.relationship("Plan", back_populates="templates")
    share_links = db.relationship(
        "Share",  # クラス名を "ShareLink" -> "Share" に修正
        back_populates="template",
        cascade="all, delete-orphan",
    )


# クラス名を ShareLink -> Share に修正
class Share(db.Model):
    # テーブル名を "share_links" -> "shares" に修正
    __tablename__ = "shares"

    share_id = db.Column(db.Integer, primary_key=True)  # 
    template_id = db.Column(db.Integer, db.ForeignKey("templates.template_id"), nullable=False, index=True)  # [cite: 41, 36]
    url_token = db.Column(db.String(100), unique=True, nullable=False, index=True)  # [cite: 41]
    permission = db.Column(db.String(40), default="read", nullable=False)  # [cite: 41]
    template_version = db.Column(db.Integer)  # [cite: 41]
    expires_at = db.Column(db.DateTime)  # 
    is_expired = db.Column(db.Boolean, default=False, nullable=False)  # 
    access_count = db.Column(db.Integer, default=0, nullable=False)  # 
    issuer_user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True, index=True)  # [cite: 42, 2]
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)  # [cite: 43]
    last_accessed_at = db.Column(db.DateTime)  # [cite: 43]

    template = db.relationship("Template", back_populates="share_links")
    # back_populates を "created_share_links" -> "created_shares" に修正
    createdBy = db.relationship("User", back_populates="created_shares")