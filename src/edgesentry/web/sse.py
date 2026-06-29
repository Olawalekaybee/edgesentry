"""Server-Sent Events live feed (reused/adapted from v1).

v1 already streams the annotated camera feed and live detections to the
dashboard. Port that generator here and wire it to a /stream route in routes.py.
Kept as a stub so the v2 layers stay runnable without the camera.
"""
from __future__ import annotations

from collections.abc import Iterator


def event_stream() -> Iterator[str]:
    """Yield SSE-formatted strings: 'data: {...}\\n\\n'."""
    # TODO(v1): port the v1 SSE generator (live detections / MJPEG metadata).
    raise NotImplementedError("Port v1 SSE generator into event_stream().")
