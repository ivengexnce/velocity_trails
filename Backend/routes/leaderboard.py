from flask import Blueprint, jsonify

leaderboard_bp = Blueprint("leaderboard", __name__)


@leaderboard_bp.route("/")
def leaderboard():

    return jsonify([])