from app.extensions import db, bcrypt
from app.models.user import User
from app.models.plan import Plan, Template, TransportSnapshot, Schedule, HotelSnapshot
from flask_login import current_user
from app.models.checklist import Checklist, ChecklistItem, Item, Category


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
            user_id = current_user.id
        return (
            Plan.query.filter_by(user_id=user_id)
            .order_by(Plan.created_at.desc())
            .all()
        )
    
    @staticmethod
    def get_public_plans():
        return Template.query.filter_by(publish_status="public").all()
    
    @staticmethod
    def get_plan_by_id(plan_id, user_id=None):
        if user_id is None:
            user_id = current_user.id
        return Plan.query.filter_by(id=plan_id, user_id=user_id).first()
    
    @staticmethod
    def get_transit_by_id(plan_id, user_id=None):
        if user_id is None:
            user_id = current_user.id
        if not user_id:
            return []
        return TransportSnapshot.query.join(Plan).filter(
            TransportSnapshot.plan_id == plan_id,
            Plan.user_id == user_id
        ).all()
    
    @staticmethod
    def create_plan(user_id, destination, departure, start_date, days, purpose, options, plan_title):
        if user_id is None:
            user_id = current_user.id
        
        plan = Plan(
            user_id=user_id,
            destination=destination,
            departure=departure,
            start_date=start_date,
            days=days,
            purpose=purpose,
            options=options,
            title = plan_title
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
