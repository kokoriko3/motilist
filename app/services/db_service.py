from app.models.user import User
from app import db


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