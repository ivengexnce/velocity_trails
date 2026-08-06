"""
Velocity Trails - Air Writer
============================

Standalone webcam test.

Run from Backend:

    py -3.11 test_air_writer.py

Draw:
    A-Z
    0-9

Controls:
    INDEX ONLY     -> draw
    FIST           -> commit
    OPEN PALM      -> clear
    THUMB ONLY     -> confirm
    Q / ESC        -> quit
"""

import base64
import cv2

# IMPORTANT:
# air_writer.py is inside Backend/services/
from services.air_writer import get_air_writer


WINDOW = "Velocity Trails - Air Writer"


def frame_to_base64(frame):
    """Convert OpenCV frame to JPEG base64."""

    ok, encoded = cv2.imencode(
        ".jpg",
        frame,
        [
            cv2.IMWRITE_JPEG_QUALITY,
            90,
        ],
    )

    if not ok:
        return None

    return base64.b64encode(
        encoded.tobytes()
    ).decode("utf-8")


def draw_trail(frame, trail):
    """Draw the detected air-writing trail."""

    if len(trail) < 2:
        return

    for i in range(1, len(trail)):
        cv2.line(
            frame,
            trail[i - 1],
            trail[i],
            (0, 255, 0),
            5,
            cv2.LINE_AA,
        )

    x, y = trail[-1]

    cv2.circle(
        frame,
        (x, y),
        10,
        (0, 0, 255),
        -1,
        cv2.LINE_AA,
    )


def draw_text(
    frame,
    text,
    position,
    scale=0.65,
    thickness=2,
):
    """Draw readable text on the webcam window."""

    cv2.putText(
        frame,
        str(text),
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )


