# app/__init__.py
from flask import Flask
from config import Config
# extensionsから作成済みのインスタンスをインポート
from app.extensions import db, migrate, bcrypt, login_manager

def create_app():
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    
    app.config.from_object(Config)
    
    # アプリと拡張機能を紐付け
    db.init_app(app)
    migrate.init_app(app, db) 
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # --- 循環参照を防ぐため、ここ(関数内)でモデルとBlueprintをインポート ---
    
    # Userモデルのインポート (user_loaderのため)
    # ※ import user ではなく、正しいパス(app.models.user)を指定します
    from app.models.user import User 

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprintの登録
    from app.routes.plan_routes import plan_bp
    from app.routes.auth_routes import auth_bp
    
    app.register_blueprint(plan_bp)
    app.register_blueprint(auth_bp)

    return app