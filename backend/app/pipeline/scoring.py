"""Behaviour scoring engine and risk bands.

Features are per-candidate, per-window values in [0, 1] produced by the
vision modules. The weights below are a transparent starting point; once a
shadow session has been labelled, refit them (logistic regression) and
replace WEIGHTS - the interface does not change.

Product metric: false alerts per invigilator-hour (target < 0.5), not accuracy.
"""
from dataclasses import dataclass

WEIGHTS: dict[str, float] = {
    "gaze_off_paper": 0.15,        # fraction of window eyes are off own paper
    "head_yaw_sideways": 0.15,     # sustained yaw towards a neighbour (vs own neutral pose)
    "head_turn_frequency": 0.08,   # repeated turns per minute, normalised
    "gadget_persistence": 0.45,    # gadget seen in >= 4 of 12 frames
    "hand_below_desk": 0.07,
    "neighbour_proximity": 0.05,   # leaning/looking towards adjacent seat
    "speech_detected": 0.05,       # Silero VAD, only if audio is deployed
}

REVIEW_THRESHOLD = 0.45
HIGH_THRESHOLD = 0.70


@dataclass
class RiskResult:
    score: float
    band: str          # low | review | high
    reasons: list[str]


def score_features(features: dict[str, float]) -> RiskResult:
    total, contributions = 0.0, []
    for name, weight in WEIGHTS.items():
        value = min(max(float(features.get(name, 0.0)), 0.0), 1.0)
        c = weight * value
        total += c
        if c > 0:
            contributions.append((c, name, value))
    total = min(total, 1.0)
    contributions.sort(reverse=True)
    reasons = [f"{name} ({value:.2f})" for _, name, value in contributions[:3]]
    band = "high" if total >= HIGH_THRESHOLD else "review" if total >= REVIEW_THRESHOLD else "low"
    return RiskResult(round(total, 3), band, reasons)


class Hysteresis:
    """Stops an alert flapping around a threshold: raise at `high`, clear at `low`."""

    def __init__(self, raise_at: float = REVIEW_THRESHOLD, clear_at: float = 0.35):
        self.raise_at, self.clear_at, self.active = raise_at, clear_at, False

    def update(self, score: float) -> bool:
        if not self.active and score >= self.raise_at:
            self.active = True
        elif self.active and score < self.clear_at:
            self.active = False
        return self.active
