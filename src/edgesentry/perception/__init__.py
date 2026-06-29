"""Perception layer — the v1 vision pipeline running on the Hailo-8L NPU.

This package is a thin adapter around your existing **Pi5 Edge AI Security
Monitor** code (YOLOv8 detection + ResNet re-identification + polygon zones).
The rest of EdgeSentry never imports Hailo directly — it only depends on the
plain `Detection` dataclass defined here. That single contract is what keeps the
v2 layers (events / rag / agent) testable without any NPU attached.

If your v1 lives in a separate repo, import it inside these adapters. If you fold
v1 into this repo, drop its modules in here and have the adapters call them.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Detection:
    """One detected person in one frame — the contract between vision and v2.

    Coordinates are pixel values in the camera frame. `person_id` comes from the
    ReID model and is what lets the agent answer "has the same person appeared
    before?". `zone` is filled by ZoneMap; both may be None before annotation.
    """

    bbox: tuple[int, int, int, int]          # (x1, y1, x2, y2)
    confidence: float
    person_id: str | None = None             # set by ReID
    zone: str | None = None                  # set by ZoneMap
    embedding: list[float] | None = field(default=None, repr=False)  # ReID vector

    @property
    def foot_point(self) -> tuple[int, int]:
        """Bottom-centre of the bbox — used for zone containment tests."""
        x1, _, x2, y2 = self.bbox
        return ((x1 + x2) // 2, y2)
