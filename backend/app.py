import os

from flask import Flask, jsonify, send_from_directory

from config import BASE_DIR, Config
from extensions import db

FRONTEND_DIST = os.path.join(os.path.dirname(BASE_DIR), "frontend", "dist")

def create_admin():
    """The one and only admin is created in code - there is no admin registration."""
    from models import User
    if not User.query.filter_by(role="admin").first():
        admin = User(name=Config.ADMIN_NAME, email=Config.ADMIN_EMAIL, role="admin", status="active")
        admin.set_password(Config.ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(Config.DB_DIR, exist_ok=True)
    db.init_app(app)

    from routes import register_routes
    register_routes(app)

    with app.app_context():
        import models
        db.create_all()  
        create_admin()

    @app.after_request
    def cors(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        resp.headers["Access-Control-Expose-Headers"] = "X-Cache"
        return resp

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def not_allowed(_):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def server_error(_):
        db.session.rollback()
        return jsonify({"error": "Something went wrong on the server"}), 500

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def spa(path):
        if os.path.isdir(FRONTEND_DIST):
            file = os.path.join(FRONTEND_DIST, path)
            if path and os.path.isfile(file):
                return send_from_directory(FRONTEND_DIST, path)
            return send_from_directory(FRONTEND_DIST, "index.html")
        return jsonify({"message": "Trekking API is running. Start the Vue dev server in /frontend."})

    return app


_app = None


def get_flask_app():
    global _app
    if _app is None:
        _app = create_app()
    return _app


if __name__ == "__main__":
    get_flask_app().run(debug=True, port=5000, use_reloader=False)
