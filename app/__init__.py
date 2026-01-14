import logging
from flask import Flask, session
# configモジュールの場所がルートにある場合は 'config'、app内にある場合は 'app.config' としてください
# 提示されたコードに従い 'config' からインポートします
from config import Config
from app.extensions import db, migrate, bcrypt, login_manager
from app.routes.root_routes import root_bp


def create_app():
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static'
                )
    
    # 設定の読み込み
    app.config.from_object(Config)

    # ▼▼▼ 追加: ログ設定 ▼▼▼
    # Gunicorn経由で起動した場合、標準出力にログが出るように設定を紐付けます
    if __name__ != '__main__':
        gunicorn_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)
    # ▲▲▲ 追加ここまで ▲▲▲
    
    # アプリと拡張機能を紐付け
    db.init_app(app)
    migrate.init_app(app, db) 
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # --- 循環参照を防ぐため、ここ(関数内)でモデルとBlueprintをインポート ---
    
    # Userモデルのインポート (user_loaderのため)
    from app.models.user import User 

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @login_manager.request_loader
    def load_user_from_request(request):
        user_id = session.get("user_id")
        if not user_id:
            return None
        try:
            return User.query.get(int(user_id))
        except (TypeError, ValueError):
            return User.query.filter_by(email=str(user_id)).first()

    # Blueprintの登録
    from app.routes.plan_routes import plan_bp
    from app.routes.auth_routes import auth_bp
    
    app.register_blueprint(plan_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(root_bp)

    return app
