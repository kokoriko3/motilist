from app import db
from app.models.user import User
from app.models.plan import Plan
from flask_login import current_user


class UserDBService:


    @staticmethod
    def get_user_by_email(email: str):
        return User.query.filter_by(email=email).first()


    @staticmethod
    def create_user(display_name: str, email: str, password_hash: str):
        user = User(
            displayName=display_name,
            email=email,
            passwordHash=password_hash,
    )
        db.session.add(user)
        db.session.commit()
        return user
    
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