"""YOLOv8 person detector running on the Hailo-8L NPU (v1 adapter)."""
from __future__ import annotations

import numpy as np

from edgesentry.config import Config
from edgesentry.perception import Detection


class Detector:
    def __init__(self, cfg: Config) -> None:
        self.hef_path = cfg.perception.detector_hef
        self.conf = cfg.perception.confidence_threshold
        # TODO(v1): load the .hef and create the Hailo inference pipeline,
        # exactly as in the Pi5 Edge AI Security Monitor.

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """Run YOLOv8 on the NPU and return person detections."""
        # TODO(v1): run inference, filter to the 'person' class above self.conf,
        # and wrap each result in a Detection(bbox=..., confidence=...).
        raise NotImplementedError("Port v1 YOLOv8/Hailo inference into Detector.detect().")
