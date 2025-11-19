from flask import Flask
from .extensions import db, bcrypt, csrf
from .routes.auth_routes import auth_bp
from .routes.plan_routes import plan_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # DB設定
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # 拡張機能を初期化
    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    # Blueprint 登録
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(plan_bp)

    # DB作成
    with app.app_context():
        db.create_all()

    return app
