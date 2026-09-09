from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _add_vertical_marker(figure, when, color: str, label: str) -> None:
    """Add a timestamp marker without Plotly's datetime add_vline bug."""
    timestamp = when.isoformat() if hasattr(when, "isoformat") else str(when)

    figure.add_shape(
        type="line",
        x0=timestamp,
        x1=timestamp,
        y0=0,
        y1=1,
        xref="x",
        yref="paper",
        line={"color": color, "dash": "dash", "width": 2},
    )

    figure.add_annotation(
        x=timestamp,
        y=1,
        xref="x",
        yref="paper",
        text=label,
        showarrow=False,
        yshift=12,
        font={"color": color},
    )


def write_alert_timeline(frame, output_path: Path) -> None:
    """Write a portable interactive timeline for one representative held-out event."""
    episode_id = frame.loc[
        (frame["split"] == "test") & frame["is_event"], "episode_id"
    ].iloc[0]

    data = frame.loc[frame["episode_id"] == episode_id].sort_values("timestamp")

    figure = make_subplots(specs=[[{"secondary_y": True}]])

    figure.add_trace(
        go.Scatter(
            x=data["timestamp"],
            y=data["response_time_ms"],
            name="Response latency (ms)",
        ),
        secondary_y=False,
    )

    figure.add_trace(
        go.Scatter(
            x=data["timestamp"],
            y=data["iforest_score"],
            name="Isolation Forest score",
        ),
        secondary_y=True,
    )

    figure.add_trace(
        go.Scatter(
            x=data["timestamp"],
            y=data["baseline_score"],
            name="Robust baseline score",
            line={"dash": "dot"},
        ),
        secondary_y=True,
    )

    warning = data.loc[data["is_warning"], "timestamp"].min()
    onset = data.loc[data["is_event"], "timestamp"].min()

    _add_vertical_marker(figure, warning, "#86A8CF", "Warning window")
    _add_vertical_marker(figure, onset, "#C38EB4", "Event onset")

    for column, color, label in [
        ("iforest_alert", "#31B7A5", "IF alert"),
        ("reactive_alert", "#F4B942", "Reactive breach"),
    ]:
        alerts = data.loc[data[column]]

        if not alerts.empty:
            _add_vertical_marker(figure, alerts["timestamp"].iloc[0], color, label)

    figure.update_layout(
        title=f"Alert timeline: {episode_id}",
        template="plotly_dark",
        height=560,
    )

    figure.write_html(output_path, include_plotlyjs="cdn")