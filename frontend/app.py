import os
import sys
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from frontend.client import API_BASE_URL, PulseOpsAPIError, delete, get_json, post_json, put_json
from frontend.components.charts import bar_chart, forecast_chart, gauge, line_chart
from frontend.components.style import CYAN, GREEN, ORANGE, PINK, RED, apply_theme, kpi, metric, risk_bar, status_badge


PAGES = [
    "Landing",
    "Overview",
    "API Intelligence",
    "Traffic Forecast",
    "Incidents & Root Cause",
    "What-If Simulator",
    "API Registry",
]


def configured_credentials() -> tuple[str, str]:
    return (
        os.getenv("PULSEOPS_USERNAME", "admin"),
        os.getenv("PULSEOPS_PASSWORD", "pulseops123"),
    )


def logout() -> None:
    st.session_state.authenticated = False
    st.session_state.page = "Landing"
    st.rerun()


def login_page() -> None:
    username, password = configured_credentials()
    st.markdown(
        """
        <div class="hero" style="grid-template-columns:minmax(0,1fr) minmax(340px,.62fr);min-height:660px;">
            <div>
                <div class="eyebrow">PULSEOPS SECURE ACCESS</div>
                <div class="hero-title">Predictive API Intelligence Command Center.</div>
                <div class="hero-copy">
                    Sign in to monitor API health, forecast degradation, explain incidents
                    and simulate infrastructure decisions before production risk escalates.
                </div>
                <div class="flow-card" style="margin-top:1.5rem;max-width:620px;">
                    <div class="flow-node"><strong>Monitor</strong><span>fleet health</span></div>
                    <div class="flow-node"><strong>Predict</strong><span>traffic risk</span></div>
                    <div class="flow-node"><strong>Explain</strong><span>root cause</span></div>
                    <div class="flow-node"><strong>Simulate</strong><span>capacity decisions</span></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1.05, 0.9, 1.05])

    with center:
        st.markdown(
            '<div class="panel"><h2>Sign In</h2><p class="muted">Use the demo operator account to enter PulseOps.</p>',
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            entered_user = st.text_input("Username", value="admin")
            entered_pass = st.text_input("Password", type="password", value="")
            submitted = st.form_submit_button("Enter Operations Center", use_container_width=True)

        st.markdown(
            '<p class="muted" style="font-size:.82rem;">Demo credentials: admin / pulseops123</p></div>',
            unsafe_allow_html=True,
        )

        if submitted:
            if entered_user == username and entered_pass == password:
                st.session_state.authenticated = True
                st.session_state.page = "Landing"
                st.rerun()
            else:
                st.error("Invalid credentials. Try the demo operator account.")


def go(page: str, api_id: int | None = None) -> None:
    st.session_state.page = page
    if api_id is not None:
        st.session_state.api_id = api_id
    st.rerun()


def page_state() -> str:
    st.session_state.setdefault("page", "Landing")
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("api_id", 1)
    return st.session_state.page


def shell() -> None:
    with st.sidebar:
        st.markdown(
            '<div class="brand"><div class="name">PULSEOPS</div><div class="tag">Predictive API Intelligence</div></div>',
            unsafe_allow_html=True,
        )

        for page in PAGES[1:]:
            label = page.upper()
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                go(page)

        st.markdown(
            f"""
            <div class="side-status">
                <div style="color:#6ee7a8;font-weight:800;">System Status: Operational</div>
                <div class="muted" style="margin-top:.45rem;">Environment: Development</div>
                <div class="muted" style="margin-top:.45rem;">API: {API_BASE_URL}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("SIGN OUT", use_container_width=True):
            logout()


def api_selector(label: str = "Select API") -> tuple[list[dict], int]:
    apis = get_json("/apis")
    if not apis:
        st.warning("No APIs are registered yet.")
        return [], 0

    ids = [api["id"] for api in apis]

    if st.session_state.get("api_id") not in ids:
        st.session_state.api_id = ids[0]

    labels = {
        api["id"]: f'{api["name"]}  {api["method"]} {api["endpoint"]}'
        for api in apis
    }

    api_id = st.selectbox(
        label,
        ids,
        format_func=lambda value: labels[value],
        index=ids.index(st.session_state.api_id),
    )

    st.session_state.api_id = api_id
    return apis, api_id


def landing() -> None:
    st.markdown(
        """
        <div class="hero">
            <div>
                <div class="eyebrow">PULSEOPS / Predictive API Intelligence</div>
                <div class="hero-title">Know what will happen to your APIs before they fail.</div>
                <div class="hero-copy">
                    PulseOps combines API observability, machine learning, anomaly detection,
                    explainable root-cause analysis and impact simulation into one operational
                    intelligence platform.
                </div>
            </div>
            <div class="flow-card">
                <div class="flow-node"><strong>Monitor</strong><span>risk + telemetry</span></div>
                <div class="flow-node"><strong>Predict</strong><span>traffic forecast</span></div>
                <div class="flow-node"><strong>Explain</strong><span>causal chain</span></div>
                <div class="flow-node"><strong>Simulate</strong><span>what-if impact</span></div>
                <div class="flow-node"><strong>Recommend</strong><span>capacity decision</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1.1, 1, 2.3])

    if c1.button("Open Operations Center", use_container_width=True):
        go("Overview")

    if c2.button("Explore Intelligence", use_container_width=True):
        go("API Intelligence")

    st.markdown("### Core Capabilities")

    cols = st.columns(4)

    features = [
        ("01", "Monitor", "API Risk & Health Intelligence"),
        ("02", "Predict", "ML Traffic Forecasting"),
        ("03", "Explain", "Root Cause Analysis"),
        ("04", "Simulate", "What-If Impact Simulation"),
    ]

    targets = [
        "Overview",
        "Traffic Forecast",
        "Incidents & Root Cause",
        "What-If Simulator",
    ]

    for col, (num, title, body), target in zip(cols, features, targets):
        with col:
            st.markdown(
                f'<div class="feature-card"><div class="eyebrow">{num}</div><h3>{title}</h3><p class="muted">{body}</p></div>',
                unsafe_allow_html=True,
            )
            if st.button(f"Open {title}", key=f"feature_{title}", use_container_width=True):
                go(target)

    st.markdown("### How PulseOps Works")

    st.markdown(
        '<div class="panel"><strong>Telemetry</strong> -> <strong>Analytics</strong> -> <strong>ML</strong> -> <strong>Intelligence</strong> -> <strong>Decision Support</strong><br><span class="muted">FastAPI, SQLAlchemy, SQLite, Scikit-learn, Streamlit, Plotly, Docker, Kubernetes and GitHub Actions.</span></div>',
        unsafe_allow_html=True,
    )


def overview_page() -> None:
    data = get_json("/analytics/overview")

    st.title("Operations Center")
    st.markdown(
        '<div class="muted">Real-time API health, performance and predictive risk.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="panel" style="margin-top:1rem;">{status_badge("Healthy")} &nbsp; <strong>{data["apis_monitored"]} APIs monitored</strong> &nbsp; <span class="muted">{data["incidents"]} incidents generated by RCA checks. Last updated {data["last_updated"][:19]} UTC.</span></div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(6)

    values = [
        ("Total Requests", f'{data["total_requests"]:,}', "Synthetic 14-day telemetry"),
        ("Avg Response Time", f'{data["avg_response_time"]:.0f} ms', "Current fleet average"),
        ("P95 Latency", f'{data["p95_response_time"]:.0f} ms', "Tail performance"),
        ("Error Rate", f'{data["error_rate"]:.2f}%', "5xx weighted by traffic"),
        ("Healthy APIs", str(data["healthy_apis"]), "Operating normally"),
        ("At-Risk APIs", str(data["at_risk_apis"]), "Needs attention"),
    ]

    for col, args in zip(cols, values):
        with col:
            kpi(*args)

    st.markdown("### API Health Overview")

    api_rows = pd.DataFrame(data["apis"]).sort_values("risk_score", ascending=False)

    view = api_rows[
        [
            "name",
            "status",
            "risk_score",
            "traffic_delta",
            "latency",
            "error_rate",
            "anomaly",
            "endpoint",
        ]
    ].rename(
        columns={
            "name": "API",
            "status": "Status",
            "risk_score": "Risk",
            "traffic_delta": "Traffic Delta %",
            "latency": "Latency ms",
            "error_rate": "Error %",
            "anomaly": "Anomaly",
            "endpoint": "Endpoint",
        }
    )

    st.dataframe(view, use_container_width=True, hide_index=True)

    left, right = st.columns([1.42, 1])
    ts_frames = []

    for row in data["apis"][:5]:
        detail = get_json(f"/analytics/apis/{row['id']}")
        df = pd.DataFrame(detail["timeseries"])

        if not df.empty:
            df["api"] = row["name"]
            ts_frames.append(df)

    if ts_frames:
        combined = pd.concat(ts_frames)
        traffic = combined.groupby("timestamp", as_index=False)["request_count"].sum()
        perf = combined.groupby("timestamp", as_index=False).agg(
            response_time_ms=("response_time_ms", "mean"),
            error_rate=("error_rate", "mean"),
        )

        with left:
            st.plotly_chart(
                line_chart(
                    traffic,
                    "timestamp",
                    [("request_count", "Requests")],
                    "Traffic Overview",
                    410,
                ),
                use_container_width=True,
            )

        with right:
            st.plotly_chart(
                line_chart(
                    perf,
                    "timestamp",
                    [
                        ("response_time_ms", "Latency"),
                        ("error_rate", "Errors %"),
                    ],
                    "Performance Overview",
                    410,
                ),
                use_container_width=True,
            )

    st.markdown("### Attention Required")

    risky = api_rows[api_rows["risk_score"] >= 40].head(3)
    cols = st.columns(max(1, len(risky)))

    for col, (_, row) in zip(cols, risky.iterrows()):
        with col:
            st.markdown(
                f"""
                <div class="attention-card">
                    {status_badge(row["status"])}
                    <h3>{row["name"]}</h3>
                    {risk_bar(row["risk_score"])}
                    <p class="muted">Traffic {row["traffic_delta"]:+.1f}% with latency {row["latency"]:.0f}ms and errors {row["error_rate"]:.1f}%.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("Investigate", key=f"investigate_{row['id']}", use_container_width=True):
                go("API Intelligence", int(row["id"]))


def intelligence_page() -> None:
    _, api_id = api_selector()

    detail = get_json(f"/analytics/apis/{api_id}")
    anomaly = get_json(f"/analytics/apis/{api_id}/anomalies")

    api, metrics = detail["api"], detail["metrics"]

    st.title("API Intelligence")
    st.markdown(
        f'<div class="muted">{api["method"]} {api["endpoint"]} owned by {api["owner"]}</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([0.82, 1.18])

    with c1:
        st.plotly_chart(gauge(metrics["risk_score"]), use_container_width=True)
        st.markdown(
            f'<div class="panel">{status_badge(metrics["status"])}<br><br>{risk_bar(metrics["risk_score"])}</div>',
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown("### Risk Contributors")
        for name, value in metrics["contributors"].items():
            st.markdown(
                f'<div class="panel" style="margin-bottom:.45rem;display:flex;justify-content:space-between;"><span>{name}</span><strong>+{value:.1f}</strong></div>',
                unsafe_allow_html=True,
            )

    cols = st.columns(6)

    metric_cards = [
        ("Average Latency", f'{metrics["avg_response_time"]:.0f} ms', "recent 6h"),
        ("P95 Latency", f'{metrics["p95_response_time"]:.0f} ms', "tail"),
        ("Error Rate", f'{metrics["error_rate"]:.2f}%', "5xx"),
        ("Requests/hr", f'{metrics["request_rate"]:.0f}', "current"),
        ("CPU", f'{metrics["cpu_usage"]:.1f}%', "service"),
        ("DB Latency", f'{metrics["db_latency"]:.0f} ms', "database"),
    ]

    for col, args in zip(cols, metric_cards):
        with col:
            metric(*args)

    df = pd.DataFrame(detail["timeseries"])

    if not df.empty:
        left, right = st.columns(2)

        with left:
            st.plotly_chart(
                line_chart(
                    df,
                    "timestamp",
                    [
                        ("request_count", "Traffic"),
                        ("response_time_ms", "Latency"),
                    ],
                    "Traffic and Latency",
                ),
                use_container_width=True,
            )

        with right:
            st.plotly_chart(
                line_chart(
                    df,
                    "timestamp",
                    [
                        ("error_rate", "Error %"),
                        ("db_latency_ms", "DB latency"),
                    ],
                    "Errors and Database Pressure",
                ),
                use_container_width=True,
            )

    st.markdown(
        f'<div class="panel"><h3>AI / ML Intelligence</h3><p>Anomaly detected: <strong>{str(anomaly["latest_is_anomaly"]).upper()}</strong></p><p class="muted">Isolation Forest evaluates traffic, latency, errors, CPU and DB latency to flag unusual operating states.</p></div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    if c1.button("Investigate Incident", use_container_width=True):
        go("Incidents & Root Cause", api_id)

    if c2.button("View Traffic Forecast", use_container_width=True):
        go("Traffic Forecast", api_id)


def forecast_page() -> None:
    _, api_id = api_selector()

    st.title("Traffic Forecast")
    st.markdown(
        '<div class="muted">Predict API demand before it becomes an operational problem.</div>',
        unsafe_allow_html=True,
    )

    data = get_json(f"/predictions/{api_id}")

    historical = pd.DataFrame(data["historical"])
    predicted = pd.DataFrame(data["forecast"])

    if historical.empty or predicted.empty:
        st.info("No forecast is available yet for this API.")
        return

    st.plotly_chart(forecast_chart(historical, predicted), use_container_width=True)

    summary = data["summary"]
    cols = st.columns(5)

    current_capacity = summary["capacity"]
    gap = (summary["predicted_peak_traffic"] / max(current_capacity, 1) - 1) * 100

    cards = [
        ("Predicted Peak", f'{summary["predicted_peak_traffic"]:,.0f}/hr', "forecast horizon"),
        ("Peak Time", summary["peak_time"][11:16], "UTC"),
        ("Traffic Growth", f'{summary["expected_growth"]:+.1f}%', "vs current"),
        ("Current Risk", f'{summary["current_risk"]:.0f}', "now"),
        ("Predicted Risk", f'{summary["predicted_risk"]:.0f}', "peak"),
    ]

    for col, args in zip(cols, cards):
        with col:
            metric(*args)

    status = "CAPACITY RISK" if gap > 0 else "WITHIN CAPACITY"

    recommendation = (
        "Increase service capacity by approximately "
        + str(round(max(gap, 0) + 10, 1))
        + "% before the projected peak."
        if gap > 0
        else "Current capacity appears sufficient for the forecast window."
    )

    st.markdown(
        f"""
        <div class="panel">
            <h3>Capacity Outlook</h3>
            <p>Expected traffic: <strong>{summary["predicted_peak_traffic"]:,.0f} req/hr</strong></p>
            <p>Current estimated capacity: <strong>{current_capacity:,.0f} req/hr</strong></p>
            <p>Capacity gap: <strong>{gap:+.1f}%</strong></p>
            <p>{status_badge("Critical" if gap > 15 else "Degraded" if gap > 0 else "Healthy")} <strong>{status}</strong></p>
            <p class="muted">Recommendation: {recommendation}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Run What-If Simulation", use_container_width=True):
        go("What-If Simulator", api_id)


def root_cause_page() -> None:
    _, api_id = api_selector()

    incident = get_json(f"/analytics/apis/{api_id}/root-cause")

    st.title("Incident Intelligence")
    st.markdown(
        '<div class="muted">Understand why an API is degrading, not just that it is degrading.</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(3)

    with cols[0]:
        metric("Incident Severity", incident["severity"].upper(), "deterministic RCA")

    with cols[1]:
        metric("Risk Score", f'{incident["risk_score"]:.0f}/100', "current")

    with cols[2]:
        metric("Detected At", incident["detected_at"][11:19], "UTC")

    st.markdown("### Root-Cause Chain")

    chain_html = '<div class="chain">'

    for node in incident["chain"]:
        chain_html += f'<div class="chain-node"><div class="eyebrow">{node["label"]}</div><div class="num">{node["value"]}</div></div>'

    chain_html += "</div>"

    st.markdown(chain_html, unsafe_allow_html=True)

    left, right = st.columns([1.2, 0.8])

    with left:
        st.markdown(
            f"""
            <div class="panel">
                <h3>Probable Root Cause</h3>
                <h2>{incident["probable_root_cause"].upper()}</h2>
                <p>Confidence: <strong>{incident["confidence"]}</strong></p>
                <p class="muted">{incident["explanation"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        factors = incident["contributing_factors"]
        st.plotly_chart(
            bar_chart(list(factors.keys()), list(factors.values()), "Contributing Factors"),
            use_container_width=True,
        )

    st.markdown(
        f'<div class="panel"><h3>Recommended Action</h3><p>{incident["recommended_action"]}</p></div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    if c1.button("Run What-If Simulation", use_container_width=True):
        go("What-If Simulator", api_id)

    if c2.button("View API Intelligence", use_container_width=True):
        go("API Intelligence", api_id)


def simulator_page() -> None:
    _, api_id = api_selector()

    st.title("What-If Impact Simulator")
    st.markdown(
        '<div class="muted">Test operational decisions before applying them to production. SIMULATED/PREDICTED, not live infrastructure measurements.</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([0.86, 1.14])

    with left:
        st.markdown("### Scenario Controls")
        traffic = st.slider("Traffic Change %", -50, 200, 50, 5)
        capacity = st.slider("Server Capacity Change %", -50, 200, -20, 5)
        db_latency = st.slider("Database Latency Change %", -50, 150, 10, 5)
        run = st.button("RUN SIMULATION", use_container_width=True)

    if run or "last_sim" not in st.session_state:
        st.session_state.last_sim = post_json(
            "/simulation/run",
            {
                "api_id": api_id,
                "traffic_change": traffic,
                "capacity_change": capacity,
                "db_latency_change": db_latency,
            },
        )

    sim = st.session_state.last_sim

    with right:
        st.markdown("### Simulation Preview")

        current, simulated, impact = sim["current"], sim["simulated"], sim["impact"]

        st.markdown(
            f"""
            <div class="compare">
                <div class="panel">
                    <div class="eyebrow">Current</div>
                    <h2>{current["health"]}</h2>
                    <p>Risk <strong>{current["risk"]:.0f}</strong></p>
                    <p>Latency <strong>{current["latency"]:.0f}ms</strong></p>
                    <p>Errors <strong>{current["error_rate"]:.2f}%</strong></p>
                </div>
                <div class="panel">
                    <div class="eyebrow">Simulated</div>
                    <h2>{simulated["health"]}</h2>
                    <p>Risk <strong>{simulated["risk"]:.0f}</strong></p>
                    <p>Latency <strong>{simulated["latency"]:.0f}ms</strong></p>
                    <p>Errors <strong>{simulated["error_rate"]:.2f}%</strong></p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        cols = st.columns(3)

        with cols[0]:
            metric("Latency Impact", f'{impact["latency_change_pct"]:+.1f}%', "vs current")

        with cols[1]:
            metric("Error Impact", f'{impact["error_rate_delta"]:+.2f}%', "absolute")

        with cols[2]:
            metric("Risk Impact", f'{impact["risk_delta"]:+.1f}', "score delta")

    st.markdown(
        f"""
        <div class="panel">
            <h3>Operational Recommendation</h3>
            <p>{status_badge(simulated["health"])} <strong>{sim["label"]}</strong></p>
            <p>{sim["recommendation"]}</p>
            <p class="muted">Scenario: traffic {traffic:+d}%, capacity {capacity:+d}%, database latency {db_latency:+d}%.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def registry_page() -> None:
    st.title("API Registry")

    apis = get_json("/apis")
    overview = get_json("/analytics/overview")

    risk_by_id = {row["id"]: row for row in overview["apis"]}

    search = st.text_input("Search APIs", "")
    status_filter = st.multiselect(
        "Status",
        ["Healthy", "Degraded", "Critical"],
        default=["Healthy", "Degraded", "Critical"],
    )

    rows = []

    for api in apis:
        risk = risk_by_id.get(api["id"], {})

        row = {
            "id": api["id"],
            "API": api["name"],
            "Endpoint": api["endpoint"],
            "Method": api["method"],
            "Owner": api["owner"],
            "Status": risk.get("status", api["status"]),
            "Risk": risk.get("risk_score", 0),
            "Last Updated": overview["last_updated"][:19],
        }

        searchable = f'{row["API"]} {row["Endpoint"]} {row["Owner"]}'.lower()

        if search.lower() in searchable and row["Status"] in status_filter:
            rows.append(row)

    df = pd.DataFrame(rows)

    st.dataframe(
        df.drop(columns=["id"]) if not df.empty else df,
        use_container_width=True,
        hide_index=True,
    )

    if not df.empty:
        api_id = st.selectbox(
            "Open API",
            df["id"].tolist(),
            format_func=lambda value: df[df["id"] == value]["API"].iloc[0],
        )

        c1, c2, c3 = st.columns(3)

        if c1.button("Open Intelligence", use_container_width=True):
            go("API Intelligence", int(api_id))

        with c2.expander("Add API"):
            with st.form("add_api"):
                name = st.text_input("Name")
                endpoint = st.text_input("Endpoint")
                method = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE"])
                owner = st.text_input("Owner")
                desc = st.text_area("Description")

                if st.form_submit_button("Create"):
                    payload = {
                        "name": name,
                        "endpoint": endpoint,
                        "method": method,
                        "owner": owner,
                        "description": desc,
                        "status": "Healthy",
                    }

                    post_json("/apis", payload)
                    st.success("API created.")
                    st.rerun()

        with c3.expander("Edit / Delete"):
            current = next(api for api in apis if api["id"] == api_id)

            with st.form("edit_api"):
                name = st.text_input("Name", current["name"])
                owner = st.text_input("Owner", current["owner"])

                status_options = ["Healthy", "Degraded", "Critical"]
                current_status_index = (
                    status_options.index(current["status"])
                    if current["status"] in status_options
                    else 0
                )

                status = st.selectbox(
                    "Status",
                    status_options,
                    index=current_status_index,
                )

                if st.form_submit_button("Update"):
                    put_json(
                        f"/apis/{api_id}",
                        {
                            "name": name,
                            "owner": owner,
                            "status": status,
                        },
                    )

                    st.success("API updated.")
                    st.rerun()

            if st.button("Delete Selected API", use_container_width=True):
                delete(f"/apis/{api_id}")
                st.success("API deleted.")
                st.rerun()


def main() -> None:
    apply_theme()

    page = page_state()

    if not st.session_state.authenticated:
        login_page()
        return

    if page != "Landing":
        shell()

    try:
        if page == "Landing":
            landing()
        elif page == "Overview":
            overview_page()
        elif page == "API Intelligence":
            intelligence_page()
        elif page == "Traffic Forecast":
            forecast_page()
        elif page == "Incidents & Root Cause":
            root_cause_page()
        elif page == "What-If Simulator":
            simulator_page()
        elif page == "API Registry":
            registry_page()

    except PulseOpsAPIError as exc:
        st.markdown(
            f"""
            <div class="panel">
                <h2>PulseOps API Unavailable</h2>
                <p>{exc}</p>
                <p class="muted">Start the backend with: uvicorn backend.main:app --reload --port 8000</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()