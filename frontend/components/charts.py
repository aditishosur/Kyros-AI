import pandas as pd
import plotly.graph_objects as go

from frontend.components.style import CYAN, GREEN, MUTED, ORANGE, PANEL, PINK, PLOT_BG, RED, TEXT


def layout(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_BG,
        font={"color": TEXT, "family": "Inter, Segoe UI, sans-serif"},
        margin=dict(l=20, r=20, t=34, b=24),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor="rgba(134,168,207,.12)", zeroline=False),
        yaxis=dict(gridcolor="rgba(134,168,207,.12)", zeroline=False),
    )
    return fig


def line_chart(df: pd.DataFrame, x: str, series: list[tuple[str, str]], title: str, height: int = 360) -> go.Figure:
    fig = go.Figure()
    colors = [CYAN, PINK, ORANGE, GREEN, RED]
    for i, (col, name) in enumerate(series):
        fig.add_trace(go.Scatter(x=df[x], y=df[col], mode="lines", name=name, line=dict(color=colors[i % len(colors)], width=2.6)))
    fig.update_layout(title=title)
    return layout(fig, height)


def forecast_chart(historical: pd.DataFrame, forecast: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=historical["timestamp"], y=historical["request_count"], mode="lines", name="Historical", line=dict(color=CYAN, width=2.5)))
    fig.add_trace(go.Scatter(x=forecast["timestamp"], y=forecast["predicted_request_count"], mode="lines", name="Forecast", line=dict(color=PINK, width=3, dash="dash")))
    if not forecast.empty:
        fig.add_vrect(x0=forecast["timestamp"].min(), x1=forecast["timestamp"].max(), fillcolor=PINK, opacity=0.09, line_width=0)
    fig.update_layout(title="Historical vs Forecast Traffic")
    return layout(fig, 430)


def bar_chart(labels: list, values: list, title: str) -> go.Figure:
    fig = go.Figure(go.Bar(x=labels, y=values, marker=dict(color=[CYAN, PINK, ORANGE, GREEN, RED][: len(labels)])))
    fig.update_layout(title=title)
    return layout(fig, 330)


def gauge(score: float, title: str = "Risk Score") -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": title, "font": {"color": TEXT}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": MUTED},
                "bar": {"color": CYAN},
                "bgcolor": PANEL,
                "borderwidth": 1,
                "bordercolor": "rgba(134,168,207,.28)",
                "steps": [
                    {"range": [0, 40], "color": "rgba(110,231,168,.22)"},
                    {"range": [40, 70], "color": "rgba(247,178,103,.22)"},
                    {"range": [70, 100], "color": "rgba(255,107,122,.24)"},
                ],
            },
        )
    )
    return layout(fig, 270)
