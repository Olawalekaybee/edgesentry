"""ResNet-based person re-identification on the Hailo-8L NPU (v1 adapter).

Assigns a stable `person_id` to each detection by comparing its ReID embedding
against a short-lived gallery of recently seen people. This is what lets the
agent answer questions like "has the same person shown up more than twice?".
"""
from __future__ import annotations

import numpy as np

from edgesentry.config import Config
from edgesentry.perception import Detection


class ReID:
    def __init__(self, cfg: Config) -> None:
        self.hef_path = cfg.perception.reid_hef
        # TODO(v1): load the ReID .hef. Keep an in-memory gallery of recent
        # {person_id: embedding} to match against (cosine similarity).

    def annotate(self, frame: np.ndarray, detections: list[Detection]) -> list[Detection]:
        """Fill `person_id` and `embedding` on each detection."""
        # TODO(v1): for each detection, crop the bbox, run the ReID model on the
        # NPU, match against the gallery, and set person_id + embedding.
        raise NotImplementedError("Port v1 ReID into ReID.annotate().")
