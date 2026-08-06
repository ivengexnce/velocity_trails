import os

from flask import Flask
from flask_cors import CORS

from routes.auth import auth_bp
from routes.clue import clue_bp
from routes.gesture import gesture_bp
from routes.leaderboard import leaderboard_bp
from routes.admin import admin_bp
from services.gesture_service import get_gesture_service

app = Flask(__name__)

# ── Security ───────────────────────────────────────────────────────────────
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev_fallback_change_in_prod")

# ── CORS ───────────────────────────────────────────────────────────────────
# Restrict to your frontend origin in production
CORS(app, origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","))

# ── Blueprints ─────────────────────────────────────────────────────────────
app.register_blueprint(auth_bp,         url_prefix="/api/auth")
app.register_blueprint(clue_bp,         url_prefix="/api/clue")
app.register_blueprint(gesture_bp,      url_prefix="/api/gesture")
app.register_blueprint(leaderboard_bp,  url_prefix="/api/leaderboard")
app.register_blueprint(admin_bp,        url_prefix="/api/admin")


# ── Health check ───────────────────────────────────────────────────────────
@app.route("/")
def home():
    return {
        "project": "Velocity Trials",
        "backend": "Running",
        "version": "1.0",
    }


# ── Teardown: release MediaPipe resources ──────────────────────────────────
@app.teardown_appcontext
def close_gesture_service(exception=None):
    from services.gesture_service import _instance
    if _instance is not None:
        _instance.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)