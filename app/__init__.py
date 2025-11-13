from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  
from config import Config

db = SQLAlchemy()
migrate = Migrate()  

def create_app():
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    
    app.config.from_object(Config)
    
    db.init_app(app)
    migrate.init_app(app, db) 

    from app.routes import plan_routes
    app.register_blueprint(plan_routes.bp)
    
    return app