from app.extensions import db, bcrypt
from app.models.user import User
from app.models.plan import Plan, Template, TransportSnapshot, Schedule, HotelSnapshot, Share
from app.models.checklist import Checklist,ChecklistItem,Item,Category
from flask_login import current_user
from uuid import uuid4


class UserDBService:
    @staticmethod
    def create_user(email, displayName, password):
        user = User(
            email=email,
            displayName=displayName,
            passwordHash=bcrypt.generate_password_hash(password).decode("utf-8")
        )
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def get_user_by_email(email):
        return User.query.filter_by(email=email).first()
    
class PlanDBService:
    @staticmethod
    def get_all_plans(user_id=None):
        if user_id is None:
            user_id = current_user.user_id
        return (
            Plan.query.filter_by(user_id=user_id)
            .order_by(Plan.created_at.desc())
            .all()
        )
    
    @staticmethod
    def get_all_templates_by_user_id(user_id):
        return (
            Template.query.filter_by(user_id=user_id)
            .order_by(Template.created_at.desc())
            .all()
        )
    
    @staticmethod
    def get_public_templates():
        return (
            Template.query.filter_by(visibility="public")
            .order_by(Template.created_at.desc())
            .all()
        )
    
    @staticmethod
    def get_private_templates(user_id):
        return Template.query.filter_by(user_id=user_id, visibility="private").all()
    
    @staticmethod
    def get_all_templates_by_id(template_id):
        return Template.query.filter_by(template_id=template_id).first()

    @staticmethod
    def get_plan_by_id(plan_id, user_id):
        if user_id is None:
            return Plan.query.filter_by(id=plan_id).first()
        return Plan.query.filter_by(id=plan_id, user_id=user_id).first()
    
    @staticmethod
    def get_schedule_by_id(plan_id, user_id=None):
        if user_id is None:
            return Schedule.query.filter(Schedule.plan_id == plan_id).first()
        if not user_id:
            return []
        return Schedule.query.join(Plan).filter(
            Schedule.plan_id == plan_id,
            Plan.user_id == user_id
        ).first()
    
    @staticmethod
    def get_transit_by_id(plan_id, user_id=None):
        if user_id is None:
            user_id = current_user.user_id
        if not user_id:
            return []
        return (
            TransportSnapshot.query.join(Plan)
            .filter(
                TransportSnapshot.plan_id == plan_id,
                Plan.user_id == user_id,
            )
            .order_by(TransportSnapshot.id.asc())
            .all()
        )

    @staticmethod
    def get_hotels_by_id(plan_id, user_id=None):
        if user_id is None:
            user_id = current_user.user_id
        if not user_id:
            return []
        return HotelSnapshot.query.join(Plan).filter(
            HotelSnapshot.plan_id == plan_id,
            Plan.user_id == user_id
        ).all()

    @staticmethod
    def get_selected_transit(plan_id, user_id=None):
        if user_id is None:
            user_id = current_user.user_id
        if not user_id:
            return None
        return TransportSnapshot.query.join(Plan).filter(
            TransportSnapshot.plan_id == plan_id,
            Plan.user_id == user_id,
            TransportSnapshot.is_selected.is_(True)
        ).first()

    @staticmethod
    def get_selected_hotel(plan_id, user_id=None):
        if user_id is None:
            user_id = current_user.user_id
        if not user_id:
            return None
        return HotelSnapshot.query.join(Plan).filter(
            HotelSnapshot.plan_id == plan_id,
            Plan.user_id == user_id,
            HotelSnapshot.is_selected.is_(True)
        ).first()

    @staticmethod
    def select_hotel(plan_id, hotel_snapshot_id, user_id=None):
        if user_id is None:
            user_id = current_user.user_id
        if not user_id:
            return False
        try:
            hotel = (
                HotelSnapshot.query.join(Plan)
                .filter(
                    HotelSnapshot.id == hotel_snapshot_id,
                    HotelSnapshot.plan_id == plan_id,
                    Plan.user_id == user_id,
                )
                .first()
            )
            if not hotel:
                return False

            HotelSnapshot.query.filter_by(plan_id=plan_id).update({"is_selected": False})
            hotel.is_selected = True

            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error selecting hotel: {e}")
            return False

    @staticmethod
    def select_transit(plan_id, transit_type, user_id=None):
        if user_id is None:
            user_id = current_user.user_id
        if not user_id:
            return False
        try:
            snapshot = (
                TransportSnapshot.query.join(Plan)
                .filter(
                    TransportSnapshot.plan_id == plan_id,
                    TransportSnapshot.type == transit_type,
                    Plan.user_id == user_id,
                )
                .first()
            )
            if not snapshot:
                return False

            TransportSnapshot.query.filter_by(plan_id=plan_id).update({"is_selected": False})
            snapshot.is_selected = True
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error selecting transit: {e}")
            return False
    
    @staticmethod
    def create_plan(user_id, destination, departure, start_date, days, purpose, options, plan_title, hotel = None):
        if user_id is None:
            user_id = current_user.user_id
        
        plan = Plan(
            user_id=user_id,
            destination=destination,
            departure=departure,
            start_date=start_date,
            days=days,
            purpose=purpose,
            options=options,
            title = plan_title or "無題のプラン",
            hotel = hotel, # 追加
        )
        db.session.add(plan)
        db.session.commit()
        return plan.id

    @staticmethod
    def create_transit(plan_id, ai_transit):
        if not ai_transit:
            return False
        try:
            for key, data in ai_transit.items():
                snapshot = TransportSnapshot(
                    plan_id=plan_id,
                    type=key, 
                    transport_method=data.get("method"),
                    cost=data.get("estimated_cost"),
                    duration=data.get("estimated_time"),
                    transit_count=data.get("transit_count"),
                    departure_time=str(data.get("departure_time")) if data.get("departure_time") else None,
                    arrival_time=str(data.get("arrival_time")) if data.get("arrival_time") else None
                )
                db.session.add(snapshot)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creating transit snapshots: {e}")
            return False
            
    @staticmethod
    def create_hotel(plan_id, hotels):
        if not hotels:
            return False
        try:
            for h in hotels:
                snapshot = HotelSnapshot(
                    plan_id=plan_id,
                    hotel_no=str(h.get("id")),
                    name=h.get("name"),
                    url=h.get("url"),
                    image_url=h.get("imageUrl"),
                    price=h.get("price"),
                    address=h.get("address"),
                    review=str(h.get("review"))
                )
                db.session.add(snapshot)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creating hotel snapshots: {e}")
            return False

    @staticmethod
    def create_schedule(plan_id, ai_schedule):
        if not ai_schedule:
            return False
        try:
            scchedule = Schedule(
                plan_id=plan_id,
                daily_plan_json = ai_schedule
            )
            db.session.add(scchedule)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creating schedule: {e}")
            return False

    @staticmethod
    def save_template(plan, schedule, title, short_note="", visibility="private"):
        """
        プランをテンプレートとして保存・更新する。
        既に同じプランのテンプレートがある場合は上書きする。
        """
        if not plan or not title:
            return None

        itinerary_outline = schedule.daily_plan_json if schedule else {}
        checklist_summary = {"items": []}
        tags = ", ".join(plan.options) if isinstance(plan.options, list) else (plan.options if plan.options else None)

        try:
            template = Template.query.filter_by(plan_id=plan.id, user_id=plan.user_id).first()

            if template:
                template.public_title = title
                template.short_note = short_note
                template.itinerary_outline_json = itinerary_outline
                template.checklist_summary_json = checklist_summary
                template.days = plan.days
                template.items_count = len(checklist_summary.get("items", [])) if isinstance(checklist_summary, dict) else 0
                template.tags = tags
                template.visibility = visibility or "private"
            else:
                template = Template(
                    user_id=plan.user_id,
                    plan_id=plan.id,
                    public_title=title,
                    short_note=short_note,
                    itinerary_outline_json=itinerary_outline,
                    checklist_summary_json=checklist_summary,
                    days=plan.days,
                    items_count=len(checklist_summary.get("items", [])) if isinstance(checklist_summary, dict) else 0,
                    essential_ratio=None,
                    tags=tags,
                    visibility=visibility or "private",
                    display_version=1,
                )
                db.session.add(template)

            db.session.commit()
            return template
        except Exception as e:
            db.session.rollback()
            print(f"Error saving template: {e}")
            return None

    @staticmethod
    def create_share(template: Template):
        if not template:
            return None
        try:
            # 既存の共有があればそれを使う
            share = Share.query.filter_by(template_id=template.template_id).first()
            if share:
                return share

            share = Share(
                template_id=template.template_id,
                issuer_user_id=template.user_id,
                url_token=str(uuid4()),
            )
            db.session.add(share)
            db.session.commit()
            return share
        except Exception as e:
            db.session.rollback()
            print(f"Error creating share: {e}")
            return None

    @staticmethod
    def get_share_by_token(token: str):
        if not token:
            return None
        return Share.query.filter_by(url_token=token).first()
        

        
    @staticmethod
    def get_plan_detail(plan_id):
        # --- 1. プラン本体 ---
        plan = Plan.query.get(plan_id)
        if not plan:
            return None

        # --- 2. 交通手段 ---
        transports = TransportSnapshot.query.filter_by(plan_id=plan_id).all()
        selected_transport = next((t for t in transports if t.is_selected), None)

        if selected_transport:
            transport_text = selected_transport.transport_method
        elif transports:
            transport_text = transports[0].transport_method
        else:
            transport_text = "未設定"

        # --- 3. 宿泊情報 ---
        hotels = HotelSnapshot.query.filter_by(plan_id=plan_id).all()
        selected_hotel = next((h for h in hotels if h.is_selected), None)

        accommodation = selected_hotel.name if selected_hotel else "未設定"
        hotel_price = (
            f"{selected_hotel.price}円〜"
            if selected_hotel and selected_hotel.price
            else ""
        )

        # --- 4. スケジュール ---
        schedule = Schedule.query.filter_by(plan_id=plan_id).first()
        stay_locations = []

        if schedule and schedule.daily_plan_json:
            for day in schedule.daily_plan_json:
                area = day.get("area", "")
                place = day.get("place", "")
                stay_locations.append(f"{area}（{place}）")

        # --- 5. 返却 ---
        return {
            "plan": plan,
            "transport": transport_text,
            "accommodation": accommodation,
            "stay_locations": stay_locations,
            "hotel_price": hotel_price,
        }


    @staticmethod
    def get_checklist_by_id(plan_id,user_id):
        if user_id is None:
            user_id = current_user.user_id
        if not user_id:
            return None
        return Checklist.query.join(Plan).filter(
            Checklist.plan_id == plan_id,
            Plan.user_id == user_id,
        ).first()

    @staticmethod
    def get_or_create_category(category_name):
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name)
            db.session.add(category)
            db.session.flush()
        return category

    @staticmethod
    def get_or_create_item(item_name, category_id):
        # ユニーク制約が name にかかっているため、まずは名前だけで検索する
        item = Item.query.filter_by(name=item_name).first()
        
        # 存在すればそれを返す（カテゴリが違っても、Itemとしての実体は同一とする）
        if item:
            return item
            
        # 存在しなければ新規作成
        item = Item(name=item_name, category_id=category_id)
        db.session.add(item)
        db.session.flush()
        return item

    @staticmethod
    def create_checklist(plan_id, title="持ち物リスト", status="draft", memo=None):
        checklist = Checklist(
            plan_id=plan_id,
            title=title,
            status=status,
            memo=memo
        )
        db.session.add(checklist)
        db.session.commit()
        return checklist

    @staticmethod
    def add_items_to_checklist(checklist_id, items_data):
        try:
            for category_data in items_data:
                category_name = category_data.get("category")
                if not category_name:
                    continue

                category = PlanDBService.get_or_create_category(category_name)
                
                # 必須アイテムの処理
                for item_name in category_data.get("required_items", []):
                    if not item_name: continue
                    item = PlanDBService.get_or_create_item(item_name, category.category_id)
                    checklist_item = ChecklistItem(
                        checklist_id=checklist_id,
                        item_id=item.item_id,
                        category_id=category.category_id,
                        quantity=1, # デフォルト値
                        is_required=True,
                    )
                    db.session.add(checklist_item)

                # 通常アイテムの処理
                for item_name in category_data.get("items", []):
                    if not item_name: continue
                    item = PlanDBService.get_or_create_item(item_name, category.category_id)
                    checklist_item = ChecklistItem(
                        checklist_id=checklist_id,
                        item_id=item.item_id,
                        category_id=category.category_id,
                        quantity=1, # デフォルト値
                        is_required=False,
                    )
                    db.session.add(checklist_item)
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error adding items to checklist: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    @staticmethod
    def get_checklist_item_by_id(checklist_id):
        checklistItem = ChecklistItem.query.filter_by(checklist_id=checklist_id).all()
        return checklistItem
    @staticmethod
    def copy_plan(plan_id, user_id):
        # 1. 元のプランを取得
        source_plan = Plan.query.get(plan_id)
        if not source_plan:
            return None

        try:
            # 2. プラン本体の複製
            new_title = f"{source_plan.title} のコピー"
            
            new_plan = Plan(
                user_id=user_id,
                destination=source_plan.destination,
                departure=source_plan.departure,
                start_date=source_plan.start_date,
                days=source_plan.days,
                purpose=source_plan.purpose,
                options=source_plan.options,
                title=new_title,
                hotel=source_plan.hotel,     # JSONデータもコピー
                transit=source_plan.transit  # JSONデータもコピー
            )
            db.session.add(new_plan)
            db.session.flush() # new_plan.id を確定させる

            # 3. スケジュールの複製
            source_schedule = Schedule.query.filter_by(plan_id=plan_id).first()
            if source_schedule:
                new_schedule = Schedule(
                    plan_id=new_plan.id,
                    daily_plan_json=source_schedule.daily_plan_json
                )
                db.session.add(new_schedule)

            # 4. 交通手段候補の複製
            source_transports = TransportSnapshot.query.filter_by(plan_id=plan_id).all()
            for t in source_transports:
                new_transport = TransportSnapshot(
                    plan_id=new_plan.id,
                    type=t.type,
                    transport_method=t.transport_method,
                    cost=t.cost,
                    duration=t.duration,
                    transit_count=t.transit_count,
                    departure_time=t.departure_time,
                    arrival_time=t.arrival_time,
                    is_selected=t.is_selected
                )
                db.session.add(new_transport)

            # 5. 宿泊先候補の複製
            source_hotels = HotelSnapshot.query.filter_by(plan_id=plan_id).all()
            for h in source_hotels:
                new_hotel = HotelSnapshot(
                    plan_id=new_plan.id,
                    hotel_no=h.hotel_no,
                    name=h.name,
                    url=h.url,
                    image_url=h.image_url,
                    price=h.price,
                    address=h.address,
                    review=h.review,
                    is_selected=h.is_selected
                )
                db.session.add(new_hotel)

            # 6. チェックリストの複製
            source_checklist = Checklist.query.filter_by(plan_id=plan_id).first()
            
            if source_checklist:
                # チェックリスト本体
                new_checklist = Checklist(
                    plan_id=new_plan.id,
                    title=source_checklist.title,
                    status="draft",
                    memo=source_checklist.memo
                )
                db.session.add(new_checklist)
                db.session.flush() # ID確定

                # アイテム詳細
                source_items = ChecklistItem.query.filter_by(
                    checklist_id=source_checklist.checklist_id, 
                    is_deleted=False
                ).all()

                for item in source_items:
                    new_item = ChecklistItem(
                        checklist_id=new_checklist.checklist_id,
                        item_id=item.item_id,
                        category_id=item.category_id,
                        quantity=item.quantity,
                        is_required=item.is_required,
                        reason_list_json=item.reason_list_json,
                        memo=item.memo,
                        is_checked=False, # チェック状態はリセット
                        is_crowned=item.is_crowned,
                        sort_order=item.sort_order,
                        is_deleted=False
                    )
                    db.session.add(new_item)

            # 7. テンプレートの複製（★追加部分）
            source_template = Template.query.filter_by(plan_id=plan_id).first()
            if source_template:
                new_template_title = f"{source_template.public_title} のコピー"
                
                new_template = Template(
                    user_id=user_id,
                    plan_id=new_plan.id,
                    public_title=new_template_title,
                    short_note=source_template.short_note,
                    itinerary_outline_json=source_template.itinerary_outline_json,
                    checklist_summary_json=source_template.checklist_summary_json,
                    days=source_template.days,
                    items_count=source_template.items_count,
                    essential_ratio=source_template.essential_ratio,
                    tags=source_template.tags,
                    visibility="private", # コピー後は非公開に戻す
                    display_version=1     # バージョンリセット
                )
                db.session.add(new_template)
                # Share（共有URL）はコピーしません（新規発行が必要なため）

            db.session.commit()
            return new_plan.id

        except Exception as e:
            db.session.rollback()
            print(f"Error copying plan: {e}")
            import traceback
            traceback.print_exc()
            return None

