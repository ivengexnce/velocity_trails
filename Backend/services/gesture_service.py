"""
gesture_service.py – Velocity Trials · Level 1
================================================
Single-hand gesture recognition via MediaPipe.
Converts held hand poses into digit inputs for secret code entry.

Gesture Map  (Thumb | Index | Middle | Ring | Pinky)
─────────────────────────────────────────────────────
  0  →  F F F F F   fist
  1  →  F T F F F   index only
  2  →  F T T F F   peace sign
  3  →  F T T T F
  4  →  F T T T T   four fingers, no thumb
  5  →  T T T T T   open hand
  6  →  T F F F T   shaka
  7  →  T T T F F
  8  →  T T F F F
  9  →  T F F F F   thumb only

CONFIRM   →  F T F F T   index + pinky  (rock-on)
BACKSPACE →  F F F F T   pinky only

Hold any gesture for `hold_duration` seconds to register it.
A short cooldown prevents double-triggers while the hand stays still.
"""

from __future__ import annotations

import base64
import time
from typing import Optional

import cv2
# pyrefly: ignore [missing-import]
import mediapipe as mp
import numpy as np


# ── Gesture → symbol lookup ──────────────────────────────────────────────────

_GESTURE_MAP: dict[tuple[bool, ...], str] = {
    # Digits
    (False, False, False, False, False): "0",
    (False, True,  False, False, False): "1",
    (False, True,  True,  False, False): "2",
    (False, True,  True,  True,  False): "3",
    (False, True,  True,  True,  True ): "4",
    (True,  True,  True,  True,  True ): "5",
    (True,  False, False, False, True ): "6",
    (True,  True,  True,  False, False): "7",
    (True,  True,  False, False, False): "8",
    (True,  False, False, False, False): "9",
    # Special actions  (no overlap with digits)
    (False, True,  False, False, True ): "CONFIRM",    # index + pinky
    (False, False, False, False, True ): "BACKSPACE",  # pinky only
}


# ── Core service class ────────────────────────────────────────────────────────

