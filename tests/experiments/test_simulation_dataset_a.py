
"""Regression and consistency tests for the offline Dataset A simulator."""

import pandas as pd
import pytest

from experiments.simulation.run_dataset_a import (
    SCENARIOS,
    build_episode_baselines,
    evaluate_scenarios,
    simulate,
    summarize_test_scenarios,
)


def test_no_change_preserves_baseline():
    result = simulate(
        request_rate=100,
        latency=200,
        error_rate=2,
        db_latency=80,
        traffic_change=0,
        capacity_change=0,
        db_latency_change=0,
    )

    assert result["simulated_request_rate"] == pytest.approx(100)
    assert result["simulated_latency"] == pytest.approx(200)
    assert result["simulated_error_rate"] == pytest.approx(2)
    assert result["simulated_db_latency"] == pytest.approx(80)


def test_scenario_direction_and_capacity_offset():
    baseline = dict(
        request_rate=100,
        latency=200,
        error_rate=2,
        db_latency=80,
    )

    traffic = simulate(
    **baseline,
    traffic_change=20,
    capacity_change=0,
    db_latency_change=0,
    )
    capacity = simulate(
        **baseline,
        traffic_change=0,
        capacity_change=20,
        db_latency_change=0,
    )
    balanced = simulate(
        **baseline,
        traffic_change=20,
        capacity_change=20,
        db_latency_change=0,
    )
    db_increase = simulate(
        **baseline,
        traffic_change=0,
        capacity_change=0,
        db_latency_change=20,
    )
    db_decrease = simulate(
        **baseline,
        traffic_change=0,
        capacity_change=0,
        db_latency_change=-20,
    )

    assert traffic["simulated_latency"] > baseline["latency"]
    assert traffic["simulated_error_rate"] > baseline["error_rate"]

    # In the current model, spare capacity has no direct benefit
    # unless it offsets traffic-induced pressure.
    assert capacity["simulated_latency"] == pytest.approx(
        baseline["latency"]
    )
    assert balanced["simulated_latency"] == pytest.approx(
        baseline["latency"]
    )

    assert db_increase["simulated_latency"] > baseline["latency"]
    assert db_decrease["simulated_latency"] < baseline["latency"]


def test_dataset_a_output_counts_and_no_change():
    telemetry = pd.read_csv(
        "data/processed/controlled_anomaly/telemetry.csv"
    )
    manifest = pd.read_csv(
        "data/processed/controlled_anomaly/manifest.csv"
    )

    baselines = build_episode_baselines(telemetry, manifest)
    results = evaluate_scenarios(baselines)
    summary = summarize_test_scenarios(results)

    assert len(baselines) == 100
    assert baselines["episode_id"].is_unique
    assert len(results) == 100 * len(SCENARIOS)
    assert len(summary) == len(SCENARIOS)
    assert summary["episodes"].eq(45).all()

    no_change = results[results["scenario"] == "no_change"]
    assert no_change["latency_delta"].abs().max() < 1e-9
    assert no_change["error_rate_delta"].abs().max() < 1e-9

    test_results = results[results["split"] == "test"]
    assert len(test_results) == 45 * len(SCENARIOS)
