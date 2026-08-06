# pyrefly: ignore [missing-import]
import firebase_admin
# pyrefly: ignore [missing-import]
from firebase_admin import credentials
# pyrefly: ignore [missing-import]
from firebase_admin import firestore

from config import Config

db = None


def initialize():

    global db

    if firebase_admin._apps:
        db = firestore.client()
        return

    cred = credentials.Certificate(
        Config.FIREBASE_CREDENTIAL
    )

    firebase_admin.initialize_app(cred)

    db = firestore.client()


def create_player(player):

    db.collection("players").document(player.uid).set({

        "name": player.name,

        "email": player.email,

        "level": player.level,

        "score": player.score,

        "qualified": False,

        "time": 0,

        "gesture_accuracy": 0

    })


def update_level1(uid, score, total_time, accuracy):
    db.collection("players").document(uid).update({

        "score": score,

        "time": total_time,

        "gesture_accuracy": accuracy,

        "level": 2

    })


def qualify(uid):

    db.collection("players").document(uid).update({

        "qualified": True

    })


def leaderboard():

    docs = db.collection("players") \
             .order_by("time") \
             .stream()

    return [d.to_dict() for d in docs]