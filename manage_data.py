import json
import click
from datetime import date, datetime
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.plan import Plan, TransportSnapshot, HotelSnapshot, Schedule, Template, Share
from app.models.checklist import Checklist, ChecklistItem, Item, Category

app = create_app()

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

@click.group()
def cli():
    """データベースデータの管理コマンド"""
    pass

@cli.command()
def dump():
    """
    最新のプラン1件とその関連データのみを seed_data.json に保存します。
    """
    with app.app_context():
        # 1. 最新のプランを1件取得
        latest_plan = Plan.query.order_by(Plan.created_at.desc()).first()
        
        if not latest_plan:
            print("⚠️  プランデータが存在しません。空のファイルを作成します。")
            with open("seed_data.json", "w", encoding="utf-8") as f:
                json.dump({}, f)
            return

        print(f"📦 最新のプラン (ID: {latest_plan.id}, Title: {latest_plan.title}) を収集中...")

        data = {
            "users": [],
            "plans": [],
            "transport_snapshots": [],
            "hotel_snapshots": [],
            "schedules": [],
            "templates": [],
            "shares": [],
            "checklists": [],
            "checklist_items": [],
            "items": [],     # マスタ系は全件保存
            "categories": [] # マスタ系は全件保存
        }

        # 2. プランデータの保存
        data["plans"].append({
            "id": latest_plan.id,
            "user_id": latest_plan.user_id,
            "title": latest_plan.title,
            "destination": latest_plan.destination,
            "departure": latest_plan.departure,
            "start_date": latest_plan.start_date,
            "days": latest_plan.days,
            "companion_count": latest_plan.companion_count,
            "purpose": latest_plan.purpose,
            "options": latest_plan.options,
            "transit": latest_plan.transit,
            "hotel": latest_plan.hotel,
            "created_at": latest_plan.created_at,
            "updated_at": latest_plan.updated_at
        })

        # 3. 関連するユーザーの保存 (プラン作成者のみ)
        user = User.query.get(latest_plan.user_id)
        if user:
            data["users"].append({
                "user_id": user.user_id,
                "anonymous_id": user.anonymous_id,
                "display_name": user.display_name,
                "email": user.email,
                "passwordHash": user.passwordHash,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            })

        # 4. 関連する子データの保存 (filter_by(plan_id=...) で絞り込み)
        
        # TransportSnapshot
        transports = TransportSnapshot.query.filter_by(plan_id=latest_plan.id).all()
        for t in transports:
            data["transport_snapshots"].append({
                "id": t.id,
                "plan_id": t.plan_id,
                "type": t.type,
                "transport_method": t.transport_method,
                "cost": t.cost,
                "duration": t.duration,
                "transit_count": t.transit_count,
                "departure_time": t.departure_time,
                "arrival_time": t.arrival_time,
                "is_selected": t.is_selected,
                "created_at": t.created_at
            })

        # HotelSnapshot
        hotels = HotelSnapshot.query.filter_by(plan_id=latest_plan.id).all()
        for h in hotels:
            data["hotel_snapshots"].append({
                "id": h.id,
                "plan_id": h.plan_id,
                "hotel_no": h.hotel_no,
                "name": h.name,
                "url": h.url,
                "image_url": h.image_url,
                "price": h.price,
                "address": h.address,
                "review": h.review,
                "is_selected": h.is_selected,
                "created_at": h.created_at
            })

        # Schedule
        schedules = Schedule.query.filter_by(plan_id=latest_plan.id).all()
        for s in schedules:
            data["schedules"].append({
                "id": s.id,
                "plan_id": s.plan_id,
                "daily_plan_json": s.daily_plan_json,
                "created_at": s.created_at
            })
        
        # Template (このプランに関連するものがあれば)
        templates = Template.query.filter_by(plan_id=latest_plan.id).all()
        for tmpl in templates:
            data["templates"].append({
                "template_id": tmpl.template_id,
                "user_id": tmpl.user_id,
                "plan_id": tmpl.plan_id,
                "public_title": tmpl.public_title,
                "short_note": tmpl.short_note,
                "itinerary_outline_json": tmpl.itinerary_outline_json,
                "checklist_summary_json": tmpl.checklist_summary_json,
                "days": tmpl.days,
                "items_count": tmpl.items_count,
                "essential_ratio": tmpl.essential_ratio,
                "tags": tmpl.tags,
                "visibility": tmpl.visibility,
                "display_version": tmpl.display_version,
                "created_at": tmpl.created_at,
                "updated_at": tmpl.updated_at
            })

        # Checklist
        checklists = Checklist.query.filter_by(plan_id=latest_plan.id).all()
        checklist_ids = []
        for cl in checklists:
            checklist_ids.append(cl.checklist_id)
            data["checklists"].append({
                "checklist_id": cl.checklist_id,
                "plan_id": cl.plan_id,
                "title": cl.title,
                "status": cl.status,
                "memo": cl.memo,
                "created_at": cl.created_at,
                "updated_at": cl.updated_at
            })

        # ChecklistItem (抽出したチェックリストIDに含まれるもの)
        if checklist_ids:
            checklist_items = ChecklistItem.query.filter(ChecklistItem.checklist_id.in_(checklist_ids)).all()
            for ci in checklist_items:
                data["checklist_items"].append({
                    "checklist_item_id": ci.checklist_item_id,
                    "checklist_id": ci.checklist_id,
                    "item_id": ci.item_id,
                    "category_id": ci.category_id,
                    "quantity": ci.quantity,
                    "is_required": ci.is_required,
                    "reason_list_json": ci.reason_list_json,
                    "memo": ci.memo,
                    "is_checked": ci.is_checked,
                    "is_crowned": ci.is_crowned,
                    "sort_order": ci.sort_order,
                    "is_deleted": ci.is_deleted,
                    "created_at": ci.created_at,
                    "updated_at": ci.updated_at
                })

        # マスタデータ（Category, Item）はプランに依存しないため全件保存（または必要に応じて絞り込み）
        # ここでは全件保存とします
        for c in Category.query.all():
            data["categories"].append({
                "category_id": c.category_id,
                "name": c.name,
                "sort_order": c.sort_order,
                "created_at": c.created_at,
                "updated_at": c.updated_at
            })
        
        for i in Item.query.all():
            data["items"].append({
                "item_id": i.item_id,
                "name": i.name,
                "name_variants_json": i.name_variants_json,
                "category_id": i.category_id,
                "default_quantity": i.default_quantity,
                "unit": i.unit,
                "is_deleted": i.is_deleted,
                "tags": i.tags,
                "is_searchable": i.is_searchable,
                "created_at": i.created_at,
                "updated_at": i.updated_at
            })

        with open("seed_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, cls=DateEncoder, indent=2, ensure_ascii=False)
        
        print(f"✅ 保存完了: 最新プラン (ID: {latest_plan.id})")

@cli.command()
@click.option('--force', is_flag=True, help="既存データを削除して強制的に上書きします")
def seed(force):
    """seed_data.json からデータをDBにインポートします"""
    if not force:
        print("⚠️  注意: このコマンドは既存のデータを追加します。データ重複のエラーが出る可能性があります。")
        print("既存データを消して初期化したい場合は --force オプションを付けてください。")
        return
    
    try:
        with open("seed_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ seed_data.json が見つかりません。先に 'dump' コマンドを実行してください。")
        return

    with app.app_context():
        print("🗑️  既存のデータを削除中...")
        db.session.query(ChecklistItem).delete()
        db.session.query(Checklist).delete()
        db.session.query(Item).delete()
        db.session.query(Category).delete()
        
        db.session.query(Share).delete()
        db.session.query(Template).delete()
        db.session.query(Schedule).delete()
        db.session.query(HotelSnapshot).delete()
        db.session.query(TransportSnapshot).delete()
        db.session.query(Plan).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        print("🌱 データのインポートを開始します...")

        try:
            # User
            for u_data in data.get("users", []):
                if u_data.get("created_at"): u_data["created_at"] = datetime.fromisoformat(u_data["created_at"])
                if u_data.get("updated_at"): u_data["updated_at"] = datetime.fromisoformat(u_data["updated_at"])
                db.session.merge(User(**u_data))
            db.session.commit()

            # Plan
            for p_data in data.get("plans", []):
                if p_data.get("start_date"): p_data["start_date"] = date.fromisoformat(p_data["start_date"])
                if p_data.get("created_at"): p_data["created_at"] = datetime.fromisoformat(p_data["created_at"])
                if p_data.get("updated_at"): p_data["updated_at"] = datetime.fromisoformat(p_data["updated_at"])
                db.session.merge(Plan(**p_data))
            db.session.commit()

            # Snapshots & Schedule
            for t_data in data.get("transport_snapshots", []):
                if t_data.get("created_at"): t_data["created_at"] = datetime.fromisoformat(t_data["created_at"])
                db.session.merge(TransportSnapshot(**t_data))

            for h_data in data.get("hotel_snapshots", []):
                if h_data.get("created_at"): h_data["created_at"] = datetime.fromisoformat(h_data["created_at"])
                db.session.merge(HotelSnapshot(**h_data))

            for s_data in data.get("schedules", []):
                if s_data.get("created_at"): s_data["created_at"] = datetime.fromisoformat(s_data["created_at"])
                db.session.merge(Schedule(**s_data))
            
            # Template
            for tmpl_data in data.get("templates", []):
                if tmpl_data.get("created_at"): tmpl_data["created_at"] = datetime.fromisoformat(tmpl_data["created_at"])
                if tmpl_data.get("updated_at"): tmpl_data["updated_at"] = datetime.fromisoformat(tmpl_data["updated_at"])
                db.session.merge(Template(**tmpl_data))
            
            # Checklists
            for c_data in data.get("categories", []):
                if c_data.get("created_at"): c_data["created_at"] = datetime.fromisoformat(c_data["created_at"])
                if c_data.get("updated_at"): c_data["updated_at"] = datetime.fromisoformat(c_data["updated_at"])
                db.session.merge(Category(**c_data))
            
            for i_data in data.get("items", []):
                if i_data.get("created_at"): i_data["created_at"] = datetime.fromisoformat(i_data["created_at"])
                if i_data.get("updated_at"): i_data["updated_at"] = datetime.fromisoformat(i_data["updated_at"])
                db.session.merge(Item(**i_data))
                
            for cl_data in data.get("checklists", []):
                if cl_data.get("created_at"): cl_data["created_at"] = datetime.fromisoformat(cl_data["created_at"])
                if cl_data.get("updated_at"): cl_data["updated_at"] = datetime.fromisoformat(cl_data["updated_at"])
                db.session.merge(Checklist(**cl_data))
                
            for ci_data in data.get("checklist_items", []):
                if ci_data.get("created_at"): ci_data["created_at"] = datetime.fromisoformat(ci_data["created_at"])
                if ci_data.get("updated_at"): ci_data["updated_at"] = datetime.fromisoformat(ci_data["updated_at"])
                db.session.merge(ChecklistItem(**ci_data))

            db.session.commit()
            
            # シーケンスリセット
            tables = [
                ('users', 'user_id'),
                ('plans', 'id'),
                ('transport_snapshots', 'id'),
                ('hotel_snapshots', 'id'),
                ('schedules', 'id'),
                ('templates', 'template_id'),
                ('categories', 'category_id'),
                ('items', 'item_id'),
                ('checklists', 'checklist_id'),
                ('checklist_items', 'checklist_item_id')
            ]
            for table, pk in tables:
                try:
                    db.session.execute(db.text(f"SELECT setval(pg_get_serial_sequence('{table}', '{pk}'), coalesce(max({pk}), 1)) FROM {table};"))
                except Exception:
                    pass
            
            db.session.commit()
            print("✅ データのインポートが完了しました！")

        except Exception as e:
            db.session.rollback()
            print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    cli()