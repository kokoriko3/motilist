"""Simple seed script for local development.

This script spins up the Flask application context and inserts demo data
via SQLAlchemy models so Postgres gains a minimal working dataset.
"""

import json
from datetime import date, datetime
from uuid import uuid4

from app import create_app
from app.extensions import db, bcrypt
from app.models.user import User
from app.models.plan import (
    Plan,
    TransportSnapshot,
    HotelSnapshot, # Changed from StaySnapshot
    Schedule,
    # ScheduleDetail, # Removed: Not in plan.py
    Template,
    Share,
)
from app.models.checklist import Checklist, ChecklistItem, Item, Category


def run_seed():
    """Entrypoint that clears existing data and inserts demo records."""
    app = create_app()

    with app.app_context():
        # Clean up existing data (Child -> Parent order to avoid FK errors)
        Share.query.delete()
        Template.query.delete()
        
        # Checklist related
        ChecklistItem.query.delete()
        Checklist.query.delete()
        Item.query.delete()
        Category.query.delete()
        
        # Plan related
        # Note: ScheduleDetail is likely JSON now, but if table exists in DB from old migration, might need raw SQL or ignore
        Schedule.query.delete()
        TransportSnapshot.query.delete()
        HotelSnapshot.query.delete() # Changed from StaySnapshot
        Plan.query.delete()
        
        # User
        User.query.delete()
        
        db.session.commit()
        print("Existing data cleared.")

        # Users ----------------------------------------------------------------
        user = User(
            anonymous_id="anon-123",
            display_name="デモユーザー",
            email="demo@example.com",
        )
        # Assuming bcrypt is initialized in extensions
        user.passwordHash = bcrypt.generate_password_hash("password123").decode("utf-8")
        db.session.add(user)
        db.session.flush()

        # Categories ------------------------------------------------------------
        cat_wear = Category(name="衣類", sort_order=1)
        cat_gadget = Category(name="ガジェット", sort_order=2)
        cat_other = Category(name="その他", sort_order=99)
        db.session.add_all([cat_wear, cat_gadget, cat_other])
        db.session.flush()

        # Items -----------------------------------------------------------------
        tshirt = Item(
            name="Tシャツ",
            category_id=cat_wear.category_id,
            default_quantity=2,
            unit="枚",
            tags="服,トップス",
            is_searchable=True,
        )
        pants = Item(
            name="ズボン",
            category_id=cat_wear.category_id,
            default_quantity=1,
            unit="本",
            tags="服,ボトムス",
            is_searchable=True,
        )
        smartphone = Item(
            name="スマホ",
            category_id=cat_gadget.category_id,
            default_quantity=1,
            unit="台",
            tags="電子機器",
            is_searchable=True,
        )
        db.session.add_all([tshirt, pants, smartphone])
        db.session.flush()

        hotel = {
            "candidates": [
                {
                    "id": 1,
                    "hotel_no": "196705",
                    "name": "コンフォートホテルＥＲＡ札幌北口",
                    "url": "https://img.travel.rakuten.co.jp/image/tr/api/kw/JBe8h/?f_no=196705",
                    "image_url": "https://img.travel.rakuten.co.jp/share/HOTEL/196705/196705.jpg",
                    "price": 7400,
                    "address": "北海道札幌市北区北七条西5-17-1",
                    "review": "4.2"
                },
                {
                    "id": 2,
                    "hotel_no": "762",
                    "name": "札幌グランドホテル",
                    "url": "https://img.travel.rakuten.co.jp/image/tr/api/kw/JBe8h/?f_no=762",
                    "image_url": "https://img.travel.rakuten.co.jp/share/HOTEL/762/762.jpg",
                    "price": 5525,
                    "address": "北海道札幌市中央区北1条西4丁目",
                    "review": "4.41"
                }
            ],
            "selected_id": None
        }

        # Plan ------------------------------------------------------------------
        # plan.py: Plan model uses 'id', not 'plan_id'
        plan = Plan(
            user_id=user.user_id,
            # anonymous_id="anon-plan-1", # Removed: Not in Plan model
            title="大阪1泊2日プラン",
            departure="東京",
            destination="大阪",
            start_date=date(2025, 3, 1),
            days=2,
            # purpose is Text, not JSON in model. Using string representation.
            purpose="観光 (1泊2日の関西旅行)", 
            options={"budget": "normal"},
            companion_count=1,
            hotel=hotel,
        )
        db.session.add(plan)
        db.session.flush()

        # Checklist -------------------------------------------------------------
        # checklist.py: Checklist model links to plans.id via plan_id
        checklist = Checklist(
            plan_id=plan.id,
            title="大阪1泊2日 持ち物リスト",
            status="draft",
            memo="とりあえず最低限",
        )
        db.session.add(checklist)
        db.session.flush()

        checklist_items = [
            ChecklistItem(
                checklist_id=checklist.checklist_id,
                item_id=tshirt.item_id,
                category_id=cat_wear.category_id,
                quantity=2,
                is_required=True,
                reason_list_json=["汗かきやすいから予備必要"],
                memo="天気次第で1枚減らしてもよさそう",
                is_checked=False,
                sort_order=1,
            ),
            ChecklistItem(
                checklist_id=checklist.checklist_id,
                item_id=pants.item_id,
                category_id=cat_wear.category_id,
                quantity=1,
                is_required=True,
                sort_order=2,
            ),
            ChecklistItem(
                checklist_id=checklist.checklist_id,
                item_id=smartphone.item_id,
                category_id=cat_gadget.category_id,
                quantity=1,
                is_required=True,
                memo="充電器は別チェックリストに分けてもOK",
                sort_order=3,
            ),
        ]
        db.session.add_all(checklist_items)

        # Schedule --------------------------------------------------------------
        # plan.py: Schedule has 'daily_plan_json', no separate ScheduleDetail model
        
        daily_plan_data = {
            "days": plan.days,
            "details": [
                {
                    "day": 1,
                    "slot_type": "activity",
                    "title": "移動 & チェックイン",
                    "place_name": "新大阪〜梅田周辺",
                    "start_time": "09:00",
                    "end_time": "12:00",
                    "move_mode": "train",
                    "note": "キャリーケースはホテルに預ける"
                },
                {
                    "day": 1,
                    "slot_type": "activity",
                    "title": "道頓堀観光",
                    "place_name": "道頓堀",
                    "start_time": "13:00",
                    "end_time": "18:00",
                    "move_mode": "walk"
                }
            ]
        }

        schedule = Schedule(
            plan_id=plan.id,
            daily_plan_json=daily_plan_data,
        )
        db.session.add(schedule)
        db.session.flush()

        # Template & Share ------------------------------------------------------
        # Update fields to match plan.py Template model
        
        itinerary_outline = {
            "days": [
                {
                    "day": 1,
                    "title": "移動 & チェックイン",
                    "traffic_method": "電車",
                    "places": ["新大阪", "梅田周辺", "道頓堀"],
                    "start": "09:00",
                    "end": "10:00"
                },
                {
                    "day": 2,
                    "title": "自由行動",
                    "traffic_method": "徒歩",
                    "places": ["梅田", "難波"],
                    "start": "10:00",
                    "end": "15:00"
                }
            ]
        }

        template = Template(
            user_id=user.user_id,
            plan_id=plan.id,
            public_title="大阪1泊2日テンプレ",
            short_note="seed.pyで投入したサンプルテンプレ", # Renamed from note
            itinerary_outline_json=itinerary_outline, # Renamed from schedule_summary_json
            checklist_summary_json={"items": ["Tシャツ", "ズボン", "スマホ"]},
            days=plan.days,
            items_count=3, # Renamed from total_items
            essential_ratio=100, # Renamed from required_ratio (Assuming Integer percentage)
            tags="大阪,1泊2日,観光", # String based on model
            visibility="public", # Renamed from publish_status
            display_version=1,
        )
        db.session.add(template)
        db.session.flush()

        share = Share(
            template_id=template.template_id,
            url_token=str(uuid4()),
            # permission, template_version, expires_at removed as they are not in Share model
            issuer_user_id=user.user_id,
        )
        db.session.add(share)

        # Snapshots -------------------------------------------------------------
        # TransportSnapshot
        transport_snapshot = TransportSnapshot(
            plan_id=plan.id,
            type="train", # Renamed/Mapped from api_source logic
            transport_method="新幹線（東京→新大阪）",
            cost=14000, # Renamed from price
            duration=160, # minutes
            transit_count=0,
            # Model defines these as String(50), not Time objects
            departure_time="08:00", 
            arrival_time="10:40",
            is_selected=True,
        )
        
        # HotelSnapshot (Renamed from StaySnapshot)
        hotel_snapshot = HotelSnapshot(
            plan_id=plan.id,
            hotel_no="demo-hotel-1",
            name="大阪デモホテル",
            address="大阪府大阪市北区1-1-1",
            price=12000, # Integer
            image_url="https://example.com/hotel.jpg",
            url="https://example.com/booking",
            review="4.5", # String(10)
            is_selected=True,
        )
        db.session.add_all([transport_snapshot, hotel_snapshot])

        db.session.commit()
        print("Seed data insertion completed successfully.")


if __name__ == "__main__":
    run_seed()