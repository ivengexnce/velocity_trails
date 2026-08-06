"""
test_gesture.py – Velocity Trials
===================================
Standalone gesture test. No Flask needed.
Run from the Backend/ folder:

    cd Backend
    python test_gesture.py

Controls (keyboard while window is focused):
    B  – backspace
    C  – clear buffer
    R  – restart session
    Q  – quit
"""

import base64
import sys
import os

import cv2

# ── Path fix so "services" resolves when run from Backend/ ────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from services.gesture_service import GestureService


# ── Config ────────────────────────────────────────────────────────────────────
TEST_CODE     = "1234"   # change to whatever secret code you want to test
HOLD_DURATION = 1.2      # seconds to hold a gesture
MAX_LENGTH    = len(TEST_CODE)
CAMERA_INDEX  = 0        # 0 = default webcam; try 1 if laptop camera isn't detected


# ── Helpers ───────────────────────────────────────────────────────────────────

def frame_to_b64(frame) -> str:
    """Encode an OpenCV frame as a base64 JPEG string (same path as production)."""
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return base64.b64encode(buf).decode("utf-8")


def draw_progress_bar(frame, x, y, w, h, progress, color=(0, 200, 255)):
    cv2.rectangle(frame, (x, y), (x + w, y + h), (50, 50, 50), -1)
    filled = int(w * progress)
    if filled > 0:
        cv2.rectangle(frame, (x, y), (x + filled, y + h), color, -1)


def overlay(frame, result, validated, correct):
    h, w = frame.shape[:2]
    pad = 20

    detected   = result.get("detected") or "—"
    progress   = result.get("hold_progress", 0.0)
    registered = result.get("registered")
    buf_display = result.get("buffer_display", "—")
    buf_len    = result.get("buffer_length", 0)
    max_len    = result.get("max_length", MAX_LENGTH)

    # Semi-transparent top banner
    banner = frame.copy()
    cv2.rectangle(banner, (0, 0), (w, 170), (20, 20, 20), -1)
    cv2.addWeighted(banner, 0.6, frame, 0.4, 0, frame)

    # Detected gesture
    cv2.putText(frame, f"Detected : {detected}",
                (pad, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Hold progress bar
    draw_progress_bar(frame, pad, 55, w - pad * 2, 18, progress)
    pct = int(progress * 100)
    cv2.putText(frame, f"Hold {pct}%",
                (pad, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

    # Code buffer
    cv2.putText(frame, f"Code [{buf_len}/{max_len}] : {buf_display}",
                (pad, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 220, 0), 2)

    # Flash "Registered" briefly
    if registered:
        cv2.putText(frame, f">>> {registered} <<<",
                    (pad, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    # Bottom status
    if validated:
        msg   = "CORRECT  — Press R to restart" if correct else "WRONG  — Press R to restart"
        color = (0, 230, 0) if correct else (0, 0, 230)
        cv2.rectangle(frame, (0, h - 55), (w, h), (20, 20, 20), -1)
        cv2.putText(frame, msg, (pad, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85, color, 2)
    else:
        hint = "B=backspace  C=clear  R=restart  Q=quit"
        cv2.putText(frame, hint, (pad, h - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (160, 160, 160), 1)


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    svc = GestureService(hold_duration=HOLD_DURATION, max_code_length=MAX_LENGTH)
    svc.start_session()

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"ERROR: Cannot open camera index {CAMERA_INDEX}. "
              "Try changing CAMERA_INDEX at the top of the script.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print(f"\nGesture Test Running")
    print(f"Secret code to enter: {TEST_CODE}")
    print("Hold each gesture for 1.2 s to register it.")
    print("CONFIRM gesture (index + pinky) submits the code.\n")

    validated = False
    correct   = False
    last_registered = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("ERROR: Lost camera feed.")
            break

        result = {"detected": None, "registered": None,
                  "hold_progress": 0.0, "buffer_display": "—",
                  "buffer_length": 0, "max_length": MAX_LENGTH}

        if svc.session_active:
            b64    = frame_to_b64(frame)
            result = svc.process_frame(b64)

            reg = result.get("registered")
            if reg and reg != last_registered:
                last_registered = reg
                print(f"  Registered: {reg}  →  buffer: {''.join(svc.code_buffer)}")

            if reg == "CONFIRM":
                correct   = svc.validate(TEST_CODE)
                validated = True
                entered   = "".join(svc.code_buffer)
                print(f"\nCONFIRM received.")
                print(f"  Entered : {entered}")
                print(f"  Expected: {TEST_CODE}")
                print(f"  Result  : {'✓ CORRECT' if correct else '✗ WRONG'}\n")

        overlay(frame, result, validated, correct)
        cv2.imshow("Velocity Trials – Gesture Test", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        elif key == ord("b"):
            svc.backspace()
            last_registered = None
            print(f"  Backspace  →  buffer: {''.join(svc.code_buffer)}")

        elif key == ord("c"):
            svc.clear_buffer()
            last_registered = None
            validated = False
            print("  Buffer cleared.")

        elif key == ord("r"):
            svc.start_session()
            last_registered = None
            validated = False
            correct   = False
            print("  Session restarted.")

    cap.release()
    cv2.destroyAllWindows()
    svc.close()
    print("Done.")


if __name__ == "__main__":
    main()
