"""Per-camera processing loop wiring the stages together.

Stages: frame -> YOLOv8 person detection -> ByteTrack -> seat binding ->
RetinaFace + InsightFace identity -> MediaPipe pose/gaze/hands -> gadget
detection -> windowed features -> risk score -> alert + evidence clip.

Heavy models load lazily so the API and tests run on a laptop without a GPU.
Run on the inference host:  python -m app.pipeline.runner rtsp://... --session 1
"""
import argparse
import os
import time

import cv2
import httpx

from .gadgets import GadgetDetector, PersistenceGate
from .scoring import Hysteresis, score_features


def run(source: str, session_id: int, api: str, token: str, person_weights: str = "yolov8n.pt"):
    from ultralytics import YOLO  # AGPL-3.0: see README licence notes

    person_model = YOLO(person_weights)
    gadgets, gate = GadgetDetector(), PersistenceGate()
    states: dict[int, Hysteresis] = {}
    cap = cv2.VideoCapture(source)
    headers = {"Authorization": f"Bearer {token}"}
    os.makedirs("evidence", exist_ok=True)

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        results = person_model.track(frame, persist=True, classes=[0],
                                     tracker="bytetrack.yaml", verbose=False)[0]
        if results.boxes.id is None:
            continue
        for box, tid in zip(results.boxes.xyxy.cpu().numpy(), results.boxes.id.int().tolist()):
            x1, y1, x2, y2 = map(int, box)
            crop = frame[max(y1, 0):y2, max(x1, 0):x2]
            if crop.size == 0:
                continue
            feats = {"gadget_persistence": gate.update(tid, gadgets.detect(crop))}
            # TODO(wire): gaze_off_paper, head_yaw_sideways, hand_below_desk from
            # headpose.NeutralPose + MediaPipe once those modules pass acceptance.
            risk = score_features(feats)
            if states.setdefault(tid, Hysteresis()).update(risk.score):
                path = f"evidence/s{session_id}_t{tid}_{int(time.time())}.jpg"
                cv2.imwrite(path, crop)
                httpx.post(f"{api}/alerts", headers=headers, timeout=5, json={
                    "session_id": session_id, "features": feats, "evidence_path": path})


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("source")
    p.add_argument("--session", type=int, required=True)
    p.add_argument("--api", default="http://localhost:8000")
    p.add_argument("--token", default=os.getenv("API_TOKEN", ""))
    a = p.parse_args()
    run(a.source, a.session, a.api, a.token)
