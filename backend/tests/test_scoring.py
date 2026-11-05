import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.pipeline.gadgets import PersistenceGate  # noqa: E402
from app.pipeline.scoring import Hysteresis, score_features  # noqa: E402


def test_clean_candidate_is_low():
    assert score_features({}).band == "low"


def test_gadget_alone_reaches_review():
    r = score_features({"gadget_persistence": 1.0, "gaze_off_paper": 0.5})
    assert r.band == "review" and r.reasons[0].startswith("gadget_persistence")


def test_many_signals_high():
    r = score_features({k: 1.0 for k in
                        ["gadget_persistence", "head_yaw_sideways", "gaze_off_paper", "hand_below_desk"]})
    assert r.band == "high"


def test_values_clamped():
    assert score_features({"gadget_persistence": 9}).score <= 1.0


def test_hysteresis_does_not_flap():
    h = Hysteresis(raise_at=0.5, clear_at=0.3)
    assert [h.update(s) for s in (0.4, 0.55, 0.4, 0.2)] == [False, True, True, False]


def test_persistence_gate_ignores_single_frame():
    g = PersistenceGate(window=12, min_hits=4)
    assert g.update(1, [("phone", 0.9)]) == 0.0
    for _ in range(3):
        v = g.update(1, [("phone", 0.9)])
    assert v > 0
