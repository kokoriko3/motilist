# plan.py
from app import db


class Plan(db.Model):
    __tablename__ = "plans"

    planId = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("users.userId"), nullable=False, index=True)
    anonymousId = db.Column(db.String(64), index=True)
    departurePlace = db.Column(db.String(255), nullable=False)
    destination = db.Column(db.String(255), nullable=False)
    startDate = db.Column(db.Date, nullable=False)
    days = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.JSON, nullable=True)
    options = db.Column(db.JSON, nullable=True)
    companionsCount = db.Column(db.Integer, default=0, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    user = db.relationship("User", back_populates="plans")
    transport_snapshots = db.relationship(
        "TransportSnapshot",
        back_populates="plan",
        cascade="all, delete-orphan",
    )
    lodging_snapshots = db.relationship(
        "LodgingSnapshot",
        back_populates="plan",
        cascade="all, delete-orphan",
    )
    itineraries = db.relationship(
        "Itinerary",
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

    transportSnapshotId = db.Column(db.Integer, primary_key=True)
    planId = db.Column(db.Integer, db.ForeignKey("plans.planId"), nullable=False, index=True)
    sourceApi = db.Column(db.String(80), nullable=False)
    compareLabel = db.Column(db.String(80))
    mode = db.Column(db.String(40))
    titleAndRoute = db.Column(db.Text)
    durationMin = db.Column(db.Integer)
    transferCount = db.Column(db.Integer)
    fare = db.Column(db.Integer)
    currency = db.Column(db.String(8))
    departureTime = db.Column(db.Time)
    departureBand = db.Column(db.String(40))
    arrivalTime = db.Column(db.Time)
    arrivalBand = db.Column(db.String(40))
    fetchedAt = db.Column(db.DateTime)
    note = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    plan = db.relationship("Plan", back_populates="transport_snapshots")


class LodgingSnapshot(db.Model):
    __tablename__ = "lodging_snapshots"

    lodgingSnapshotId = db.Column(db.Integer, primary_key=True)
    planId = db.Column(db.Integer, db.ForeignKey("plans.planId"), nullable=False, index=True)
    sourceApi = db.Column(db.String(80), nullable=False)
    fetchedAt = db.Column(db.DateTime)
    hotelId = db.Column(db.String(64), index=True)
    title = db.Column(db.String(255))
    area = db.Column(db.String(120))
    address = db.Column(db.String(255))
    priceBand = db.Column(db.String(40))
    imageUrl = db.Column(db.String(512))
    bookingUrl = db.Column(db.String(512))
    features = db.Column(db.JSON)
    reviewAverage = db.Column(db.Integer)
    createdAt = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    plan = db.relationship("Plan", back_populates="lodging_snapshots")


class Itinerary(db.Model):
    __tablename__ = "itineraries"

    itineraryId = db.Column(db.Integer, primary_key=True)
    planId = db.Column(db.Integer, db.ForeignKey("plans.planId"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    daysJson = db.Column(db.JSON)
    source = db.Column(db.String(80))
    version = db.Column(db.Integer, default=1, nullable=False)
    isEditable = db.Column(db.Boolean, default=True, nullable=False)
    status = db.Column(db.String(40), default="draft", nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    plan = db.relationship("Plan", back_populates="itineraries")
    slots = db.relationship(
        "ItinerarySlot",
        back_populates="itinerary",
        cascade="all, delete-orphan",
    )


class ItinerarySlot(db.Model):
    __tablename__ = "itinerary_slots"

    itinerarySlotId = db.Column(db.Integer, primary_key=True)
    itineraryId = db.Column(db.Integer, db.ForeignKey("itineraries.itineraryId"), nullable=False, index=True)
    day = db.Column(db.Integer, nullable=False)
    slotType = db.Column(db.String(40), nullable=False)
    title = db.Column(db.String(255))
    placeName = db.Column(db.String(255))
    startTime = db.Column(db.Time)
    endTime = db.Column(db.Time)
    durationMin = db.Column(db.Integer)
    mode = db.Column(db.String(40))
    packingNote = db.Column(db.Text)
    orderNo = db.Column(db.Integer, default=0, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    itinerary = db.relationship("Itinerary", back_populates="slots")


class Template(db.Model):
    __tablename__ = "templates"

    templateId = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("users.userId"), nullable=False, index=True)
    publicTitle = db.Column(db.String(255), nullable=False)
    shortNote = db.Column(db.Text)
    itineraryOutlineJson = db.Column(db.JSON)
    checklistSummaryJson = db.Column(db.JSON)
    days = db.Column(db.Integer)
    itemsCount = db.Column(db.Integer)
    essentialRatio = db.Column(db.Float)
    tags = db.Column(db.JSON)  # string[] → JSON(list[str]) として保存
    visibility = db.Column(db.String(40), default="private", nullable=False)
    displayVersion = db.Column(db.Integer, default=1, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    user = db.relationship("User", back_populates="templates")
    share_links = db.relationship(
        "ShareLink",
        back_populates="template",
        cascade="all, delete-orphan",
    )


class ShareLink(db.Model):
    __tablename__ = "share_links"

    shareId = db.Column(db.Integer, primary_key=True)
    templateId = db.Column(db.Integer, db.ForeignKey("templates.templateId"), nullable=False, index=True)
    urlToken = db.Column(db.String(100), unique=True, nullable=False, index=True)
    permission = db.Column(db.String(40), default="read", nullable=False)
    targetVersion = db.Column(db.Integer)
    expiresAt = db.Column(db.DateTime)
    disabled = db.Column(db.Boolean, default=False, nullable=False)
    accessCount = db.Column(db.Integer, default=0, nullable=False)
    createdById = db.Column(db.Integer, db.ForeignKey("users.userId"), nullable=True, index=True)
    createdAt = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    lastAccessAt = db.Column(db.DateTime)

    template = db.relationship("Template", back_populates="share_links")
    createdBy = db.relationship("User", back_populates="created_share_links")