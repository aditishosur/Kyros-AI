import pytest

from experiments.common.cause_taxonomy import (
    APPLICATION_ERROR,
    DB_LATENCY,
    ELEVATED_RISK,
    TRAFFIC_DB_PRESSURE,
)
from experiments.rca.evaluate import RCAEvaluationCase, evaluate_cases


def test_perfect_accuracy():
    cases = [
        RCAEvaluationCase(
            "case-1",
            TRAFFIC_DB_PRESSURE,
            TRAFFIC_DB_PRESSURE,
        ),
        RCAEvaluationCase(
            "case-2",
            DB_LATENCY,
            DB_LATENCY,
        ),
        RCAEvaluationCase(
            "case-3",
            APPLICATION_ERROR,
            APPLICATION_ERROR,
        ),
    ]

    result = evaluate_cases(cases)

    assert result.total_cases == 3
    assert result.correct_cases == 3
    assert result.accuracy == 1.0
    assert result.errors == []


def test_incorrect_prediction_is_recorded():
    cases = [
        RCAEvaluationCase(
            "case-1",
            DB_LATENCY,
            APPLICATION_ERROR,
        )
    ]

    result = evaluate_cases(cases)

    assert result.accuracy == 0.0
    assert result.errors == [
        {
            "case_id": "case-1",
            "true_label": DB_LATENCY,
            "predicted_label": APPLICATION_ERROR,
        }
    ]


def test_confusion_matrix_counts_predictions():
    cases = [
        RCAEvaluationCase(
            "case-1",
            DB_LATENCY,
            DB_LATENCY,
        ),
        RCAEvaluationCase(
            "case-2",
            DB_LATENCY,
            APPLICATION_ERROR,
        ),
    ]

    result = evaluate_cases(cases)

    assert result.confusion_matrix[DB_LATENCY][DB_LATENCY] == 1
    assert result.confusion_matrix[DB_LATENCY][APPLICATION_ERROR] == 1


def test_per_class_accuracy():
    cases = [
        RCAEvaluationCase(
            "case-1",
            DB_LATENCY,
            DB_LATENCY,
        ),
        RCAEvaluationCase(
            "case-2",
            DB_LATENCY,
            APPLICATION_ERROR,
        ),
        RCAEvaluationCase(
            "case-3",
            ELEVATED_RISK,
            ELEVATED_RISK,
        ),
    ]

    result = evaluate_cases(cases)

    assert result.per_class[DB_LATENCY]["total"] == 2
    assert result.per_class[DB_LATENCY]["correct"] == 1
    assert result.per_class[DB_LATENCY]["accuracy"] == 0.5

    assert result.per_class[ELEVATED_RISK]["accuracy"] == 1.0


def test_empty_input():
    result = evaluate_cases([])

    assert result.total_cases == 0
    assert result.correct_cases == 0
    assert result.accuracy == 0.0


def test_unknown_true_label_fails():
    cases = [
        RCAEvaluationCase(
            "case-1",
            "UNKNOWN_CAUSE",
            APPLICATION_ERROR,
        )
    ]

    with pytest.raises(ValueError):
        evaluate_cases(cases)


def test_unknown_predicted_label_fails():
    cases = [
        RCAEvaluationCase(
            "case-1",
            APPLICATION_ERROR,
            "UNKNOWN_CAUSE",
        )
    ]

    with pytest.raises(ValueError):
        evaluate_cases(cases)
