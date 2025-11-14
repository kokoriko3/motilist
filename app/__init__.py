from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  
from config import Config

from app.routes.plan_routes import plan_bp
from app.routes.auth_routes import auth_bp

from flask_login import LoginManager
from user import User
from extensions import bcrypt

db = SQLAlchemy()
migrate = Migrate()  

login_manager = LoginManager()
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    
    app.config.from_object(Config)
    bcrypt.init_app(app)
    
    db.init_app(app)
    migrate.init_app(app, db) 

    from app.routes import plan_routes
    app.register_blueprint(plan_routes.bp)
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(plan_bp)


    return app



