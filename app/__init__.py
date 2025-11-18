from flask import Flask
from app import db
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  
from flask_login import LoginManager
from config import Config
from .extensions import bcrypt

from app.models.user import User
from app.models.plan import Plan,TransportSnapshot,StaySnapshot,Schedule,ScheduleDetail,Template,Share
from app.models.checklist import Checklist,ChecklistItem,Item,Category


db = SQLAlchemy()
migrate = Migrate()  

login_manager = LoginManager()
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static'
                )
    
    # 設定の読み込み
    app.config.from_object(Config)

    # 拡張の初期化
    bcrypt.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # ルートのimportはここ（関数の中）で行う。
    from app.routes.plan_routes import plan_bp
    from app.routes.auth_routes import auth_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(plan_bp)


    return app



