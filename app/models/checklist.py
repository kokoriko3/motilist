from app import db

# --- チェックリスト ---
class Checklist(db.Model):
    __tablename__ = "checklists"
    checklistId = db.Column(db.Integer, primary_key=True)
    planId = db.Column(db.Integer, db.ForeignKey("plans.planId"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(40), default="draft", nullable=False)
    note = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)


# --- チェックリスト明細 ---
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


# --- アイテム ---
class Item(db.Model):
    __tablename__ = "items"
    itemId = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    aliasesJson = db.Column(db.JSON)
    categoryId = db.Column(db.Integer, db.ForeignKey("categories.categoryId"), index=True)
    defaultQty = db.Column(db.Integer, default=1, nullable=False)
    unit = db.Column(db.String(40))
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    tags = db.Column(db.String(255))  # カンマ区切り等
    searchEnabled = db.Column(db.Boolean, default=True, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)


# --- カテゴリ ---
class Category(db.Model):
    __tablename__ = "categories"
    categoryId = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    sortOrder = db.Column(db.Integer, default=0, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)