"""Simple seed script for local development.

This script spins up the Flask application context and inserts demo data
via SQLAlchemy models so Postgres gains a minimal working dataset.
"""

from datetime import date, datetime
from uuid import uuid4

from app import create_app
from app.extensions import db,bcrypt
from app.models.user import User
from app.models.plan import (
    Plan,
    TransportSnapshot,
    StaySnapshot,
    Schedule,
    ScheduleDetail,
    Template,
    Share,
)
from app.models.checklist import Checklist, ChecklistItem, Item, Category


def run_seed():
    """Entrypoint that clears existing data and inserts demo records."""
    app = create_app()

    with app.app_context():
        # Optional reset flow; keep the delete order child -> parent.
        ChecklistItem.query.delete()
        Checklist.query.delete()
        Item.query.delete()
        Category.query.delete()
        ScheduleDetail.query.delete()
        Schedule.query.delete()
        TransportSnapshot.query.delete()
        StaySnapshot.query.delete()
        Share.query.delete()
        Template.query.delete()
        Plan.query.delete()
        User.query.delete()
        db.session.commit()

        # Users ----------------------------------------------------------------
        user = User(
            anonymous_id="anon-123",
            display_name="デモユーザー",
            email="demo@example.com",
            # passwordHash="dummy-hash",
        )
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

        # Plan ------------------------------------------------------------------
        plan = Plan(
            user_id=user.user_id,
            anonymous_id="anon-plan-1",
            departure="東京",
            destination="大阪",
            start_date=date(2025, 3, 1),
            days=2,
            purpose={"type": "観光", "detail": "1泊2日の関西旅行"},
            options={"budget": "normal"},
            companion_count=1,
        )
        db.session.add(plan)
        db.session.flush()

        # Checklist -------------------------------------------------------------
        checklist = Checklist(
            plan_id=plan.plan_id,
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

        # Schedule & details ----------------------------------------------------
        schedule = Schedule(
            plan_id=plan.plan_id,
            title="大阪1泊2日スケジュール",
            daily_plan_json={"days": plan.days},
            generated_by="seed",
            version=1,
            is_editable=True,
            status="draft",
        )
        db.session.add(schedule)
        db.session.flush()

        schedule_details = [
            ScheduleDetail(
                schedule_id=schedule.schedule_id,
                date=1,
                slot_type="activity",
                title="移動 & チェックイン",
                place_name="新大阪〜梅田周辺",
                start_time=datetime.strptime("09:00", "%H:%M").time(),
                end_time=datetime.strptime("12:00", "%H:%M").time(),
                relative_time=180,
                move_mode="train",
                packing_note="キャリーケースはホテルに預ける",
                sort_order=1,
            ),
            ScheduleDetail(
                schedule_id=schedule.schedule_id,
                date=1,
                slot_type="activity",
                title="道頓堀観光",
                place_name="道頓堀",
                start_time=datetime.strptime("13:00", "%H:%M").time(),
                end_time=datetime.strptime("18:00", "%H:%M").time(),
                relative_time=300,
                move_mode="walk",
                sort_order=2,
            ),
        ]
        db.session.add_all(schedule_details)

        # Template & share ------------------------------------------------------
        template = Template(
            user_id=user.user_id,
            public_title="大阪1泊2日テンプレ",
            note="seed.pyで投入したサンプルテンプレ",
            schedule_summary_json={"example": True},
            checklist_summary_json={"items": ["Tシャツ", "ズボン", "スマホ"]},
            days=plan.days,
            total_items=3,
            required_ratio=1.0,
            search_tags=["大阪", "1泊2日", "観光"],
            publish_status="public",
            display_version=1,
        )
        db.session.add(template)
        db.session.flush()

        share = Share(
            template_id=template.template_id,
            url_token=str(uuid4()),
            permission="read",
            template_version=template.display_version,
            expires_at=None,
            is_expired=False,
            access_count=0,
            issuer_user_id=user.user_id,
        )
        db.session.add(share)

        # Snapshots -------------------------------------------------------------
        transport_snapshot = TransportSnapshot(
            plan_id=plan.plan_id,
            api_source="demo",
            compare_key="tokyo-osaka-demo-1",
            transport_mode="train",
            title_and_section="東京→新大阪",
            duration_minutes=160,
            transfer_count=0,
            price=14000,
            currency="JPY",
            departure_time=datetime.strptime("08:00", "%H:%M").time(),
            arrival_time=datetime.strptime("10:40", "%H:%M").time(),
            fetched_at=datetime.utcnow(),
            note="seedデータ",
        )
        stay_snapshot = StaySnapshot(
            plan_id=plan.plan_id,
            api_source="demo",
            fetched_at=datetime.utcnow(),
            hotel_id="demo-hotel-1",
            title="大阪デモホテル",
            area="梅田",
            address="大阪府大阪市北区1-1-1",
            price_range_text="¥10,000〜¥15,000",
            image_url="https://example.com/hotel.jpg",
            booking_url="https://example.com/booking",
            features=["駅チカ", "朝食付き"],
            review_score=85,
        )
        db.session.add_all([transport_snapshot, stay_snapshot])

        db.session.commit()
        print("Seed完了")


if __name__ == "__main__":
    run_seed()
