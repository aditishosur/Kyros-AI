
# Dataset A: What-if Simulation Evaluation

## Objective

Characterize the deterministic response of the existing Kyros-AI
what-if simulation equations to predefined changes in traffic,
capacity, and database latency.

This is a scenario-sensitivity and internal-consistency experiment,
not an evaluation of real-world counterfactual prediction accuracy.

## Data and protocol

Use the frozen synthetic Dataset A, containing 100 episodes.
For each episode, construct a baseline from the seven observations
ending at zero-based hour 131, matching the RCA evaluation time.

Apply six scenarios independently to each baseline:

1. No change.
2. Traffic +20%.
3. Capacity +20%.
4. Database latency +20%.
5. Database latency -20%.
6. Traffic +20% and capacity +20%.

The offline runner reproduces the production simulator's request-rate,
database-latency, response-latency, and error-rate equations. It does
not call the database-backed production function or evaluate its risk
score, health status, or recommendation text.

The experiment generates 600 scenario predictions across all splits.
Only the 45 held-out test episodes contribute to the reported summary.

## Held-out test results

| Scenario | Episodes | Mean predicted latency change (ms) | Mean predicted error-rate change (percentage points) |
|---|---:|---:|---:|
| No change | 45 | 0.000000 | 0.0 |
| Traffic +20% | 45 | +69.703657 | +1.6 |
| Capacity +20% | 45 | 0.000000 | 0.0 |
| Database latency +20% | 45 | +14.332208 | +0.6 |
| Database latency -20% | 45 | -14.332208 | 0.0 |
| Traffic +20%, capacity +20% | 45 | 0.000000 | 0.0 |

The capacity-only scenario produces no predicted improvement because
the existing equations impose an additional latency and error penalty
only when the traffic-to-capacity pressure ratio exceeds one.
Increasing traffic and capacity by the same percentage keeps this
ratio at one.

These results describe the behavior of the specified equations on
Dataset A baselines. They do not establish that the predicted changes
would occur following actual interventions.

## Limitations

Dataset A does not contain independently observed outcomes after
hypothetical traffic, capacity, or database interventions. Therefore,
counterfactual MAE, intervention-direction accuracy against ground
truth, and intervention-ranking agreement against ground truth cannot
be calculated from this dataset.

The offline runner mirrors the production equations rather than
independently validating them. The scenario grid is illustrative,
and the findings should not be generalized to production systems.

## Reproduction

From the repository root:

```bash
python -m experiments.simulation.run_dataset_a
python -m pytest tests/experiments/ -q
```

Generated artifacts are stored in `results/simulation_dataset_a_v1/`:
`episode_baselines.csv`, `scenario_predictions.csv`, and
`test_scenario_summary.csv`.
