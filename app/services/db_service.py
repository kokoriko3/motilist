from app.extensions import db, bcrypt
from app.models.user import User
from app.models.plan import Plan, Template, TransportSnapshot, Schedule, HotelSnapshot
from flask_login import current_user


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
    def get_all_templates_by_user_id(user_id):
        return Template.query.filter_by(user_id=user_id).all()
    
    @staticmethod
    def get_public_templates():
        return Template.query.filter_by(visibility="public").all()
    
    @staticmethod
    def get_private_templates(user_id):
        return Template.query.filter_by(user_id=user_id, visibility="private").all()
    
    @staticmethod
    def get_all_templates_by_id(template_id):
        return Template.query.filter_by(template_id=template_id).first()

    @staticmethod
    def get_plan_by_id(plan_id, user_id):
        if user_id is None:
            user_id = current_user.id
        return Plan.query.filter_by(id=plan_id, user_id=user_id).first()
    
    @staticmethod
    def get_schedule_by_id(plan_id, user_id=None):
        if user_id is None:
            user_id = current_user.id
        if not user_id:
            return []
        return Schedule.query.join(Plan).filter(
            Schedule.plan_id == plan_id,
            Plan.user_id == user_id
        ).first()
    
    @staticmethod
    def get_transit_by_id(plan_id, user_id=None):
        if user_id is None:
            user_id = current_user.id
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
            user_id = current_user.id
        if not user_id:
            return []
        return HotelSnapshot.query.join(Plan).filter(
            HotelSnapshot.plan_id == plan_id,
            Plan.user_id == user_id
        ).all()

    @staticmethod
    def get_selected_transit(plan_id, user_id=None):
        if user_id is None:
            user_id = current_user.id
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
            user_id = current_user.id
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
            user_id = current_user.id
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
            user_id = current_user.id
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
            user_id = current_user.id
        
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

        