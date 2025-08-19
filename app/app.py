
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

    @app.get("/")
    def index():
        return render_template("index.html")

    return app
