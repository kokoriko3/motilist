from app.extensions import db, bcrypt
from app.models.user import User
from app.models.plan import Plan, Template
from flask_login import current_user
from app.models import (
    Plan,
    Template,
    TransportSnapshot,
    StaySnapshot,
    Checklist
)
from sqlalchemy.orm import joinedload


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
        """ログインユーザのプラン一覧を返す。user_id指定も可。"""
        if user_id is None:
            user_id = current_user.id

        return (
            Plan.query.filter_by(user_id=user_id)
            .order_by(Plan.created_at.desc())
            .all()
        )
    
    @staticmethod
    def get_public_plans():
        # 公開planの取得
        return (
            Template.query.filter_by(publish_status="public")
            .all()
        )
    
    @staticmethod
    def get_plan_by_id(plan_id, user_id=None):
        """指定IDのプランを1件取得（自分のプランだけ）"""
        if user_id is None:
            user_id = current_user.id

        return (
            Plan.query
            .filter_by(id=plan_id, user_id=user_id)
            .first()
        )
    
    @staticmethod
    def create_plan(user_id, destination, departure, start_date, days, purposes, options):
        """フォームから新規プランを作成して、id を返す"""
        if user_id is None:
            user_id = current_user.id

        # 形だけ書いて動きを確認しただけなので変更してください
        plan = Plan(
            user_id=user_id,
            destination=destination,
            departure=departure,
            start_date=start_date,
            days=days,
            purposes=purposes,  # JSONカラム (SQLAlchemy JSON / JSONB)
            options=options,    # 同上
        )

        db.session.add(plan)
        db.session.commit()

        return plan.id

    @staticmethod
    def update_transit(plan_id, transit, user_id=None):
        """交通手段を更新"""
        plan = PlanDBService.get_plan_by_id(plan_id, user_id=user_id)
        if not plan:
            return False

        plan.transit = transit
        db.session.commit()
        return True

    @staticmethod
    def update_hotel(plan_id, hotel, user_id=None):
        """ホテル情報を更新"""
        plan = PlanDBService.get_plan_by_id(plan_id, user_id=user_id)
        if not plan:
            return False

        plan.hotel = hotel
        db.session.commit()
        return True
    

    def get_plan_detail(plan_id: int):
        """詳細ページ用：複数テーブルをまとめて読み込む"""

        plan = (
            Plan.query
            .options(
                joinedload(Plan.template),
                joinedload(Plan.transport_snapshots),
                joinedload(Plan.stay_snapshots),
                joinedload(Plan.checklists),
            )
            .filter_by(plan_id=plan_id)
            .first()
        )

        if not plan:
            return None

        # -----------------------------------------
        # 画面表示用に加工した値
        # -----------------------------------------
        template = plan.template

        # 宿泊先リスト（StaySnapshot）
        stay_locations = [
            s.title for s in plan.stay_snapshots if s.title
        ]

        # 持ち物リスト（Checklist）
        packing_details = [
            {
                "essential": item.essential,
                "extra": item.extra,
                "note": item.note,
            }
            for item in plan.checklists
        ]

        # メタ情報
        meta = {
            "created_on": plan.created_at.strftime("%Y-%m-%d"),
            "price": PlanDBService._calc_plan_price(plan),
            "items_total": len(plan.checklists),
        }

        return {
            "plan": plan,
            "template": template,
            "stay_locations": stay_locations,
            "packing_details": packing_details,
            "meta": meta,
        }

    @staticmethod
    def _calc_plan_price(plan):
        """宿泊 + 交通費 の合計（仮）"""
        price = 0
        for t in plan.transport_snapshots:
            if t.price:
                price += t.price
        for s in plan.stay_snapshots:
            if s.price_range_text:
                m = re.findall(r"\d+", s.price_range_text)
                if m:
                    price += int(m[0])
        return price