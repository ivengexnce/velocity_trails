import json
import uuid
from flask import jsonify


def generate_player_id():

    return str(uuid.uuid4())


def success(message, data=None):

    return jsonify({

        "success": True,

        "message": message,

        "data": data

    })


def failure(message):

    return jsonify({

        "success": False,

        "message": message

    })


def load_json(path):

    with open(path, "r") as f:

        return json.load(f)


def save_json(path, data):

    with open(path, "w") as f:

        json.dump(data, f, indent=4)