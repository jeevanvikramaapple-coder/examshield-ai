"""Gadget detector wrapper + persistence gate.

The detector itself (YOLOv8 trained on seat crops at imgsz 1280; classes:
phone, calculator, smartwatch, paper_slip, earbud) is one of only two
components that consume labelled data. Weights live outside git: set
GADGET_WEIGHTS to the exported .pt / .onnx file.

A gadget only counts once it is seen in >= `min_hits` of the last `window`
frames, which suppresses single-frame false positives on pens and wallets.
"""
import os
from collections import defaultdict, deque

CLASSES = ["phone", "calculator", "smartwatch", "paper_slip", "earbud"]


class GadgetDetector:
    def __init__(self, weights: str | None = None, conf: float = 0.4):
        self.conf = conf
        self.model = None
        weights = weights or os.getenv("GADGET_WEIGHTS")
        if weights and os.path.exists(weights):
            from ultralytics import YOLO  # imported lazily: heavy, AGPL
            self.model = YOLO(weights)

    def detect(self, crop):
        """Return a list of (class_name, confidence) for a seat crop (BGR ndarray)."""
        if self.model is None:
            return []
        res = self.model.predict(crop, imgsz=1280, conf=self.conf, verbose=False)[0]
        return [(res.names[int(b.cls)], float(b.conf)) for b in res.boxes]


class PersistenceGate:
    def __init__(self, window: int = 12, min_hits: int = 4):
        self.window, self.min_hits = window, min_hits
        self.history: dict[tuple, deque] = defaultdict(lambda: deque(maxlen=window))

    def update(self, track_id: int, detections: list[tuple[str, float]]) -> float:
        """Returns gadget_persistence in [0,1] for the scoring engine."""
        seen = {c for c, _ in detections}
        best = 0.0
        for cls in CLASSES:
            h = self.history[(track_id, cls)]
            h.append(1 if cls in seen else 0)
            hits = sum(h)
            if hits >= self.min_hits:
                best = max(best, min(1.0, hits / self.window * 2))
        return best
