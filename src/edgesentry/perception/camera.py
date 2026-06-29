"""Camera capture adapter.

Wraps your v1 camera code. On the Pi this is PiCamera2; for development it can
fall back to an OpenCV VideoCapture (USB webcam or video file). Yields frames as
numpy BGR arrays.
"""
from __future__ import annotations

from collections.abc import Iterator

import numpy as np

from edgesentry.config import Config


class Camera:
    def __init__(self, cfg: Config) -> None:
        self.source = cfg.perception.camera_source
        # TODO(v1): initialise PiCamera2 (hardware) or cv2.VideoCapture (dev),
        # exactly as in the Pi5 Edge AI Security Monitor.

    def frames(self) -> Iterator[np.ndarray]:
        """Yield camera frames forever as BGR numpy arrays."""
        # TODO(v1): port the capture loop from v1 here.
        raise NotImplementedError("Port v1 camera capture into Camera.frames().")
