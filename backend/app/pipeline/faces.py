"""Face detection (RetinaFace) + recognition (ArcFace) via InsightFace.

NOTE: InsightFace pretrained model packs are research-only. Swap in a
commercially licensed recogniser before any paid deployment.
"""
import numpy as np

_app = None
MATCH_THRESHOLD = 0.40  # cosine similarity; calibrate on your own hall data


def _get_app():
    global _app
    if _app is None:
        from insightface.app import FaceAnalysis
        _app = FaceAnalysis(name="buffalo_l", providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
        _app.prepare(ctx_id=0, det_size=(640, 640))
    return _app


def embed_faces(images) -> np.ndarray | None:
    app, embs = _get_app(), []
    for img in images:
        faces = app.get(img)
        if faces:
            biggest = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            embs.append(biggest.normed_embedding)
    if not embs:
        return None
    mean = np.mean(embs, axis=0)
    return mean / np.linalg.norm(mean)


def best_match(query: np.ndarray, gallery: dict[int, np.ndarray]):
    """Return (student_id, similarity) or (None, sim) if below threshold."""
    best_id, best_sim = None, -1.0
    for sid, emb in gallery.items():
        sim = float(np.dot(query, emb))
        if sim > best_sim:
            best_id, best_sim = sid, sim
    return (best_id if best_sim >= MATCH_THRESHOLD else None), best_sim
