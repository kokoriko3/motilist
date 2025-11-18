from app import db


class Checklist(db.Model):
    __tablename__ = "checklists"

    checklist_id = db.Column(db.Integer, primary_key=True)  #
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.plan_id"), nullable=False, index=True)  #
    title = db.Column(db.String(255), nullable=False)  # 
    status = db.Column(db.String(40), default="draft", nullable=False)  # 
    memo = db.Column(db.Text)  # 
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)  # 
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)  # [cite: 26]

    # Plan は plan.py 側に定義
    plan = db.relationship("Plan", back_populates="checklists")
    items = db.relationship(
        "ChecklistItem",
        back_populates="checklist",
        cascade="all, delete-orphan",
    )


class ChecklistItem(db.Model):
    __tablename__ = "checklist_items"

    checklist_item_id = db.Column(db.Integer, primary_key=True)  # 
    checklist_id = db.Column(db.Integer, db.ForeignKey("checklists.checklist_id"), nullable=False, index=True)  # 
    item_id = db.Column(db.Integer, db.ForeignKey("items.item_id"), nullable=True, index=True)  #
    category_id = db.Column(db.Integer, db.ForeignKey("categories.category_id"), nullable=True, index=True)  # 
    quantity = db.Column(db.Integer, default=1, nullable=False)  # 
    # "isEssential" -> "is_required" (ルール  の 'is_required' を採用)
    is_required = db.Column(db.Boolean, default=False, nullable=False)  # 
    reason_list_json = db.Column(db.JSON)  # 
    memo = db.Column(db.Text)  # 
    is_checked = db.Column(db.Boolean, default=False, nullable=False)  # 
    is_crowned = db.Column(db.Boolean, default=False, nullable=False)  # 
    sort_order = db.Column(db.Integer, default=0, nullable=False)  # 
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)  # 
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)  # 
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)  # 

    checklist = db.relationship("Checklist", back_populates="items")
    item = db.relationship("Item", back_populates="checklist_items")
    category = db.relationship("Category", back_populates="checklist_items")


class Item(db.Model):
    __tablename__ = "items"

    item_id = db.Column(db.Integer, primary_key=True)  # 
    name = db.Column(db.String(120), nullable=False, unique=True)  # 
    name_variants_json = db.Column(db.JSON)  # 
    category_id = db.Column(db.Integer, db.ForeignKey("categories.category_id"), index=True)  # 
    default_quantity = db.Column(db.Integer, default=1, nullable=False)  # 
    unit = db.Column(db.String(40))  # 
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)  # 
    tags = db.Column(db.String(255))  #  (ルール  準拠, 型は元のまま)
    is_searchable = db.Column(db.Boolean, default=True, nullable=False)  # 
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)  # 
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)  # 

    category = db.relationship("Category", back_populates="items")
    checklist_items = db.relationship("ChecklistItem", back_populates="item")


class Category(db.Model):
    __tablename__ = "categories"

    category_id = db.Column(db.Integer, primary_key=True)  # 
    name = db.Column(db.String(120), nullable=False, unique=True)  # 
    sort_order = db.Column(db.Integer, default=0, nullable=False)  # 
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)  # 
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)  # 

    items = db.relationship("Item", back_populates="category")
    checklist_items = db.relationship("ChecklistItem", back_populates="category")