def main():

    print("=" * 70)
    print("VELOCITY TRAILS - AIR WRITER")
    print("A-Z + 0-9 WEBCAM RECOGNITION TEST")
    print("=" * 70)

    print()
    print("Controls:")
    print("  Index finger only -> DRAW")
    print("  Fist              -> COMMIT")
    print("  Open palm         -> CLEAR")
    print("  Thumb only        -> CONFIRM")
    print("  Q / ESC           -> QUIT")
    print()

    print("For best accuracy:")
    print("  * Keep your whole character inside the box.")
    print("  * Draw slowly and clearly.")
    print("  * Use large characters.")
    print("  * Keep your hand inside camera view.")
    print("  * Hold the fist briefly after drawing.")
    print()

    # --------------------------------------------------------
    # Initialize Air Writer service
    # --------------------------------------------------------

    try:

        writer = get_air_writer()

    except Exception as exc:

        print()
        print("ERROR: Could not initialize Air Writer.")
        print()
        print(exc)
        print()

        return

    writer.start_session(
        code_length=20
    )

    # --------------------------------------------------------
    # Open webcam
    # --------------------------------------------------------

    camera = cv2.VideoCapture(
        0,
        cv2.CAP_DSHOW,
    )

    if not camera.isOpened():

        print()
        print("ERROR: Camera could not be opened.")
        print()

        try:
            writer.close()
        except Exception:
            pass

        return

    # --------------------------------------------------------
    # Camera configuration
    # --------------------------------------------------------

    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        1280,
    )

    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        720,
    )

    camera.set(
        cv2.CAP_PROP_FPS,
        30,
    )

    print("Webcam started.")
    print("Draw a character.")
    print()

    try:

        while True:

            # ------------------------------------------------
            # Read webcam
            # ------------------------------------------------

            ok, frame = camera.read()

            if not ok:

                print(
                    "ERROR: Could not read frame."
                )

                break

            # ------------------------------------------------
            # Mirror webcam
            # ------------------------------------------------

            display = cv2.flip(
                frame,
                1,
            )

            # IMPORTANT:
            # Send exactly the same mirrored frame
            # that the user sees.
            service_frame = display

            # ------------------------------------------------
            # Convert frame to base64
            # ------------------------------------------------

            encoded = frame_to_base64(
                service_frame
            )

            if encoded is None:
                continue

            # ------------------------------------------------
            # Process through Air Writer
            # ------------------------------------------------

            try:

                state = writer.process_frame(
                    encoded,
                    frame_wh=(
                        service_frame.shape[1],
                        service_frame.shape[0],
                    ),
                )

            except Exception as exc:

                print(
                    "Processing error:",
                    exc,
                )

                continue

            # ------------------------------------------------
            # Get drawing trail
            # ------------------------------------------------

            try:

                trail = writer.get_trail_pixels()

            except Exception:

                trail = []

            draw_trail(
                display,
                trail,
            )

            h, w = display.shape[:2]

            # ------------------------------------------------
            # Drawing area
            # ------------------------------------------------

            margin = 120

            cv2.rectangle(
                display,
                (
                    margin,
                    150,
                ),
                (
                    w - margin,
                    h - 100,
                ),
                (255, 255, 255),
                2,
            )

            # ------------------------------------------------
            # Top panel
            # ------------------------------------------------

            cv2.rectangle(
                display,
                (0, 0),
                (w, 135),
                (20, 20, 20),
                -1,
            )

            # ------------------------------------------------
            # Recognition information
            # ------------------------------------------------

            character = state.get(
                "character",
                None,
            )

            try:

                confidence = float(
                    state.get(
                        "confidence",
                        0.0,
                    )
                )

            except (TypeError, ValueError):

                confidence = 0.0

            try:

                margin_score = float(
                    state.get(
                        "margin",
                        0.0,
                    )
                )

            except (TypeError, ValueError):

                margin_score = 0.0

            mode = state.get(
                "mode",
                "idle",
            )

            status = state.get(
                "status",
                "READY",
            )

            code_buffer = state.get(
                "code_buffer",
                [],
            )

            if not isinstance(
                code_buffer,
                (list, tuple),
            ):

                code_buffer = []

            buffer = "".join(
                str(x)
                for x in code_buffer
            )

            if not buffer:
                buffer = "—"

            # ------------------------------------------------
            # Header
            # ------------------------------------------------

            draw_text(
                display,
                "AIR WRITER | A-Z + 0-9",
                (20, 32),
                0.75,
                2,
            )

            draw_text(
                display,
                f"MODE: {str(mode).upper()}",
                (20, 68),
                0.62,
                2,
            )

            draw_text(
                display,
                f"CODE: {buffer}",
                (20, 105),
                0.72,
                2,
            )

            # ------------------------------------------------
            # Recognition panel
            # ------------------------------------------------

            result_text = (
                str(character)
                if character
                else "—"
            )

            draw_text(
                display,
                f"RESULT: {result_text}",
                (w - 350, 38),
                0.72,
                2,
            )

            draw_text(
                display,
                f"CONF: {confidence:.1%}",
                (w - 350, 72),
                0.60,
                2,
            )

            draw_text(
                display,
                f"MARGIN: {margin_score:.3f}",
                (w - 350, 103),
                0.55,
                1,
            )

            # ------------------------------------------------
            # Status bar
            # ------------------------------------------------

            cv2.rectangle(
                display,
                (20, h - 82),
                (w - 20, h - 45),
                (20, 20, 20),
                -1,
            )

            draw_text(
                display,
                status,
                (30, h - 55),
                0.52,
                1,
            )

            draw_text(
                display,
                "INDEX=DRAW | FIST=COMMIT | PALM=CLEAR | "
                "THUMB=CONFIRM | Q=QUIT",
                (30, h - 18),
                0.43,
                1,
            )

            # ------------------------------------------------
            # Trail information
            # ------------------------------------------------

            draw_text(
                display,
                f"POINTS: {len(trail)}",
                (w - 190, h - 55),
                0.48,
                1,
            )

            # ------------------------------------------------
            # Display webcam
            # ------------------------------------------------

            cv2.imshow(
                WINDOW,
                display,
            )

            # ------------------------------------------------
            # Keyboard
            # ------------------------------------------------

            key = cv2.waitKey(1) & 0xFF

            if key in (
                ord("q"),
                ord("Q"),
                27,
            ):

                break

    except KeyboardInterrupt:

        print()
        print("Interrupted.")

    finally:

        print()
        print("Closing camera...")

        camera.release()

        try:
            writer.close()
        except Exception:
            pass

        cv2.destroyAllWindows()

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("TEST FINISHED")
    print("=" * 70)

    try:

        final_buffer = "".join(
            str(x)
            for x in writer.code_buffer
        )

    except Exception:

        final_buffer = ""

    print(
        "Final buffer:",
        final_buffer,
    )


if __name__ == "__main__":
    main()
