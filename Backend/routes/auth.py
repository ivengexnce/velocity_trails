from flask import Blueprint, request, jsonify

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json

    name = data.get("name")
    roll = data.get("roll")
    department = data.get("department")
    year = data.get("year")
    phone = data.get("phone")

    return jsonify({
        "success": True,
        "player": {
            "name": name,
            "roll": roll,
            "department": department,
            "year": year,
            "phone": phone
        },
        "message": "Mission Authorized"
    })