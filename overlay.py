import cv2


def draw_overlay(frame, text: str, score: float = None):
    """Draw a simple overlay with the monument name and optional score.

    Currently places text in the top-left corner.
    """
    h, w = frame.shape[:2]
    # rectangle background
    overlay_h = 60
    cv2.rectangle(frame, (0, 0), (w, overlay_h), (0, 0, 0), thickness=-1)

    title = text
    if score is not None:
        title = f"{text} ({score:.2f})"

    cv2.putText(frame, title, (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)

    return frame
