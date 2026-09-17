from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def write_alert_timeline(frame, output_path: Path) -> None:
    """Write a portable interactive timeline for one representative held-out event."""
    episode_id = frame.loc[(frame["split"] == "test") & frame["is_event"], "episode_id"].iloc[0]
    data = frame.loc[frame["episode_id"] == episode_id].sort_values("timestamp")
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(go.Scatter(x=data["timestamp"], y=data["response_time_ms"], name="Response latency (ms)"), secondary_y=False)
    figure.add_trace(go.Scatter(x=data["timestamp"], y=data["iforest_score"], name="Isolation Forest score"), secondary_y=True)
    figure.add_trace(go.Scatter(x=data["timestamp"], y=data["baseline_score"], name="Robust baseline score", line={"dash": "dot"}), secondary_y=True)
    onset = data.loc[data["is_event"], "timestamp"].min()
    warning = data.loc[data["is_warning"], "timestamp"].min()
    figure.add_vline(x=warning, line_dash="dash", line_color="#86A8CF", annotation_text="Warning window")
    figure.add_vline(x=onset, line_dash="dash", line_color="#C38EB4", annotation_text="Event onset")
    for column, color, label in [("iforest_alert", "#31B7A5", "IF alert"), ("reactive_alert", "#F4B942", "Reactive breach")]:
        alerts = data.loc[data[column]]
        if not alerts.empty:
            figure.add_vline(x=alerts["timestamp"].iloc[0], line_color=color, annotation_text=label)
    figure.update_layout(title=f"Alert timeline: {episode_id}", template="plotly_dark", height=560)
    figure.write_html(output_path, include_plotlyjs="cdn")
