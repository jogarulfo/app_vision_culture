import cv2
from typing import Iterator, Optional


class CameraStream:
    """Capture frames from webcam (default) or a video file.

    Usage:
        stream = CameraStream(src=0)  # webcam
        for frame in stream.frames():
            # process frame
    """

    def __init__(self, src: Optional[str | int] = 0, width: int = 640, height: int = 480):
        self.src = src
        self.width = width
        self.height = height
        self.cap = None

    def __enter__(self):
        self.cap = cv2.VideoCapture(self.src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.cap is not None:
            self.cap.release()

    def frames(self) -> Iterator:
        """Yield frames from the source until exhausted.

        Yields OpenCV BGR frames.
        """
        with self:
            if not self.cap or not self.cap.isOpened():
                raise RuntimeError(f"Unable to open video source: {self.src}")
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break
                yield frame


if __name__ == "__main__":
    cam = CameraStream(src="data/video_chateau.mp4")
    print(cam)
    cam = cam.__enter__()
    print("Starting frame capture. Press 'q' to quit.")
    for i, frame in enumerate(cam.frames()):
        cv2.imshow("Frame", frame)
        if cv2.waitKey(30) & 0xFF == ord("q"):
            break
    cam.__exit__(None, None, None)
    cv2.destroyAllWindows()