class GestureService:
    """
    Stateful gesture recognition engine.

    Lifecycle
    ---------
    1. Call `start_session()` before a player begins code entry.
    2. Feed webcam frames via `process_frame(frame_b64)` in a loop.
    3. The frontend polls the returned `hold_progress` (0.0 → 1.0) to
       animate a fill ring around the detected gesture label.
    4. When `registered == "CONFIRM"` the session closes; call `validate()`
       with the expected code to check correctness.
    5. Call `close()` on app teardown to free MediaPipe resources.
    """

    def __init__(
        self,
        hold_duration: float = 1.2,   # seconds a pose must be held to register
        cooldown: float = 0.8,        # seconds between consecutive registrations
        max_code_length: int = 6,
    ) -> None:
        self.hold_duration = hold_duration
        self.cooldown = cooldown
        self.max_code_length = max_code_length

        # MediaPipe hands (single-hand, tracking mode)
        _mp = mp.solutions.hands
        self._hands = _mp.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.75,
        )

        # Session state
        self.session_active: bool = False
        self.code_buffer: list[str] = []

        # Hold-detection state machine
        self._current_pose: Optional[str] = None
        self._pose_start: float = 0.0
        self._last_register: float = 0.0

    # ── Public API ────────────────────────────────────────────────────────────

    def start_session(self, code_length: Optional[int] = None) -> None:
        """Reset all state and open a new code-entry session."""
        self.code_buffer.clear()
        self._current_pose = None
        self._pose_start = 0.0
        self._last_register = 0.0
        self.session_active = True
        if code_length is not None:
            self.max_code_length = code_length

    def end_session(self) -> None:
        """Close the session without clearing the buffer (needed for validation)."""
        self.session_active = False

    def backspace(self) -> None:
        """Remove the last entered digit."""
        if self.code_buffer:
            self.code_buffer.pop()

    def clear_buffer(self) -> None:
        """Wipe all entered digits and reset hold state."""
        self.code_buffer.clear()
        self._current_pose = None
        self._pose_start = 0.0

    def validate(self, expected: str) -> bool:
        """Return True if the entered code matches the expected secret code."""
        return "".join(self.code_buffer) == expected.strip()

    def get_state(self) -> dict:
        """Serialisable snapshot of the current session state."""
        return {
            "session_active": self.session_active,
            "code_buffer": list(self.code_buffer),
            "buffer_display": " ".join(self.code_buffer) if self.code_buffer else "—",
            "buffer_length": len(self.code_buffer),
            "max_length": self.max_code_length,
        }

    def process_frame(self, frame_b64: str) -> dict:
        """
        Decode one base64-encoded JPEG/PNG webcam frame, run hand detection,
        and advance the hold-timer state machine.

        Returns
        -------
        dict with keys:
            session_active   bool
            code_buffer      list[str]
            buffer_display   str
            buffer_length    int
            max_length       int
            detected         str | None   – pose label this frame
            registered       str | None   – symbol that just committed (digit / CONFIRM / BACKSPACE)
            hold_progress    float 0–1    – how far through the hold threshold
            error            str | None
        """
        if not self.session_active:
            return {
                **self.get_state(),
                "detected": None,
                "registered": None,
                "hold_progress": 0.0,
                "error": "no_active_session",
            }

        frame = self._decode_frame(frame_b64)
        if frame is None:
            return {
                **self.get_state(),
                "detected": None,
                "registered": None,
                "hold_progress": 0.0,
                "error": "invalid_frame",
            }

        detected = self._detect_pose(frame)
        now = time.monotonic()
        registered: Optional[str] = None
        hold_progress: float = 0.0

        if detected and detected == self._current_pose:
            elapsed = now - self._pose_start
            hold_progress = min(elapsed / self.hold_duration, 1.0)

            if (elapsed >= self.hold_duration
                    and (now - self._last_register) >= self.cooldown):
                registered = self._commit(detected, now)

        else:
            # Pose changed → reset hold timer
            self._current_pose = detected
            self._pose_start = now if detected else 0.0

        return {
            **self.get_state(),
            "detected": detected,
            "registered": registered,
            "hold_progress": round(hold_progress, 3),
            "error": None,
        }

    def close(self) -> None:
        """Release MediaPipe resources. Call once on app teardown."""
        self._hands.close()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _decode_frame(self, frame_b64: str) -> Optional[np.ndarray]:
        """Base64 string → OpenCV BGR array, or None on failure."""
        try:
            raw = base64.b64decode(frame_b64)
            arr = np.frombuffer(raw, dtype=np.uint8)
            return cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except Exception:
            return None

    def _detect_pose(self, frame: np.ndarray) -> Optional[str]:
        """
        Run MediaPipe on one frame and return the matching gesture label,
        or None if no hand is visible or the pose is unrecognised.

        The frame is flipped horizontally before processing so that
        handedness labels are correct for a mirrored webcam feed.
        """
        rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        result = self._hands.process(rgb)

        if not result.multi_hand_landmarks:
            return None

        landmarks = result.multi_hand_landmarks[0]
        handedness = (
            result.multi_handedness[0].classification[0].label
            if result.multi_handedness
            else "Right"
        )

        states = _finger_states(landmarks.landmark, handedness)
        return _GESTURE_MAP.get(states)

    def _commit(self, gesture: str, now: float) -> Optional[str]:
        """
        Persist a fully-held gesture into the buffer or trigger an action.
        Resets the pose start time so the gesture must be released before
        it can trigger again.
        """
        self._last_register = now
        self._pose_start = now  # require a fresh hold to re-trigger

        if gesture == "CONFIRM":
            self.end_session()
            return "CONFIRM"

        if gesture == "BACKSPACE":
            self.backspace()
            return "BACKSPACE"

        if gesture.isdigit() and len(self.code_buffer) < self.max_code_length:
            self.code_buffer.append(gesture)
            return gesture

        return None  # buffer full or unknown symbol


# ── Finger-state extraction (module-level, no 'self' needed) ─────────────────

def _finger_states(
    lm,
    handedness: str,
) -> tuple[bool, bool, bool, bool, bool]:
    """
    Return (thumb, index, middle, ring, pinky) — True means extended.

    Thumb uses x-axis comparison (handedness-aware).
    Other fingers use y-axis: tip above PIP joint → extended.
    """
    # Thumb lateral extension
    if handedness == "Right":
        thumb = lm[4].x > lm[3].x   # tip further right than IP
    else:
        thumb = lm[4].x < lm[3].x   # tip further left than IP

    # Remaining fingers
    index  = lm[8].y  < lm[6].y
    middle = lm[12].y < lm[10].y
    ring   = lm[16].y < lm[14].y
    pinky  = lm[20].y < lm[18].y

    return (thumb, index, middle, ring, pinky)


# ── Process-level singleton ───────────────────────────────────────────────────

_instance: Optional[GestureService] = None


def get_gesture_service() -> GestureService:
    """Return (or create) the shared GestureService instance."""
    global _instance
    if _instance is None:
        _instance = GestureService()
    return _instance