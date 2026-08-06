import json
import os

from flask import Blueprint, jsonify

clue_bp = Blueprint("clue", __name__)

DATA = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "clues.json"
)


@clue_bp.route("/<int:number>")
def clue(number):

    with open(DATA, "r") as f:
        clues = json.load(f)

    return jsonify(clues[str(number)])