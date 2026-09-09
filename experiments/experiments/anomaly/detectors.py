from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler


class RobustLatencyBaseline:
    """A predeclared, robust univariate latency detector."""

    def fit(self, frame: pd.DataFrame) -> "RobustLatencyBaseline":
        values = frame["response_time_ms"].to_numpy(dtype=float)
        self.median_ = float(np.median(values))
        self.mad_ = float(np.median(np.abs(values - self.median_)))
        self.scale_ = max(1.4826 * self.mad_, 1e-9)
        return self

    def score(self, frame: pd.DataFrame) -> np.ndarray:
        if not hasattr(self, "median_"):
            raise RuntimeError("Baseline must be fitted before scoring")
        return np.abs(frame["response_time_ms"].to_numpy(dtype=float) - self.median_) / self.scale_


class IsolationForestDetector:
    def __init__(self, features: list[str], contamination: float, random_state: int = 42):
        self.features = features
        self.contamination = contamination
        self.random_state = random_state
        self.scaler = RobustScaler()
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=250,
            min_samples_leaf=1,
        )

    def fit(self, frame: pd.DataFrame) -> "IsolationForestDetector":
        matrix = frame[self.features].to_numpy(dtype=float)
        self.scaler.fit(matrix)
        self.model.fit(self.scaler.transform(matrix))
        return self

    def score(self, frame: pd.DataFrame) -> np.ndarray:
        """Higher values consistently mean more anomalous."""
        matrix = self.scaler.transform(frame[self.features].to_numpy(dtype=float))
        return -self.model.score_samples(matrix)
