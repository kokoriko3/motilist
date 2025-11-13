# checklist.py
from app import db


class Checklist(db.Model):
    __tablename__ = "checklists"

    checklistId = db.Column(db.Integer, primary_key=True)
    planId = db.Column(db.Integer, db.ForeignKey("plans.planId"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(40), default="draft", nullable=False)
    note = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    # Plan は plan.py 側に定義
    plan = db.relationship("Plan", back_populates="checklists")
    items = db.relationship(
        "ChecklistItem",
        back_populates="checklist",
        cascade="all, delete-orphan",
    )


class ChecklistItem(db.Model):
    __tablename__ = "checklist_items"

    checklistItemId = db.Column(db.Integer, primary_key=True)
    checklistId = db.Column(db.Integer, db.ForeignKey("checklists.checklistId"), nullable=False, index=True)
    itemId = db.Column(db.Integer, db.ForeignKey("items.itemId"), nullable=True, index=True)
    categoryId = db.Column(db.Integer, db.ForeignKey("categories.categoryId"), nullable=True, index=True)
    qty = db.Column(db.Integer, default=1, nullable=False)
    isEssential = db.Column(db.Boolean, default=False, nullable=False)
    reasonsJson = db.Column(db.JSON)
    note = db.Column(db.Text)
    checked = db.Column(db.Boolean, default=False, nullable=False)
    crowned = db.Column(db.Boolean, default=False, nullable=False)
    orderNo = db.Column(db.Integer, default=0, nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    checklist = db.relationship("Checklist", back_populates="items")
    item = db.relationship("Item", back_populates="checklist_items")
    category = db.relationship("Category", back_populates="checklist_items")


class Item(db.Model):
    __tablename__ = "items"

    itemId = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    aliasesJson = db.Column(db.JSON)
    categoryId = db.Column(db.Integer, db.ForeignKey("categories.categoryId"), index=True)
    defaultQty = db.Column(db.Integer, default=1, nullable=False)
    unit = db.Column(db.String(40))
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    tags = db.Column(db.String(255))  # カンマ区切りなどで運用
    searchEnabled = db.Column(db.Boolean, default=True, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    category = db.relationship("Category", back_populates="items")
    checklist_items = db.relationship("ChecklistItem", back_populates="item")


class Category(db.Model):
    __tablename__ = "categories"

    categoryId = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    sortOrder = db.Column(db.Integer, default=0, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    items = db.relationship("Item", back_populates="category")
    checklist_items = db.relationship("ChecklistItem", back_populates="category")