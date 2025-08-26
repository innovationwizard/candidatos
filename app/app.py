
from flask import Flask, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    env = os.getenv("FLASK_ENV", "production").lower()
    if env == "development":
        from .config import DevConfig as Config
    else:
        from .config import ProdConfig as Config

    app.config.from_object(Config)

    # CORS
    origins = app.config["CORS_ALLOW_ORIGINS"]
    CORS(app, supports_credentials=True, resources={r"/*": {"origins": origins}})

    # Blueprints
    from .auth import bp as auth_bp
    from .api import bp as api_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.get("/debug")
    def debug():
        """Debug endpoint to check database connection"""
        try:
            from .db import get_connection
            dsn = app.config["DATABASE_URL"]
            if not dsn:
                return {"error": "DATABASE_URL not set"}, 500
            
            with get_connection(dsn) as conn:
                with conn.cursor() as cur:
                    # Test auth table
                    cur.execute("SELECT COUNT(*) as count FROM users")
                    users_count = cur.fetchone()["count"]
                    
                    # Test data tables
                    cur.execute("SELECT COUNT(*) as count FROM ubis")
                    ubis_count = cur.fetchone()["count"]
                    cur.execute("SELECT COUNT(*) as count FROM partido")
                    partido_count = cur.fetchone()["count"]
                    
                    # Test auth query specifically
                    cur.execute("SELECT username FROM users LIMIT 1")
                    auth_test = cur.fetchone()
                    
                return {
                    "database_url_set": bool(dsn),
                    "connection": "success",
                    "users_count": users_count,
                    "ubis_count": ubis_count,
                    "partido_count": partido_count,
                    "auth_test": auth_test["username"] if auth_test else None
                }
        except Exception as e:
            return {"error": str(e)}, 500

    @app.get("/")
    def index():
        return render_template("index.html")

    return app
