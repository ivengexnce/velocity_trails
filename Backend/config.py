import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "velocity_trials_secret")

    # Firebase
    FIREBASE_CREDENTIAL = os.getenv(
        "FIREBASE_CREDENTIAL",
        "firebase-service-account.json"
    )

    DATABASE_URL = os.getenv("DATABASE_URL", "")

    # Camera
    CAMERA_ID = int(os.getenv("CAMERA_ID", 0))

    # Level 1
    TOTAL_CLUES = 3
    MAX_TIME = 1800          # 30 minutes
    MAX_ATTEMPTS = 3

    # Gesture Recognition
    MIN_DETECTION_CONFIDENCE = 0.7
    MIN_TRACKING_CONFIDENCE = 0.6

    # OCR
    OCR_LANGUAGES = ["en"]

    # Leaderboard
    QUALIFIED_PLAYERS = 10