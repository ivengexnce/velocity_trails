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


WINDOW = "Velocity Trails - Air Writer"


def frame_to_base64(frame):

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


def draw_trail(
    frame,
    trail
):

    if len(trail) < 2:
        return

    for i in range(
        1,
        len(trail)
    ):

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

    writer = get_air_writer()

    writer.start_session(
        code_length=20
    )

    camera = cv2.VideoCapture(
        0,
        cv2.CAP_DSHOW
    )

    if not camera.isOpened():

        print("ERROR: Camera could not be opened.")

        writer.close()

        return

    # Camera configuration.
    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        1280
    )

    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        720
    )

    camera.set(
        cv2.CAP_PROP_FPS,
        30
    )

    print("Webcam started.")
    print("Draw a character.")
    print()

    try:

        while True:

            ok, frame = camera.read()

            if not ok:

                print(
                    "ERROR: Could not read frame."
                )

                break

            # Mirror display so movement feels natural.
            display = cv2.flip(
                frame,
                1
            )

            # IMPORTANT:
            # The service receives the same mirrored image
            # that the user sees.
            service_frame = display

            encoded = frame_to_base64(
                service_frame
            )

            if encoded is None:
                continue

            state = writer.process_frame(
                encoded,
                frame_wh=(
                    service_frame.shape[1],
                    service_frame.shape[0],
                ),
            )

            # ------------------------------------------------
            # Trail
            # ------------------------------------------------

            trail = (
                writer.get_trail_pixels()
            )

            draw_trail(
                display,
                trail
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
                    150
                ),
                (
                    w - margin,
                    h - 100
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

            character = (
                state.get(
                    "character"
                )
            )

            confidence = float(
                state.get(
                    "confidence",
                    0.0
                )
            )

            margin_score = float(
                state.get(
                    "margin",
                    0.0
                )
            )

            mode = state.get(
                "mode",
                "idle"
            )

            status = state.get(
                "status",
                "READY"
            )

            buffer = "".join(
                state.get(
                    "code_buffer",
                    []
                )
            )

            if not buffer:
                buffer = "—"

            # ------------------------------------------------
            # Header
            # ------------------------------------------------

            draw_text(
                display,
                "AIR WRITER  |  A-Z + 0-9",
                (20, 32),
                0.75,
                2,
            )

            draw_text(
                display,
                f"MODE: {mode.upper()}",
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
                character
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
            # Status
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
                "INDEX=DRAW   FIST=COMMIT   PALM=CLEAR   THUMB=CONFIRM   Q=QUIT",
                (30, h - 18),
                0.43,
                1,
            )

            # ------------------------------------------------
            # Trail info
            # ------------------------------------------------

            draw_text(
                display,
                f"POINTS: {len(trail)}",
                (w - 190, h - 55),
                0.48,
                1,
            )

            cv2.imshow(
                WINDOW,
                display
            )

            key = (
                cv2.waitKey(1)
                & 0xFF
            )

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

        camera.release()

        writer.close()

        cv2.destroyAllWindows()

    print()
    print("=" * 70)
    print("TEST FINISHED")
    print("=" * 70)

    print(
        "Final buffer:",
        "".join(
            writer.code_buffer
        )
    )


if __name__ == "__main__":
    main()