from flask import Flask, jsonify

def create_app():
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)
    return app
