"""
gesture.py – Velocity Trials · Backend/routes/gesture.py
==========================================================
Flask blueprint: /gesture
Exposes the gesture recognition service to the frontend via JSON endpoints.

Endpoints
---------
  POST   /gesture/session/start    – begin a new code-entry session
  POST   /gesture/session/end      – close the session manually
  GET    /gesture/state            – current buffer state
  POST   /gesture/frame            – process one webcam frame
  POST   /gesture/backspace        – remove last digit via UI button
  POST   /gesture/clear            – wipe buffer via UI button
  POST   /gesture/validate         – check entered code against expected
"""

from flask import Blueprint, jsonify, request

from services.gesture_service import get_gesture_service

gesture_bp = Blueprint("gesture", __name__)


# ── Helper ────────────────────────────────────────────────────────────────────

def _svc():
    """Shorthand accessor for the singleton service."""
    return get_gesture_service()


# ── Session lifecycle ─────────────────────────────────────────────────────────

@gesture_bp.route("/session/start", methods=["POST"])
def start_session():
    """
    POST /gesture/session/start
    ───────────────────────────
    Body (optional JSON):
        { "code_length": 4 }

    Resets the gesture buffer and opens a new entry session.
    Call this when the Level 1 portal screen loads for a player.

    Response:
        { "ok": true, "state": { ...GestureService.get_state() } }
    """
    body = request.get_json(silent=True) or {}
    code_length = body.get("code_length")

    try:
        _svc().start_session(code_length=int(code_length) if code_length else None)
    except (ValueError, TypeError):
        return jsonify({"ok": False, "error": "invalid_code_length"}), 400

    return jsonify({"ok": True, "state": _svc().get_state()})


@gesture_bp.route("/session/end", methods=["POST"])
def end_session():
    """
    POST /gesture/session/end
    ─────────────────────────
    Closes the session without clearing the buffer.
    Useful if the admin wants to cut off input early.
    """
    _svc().end_session()
    return jsonify({"ok": True, "state": _svc().get_state()})


# ── State ─────────────────────────────────────────────────────────────────────

@gesture_bp.route("/state", methods=["GET"])
def get_state():
    """
    GET /gesture/state
    ──────────────────
    Returns the current buffer and session status without processing a frame.
    Useful for the frontend to poll when the camera is not yet active.
    """
    return jsonify(_svc().get_state())


# ── Frame processing ──────────────────────────────────────────────────────────

@gesture_bp.route("/frame", methods=["POST"])
def process_frame():
    """
    POST /gesture/frame
    ───────────────────
    Body (JSON):
        { "frame": "<base64-encoded JPEG or PNG>" }

    The frontend captures a webcam frame at ~10 fps and sends it here.
    Returns the recognition result so the UI can:
      - show which gesture is currently detected
      - animate a hold-progress ring (0.0 → 1.0)
      - update the code buffer display when a digit registers

    Response:
        {
          "session_active":  bool,
          "code_buffer":     ["3","7","4"],
          "buffer_display":  "3 7 4",
          "buffer_length":   3,
          "max_length":      6,
          "detected":        "4" | "CONFIRM" | null,
          "registered":      "4" | "CONFIRM" | "BACKSPACE" | null,
          "hold_progress":   0.0–1.0,
          "error":           null | "no_active_session" | "invalid_frame"
        }
    """
    body = request.get_json(silent=True) or {}
    frame_b64 = body.get("frame", "").strip()

    if not frame_b64:
        return jsonify({
            "error": "missing_frame",
            "detected": None,
            "registered": None,
            "hold_progress": 0.0,
            **_svc().get_state(),
        }), 400

    result = _svc().process_frame(frame_b64)
    status = 200 if result.get("error") is None else 422
    return jsonify(result), status


# ── Buffer controls (UI buttons as fallback) ──────────────────────────────────

@gesture_bp.route("/backspace", methods=["POST"])
def backspace():
    """
    POST /gesture/backspace
    ───────────────────────
    Remove the last digit from the buffer.
    Exposed so the UI can offer a physical backspace button alongside gestures.
    """
    _svc().backspace()
    return jsonify({"ok": True, "state": _svc().get_state()})


@gesture_bp.route("/clear", methods=["POST"])
def clear_buffer():
    """
    POST /gesture/clear
    ───────────────────
    Wipe the entire code buffer and reset hold state.
    """
    _svc().clear_buffer()
    return jsonify({"ok": True, "state": _svc().get_state()})


# ── Code validation ───────────────────────────────────────────────────────────

@gesture_bp.route("/validate", methods=["POST"])
def validate_code():
    """
    POST /gesture/validate
    ──────────────────────
    Body (JSON):
        {
          "player_id":    "p_abc123",      (optional, for logging)
          "expected":     "3742"           (the Level 1 secret code)
        }

    Compares the gesture buffer against the expected code.
    On success the session is closed.

    Response:
        {
          "correct":   true | false,
          "entered":   "3742",
          "expected":  "3742",
          "state":     { ...get_state() }
        }
    """
    body = request.get_json(silent=True) or {}
    expected = body.get("expected", "").strip()

    if not expected:
        return jsonify({
            "error": "expected_code_required",
            "hint": "Pass {'expected': '<secret_code>'} in the request body.",
        }), 400

    svc = _svc()
    correct = svc.validate(expected)
    entered = "".join(svc.code_buffer)

    if correct:
        svc.end_session()

    return jsonify({
        "correct":  correct,
        "entered":  entered,
        "expected": expected,
        "state":    svc.get_state(),
    })