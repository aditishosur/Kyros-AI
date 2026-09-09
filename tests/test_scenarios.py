import numpy as np

from experiments.scenarios.generator import _normal_signals, apply_scenario, generate_dataset


def test_traffic_spike_changes_demand_not_latency():
    normal = _normal_signals(7, "/payments", 168)
    changed = apply_scenario(normal, "traffic_spike", 1.2, 108, 132)
    assert changed.loc[108:131, "request_count"].mean() > normal.loc[108:131, "request_count"].mean() * 1.5
    assert np.isclose(changed.loc[108:131, "response_time_ms"].mean(), normal.loc[108:131, "response_time_ms"].mean())


def test_latency_scenario_changes_latency_without_demand_change():
    normal = _normal_signals(8, "/orders", 168)
    changed = apply_scenario(normal, "latency_increase", 1.2, 108, 132)
    assert changed.loc[108:131, "response_time_ms"].mean() > normal.loc[108:131, "response_time_ms"].mean() * 1.7
    assert np.isclose(changed.loc[108:131, "request_count"].mean(), normal.loc[108:131, "request_count"].mean())


def test_database_slowdown_propagates_to_latency_and_errors():
    normal = _normal_signals(9, "/inventory", 168)
    changed = apply_scenario(normal, "database_slowdown", 1.2, 108, 132)
    window = slice(108, 132)
    assert changed.loc[window, "db_latency_ms"].mean() > normal.loc[window, "db_latency_ms"].mean() * 2
    assert changed.loc[window, "response_time_ms"].mean() > normal.loc[window, "response_time_ms"].mean() * 1.6
    assert changed.loc[window, "error_rate"].mean() > normal.loc[window, "error_rate"].mean() + 2


def test_error_burst_changes_error_rate_without_demand_change():
    normal = _normal_signals(10, "/payments", 168)
    changed = apply_scenario(normal, "error_burst_5xx", 1.2, 108, 132)
    assert changed.loc[108:131, "error_rate"].mean() > normal.loc[108:131, "error_rate"].mean() + 8
    assert np.isclose(changed.loc[108:131, "request_count"].mean(), normal.loc[108:131, "request_count"].mean())


def test_generated_events_have_frozen_windows_and_manifest_metadata():
    config = {
        "episode_hours": 168,
        "warning_start_hour": 96,
        "event_onset_hour": 108,
        "event_end_hour": 132,
        "train_normal_seeds": [1],
        "validation_normal_seeds": [2],
        "test_normal_seeds": [3],
        "validation_event_seeds": [4],
        "test_event_seeds": [5],
        "validation_intensities": [0.5],
        "test_intensities": [1.2],
        "endpoints": ["/payments"],
    }
    telemetry, manifest = generate_dataset(config)
    assert {"run_id", "seed", "endpoint", "severity", "intensity", "primary_cause", "warning_start_time_utc", "event_onset_time_utc", "event_end_time_utc"}.issubset(manifest.columns)
    assert set(manifest.loc[manifest["scenario"] != "normal", "scenario"]) == {
        "traffic_spike", "latency_increase", "database_slowdown", "error_burst_5xx"
    }
    assert not telemetry.loc[telemetry["scenario"] == "normal", ["is_warning", "is_event"]].to_numpy().any()
    episode_id = manifest.loc[
        manifest["scenario"] == "database_slowdown", "episode_id"
    ].iloc[0]

    episode = telemetry.loc[telemetry["episode_id"] == episode_id]

    assert episode["is_warning"].sum() == 12
    assert episode["is_event"].sum() == 24
