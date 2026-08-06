from flask import Blueprint, jsonify

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
def admin():

    return jsonify({
        "status": "Admin Online"
    })