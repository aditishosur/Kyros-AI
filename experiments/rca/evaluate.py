from dataclasses import dataclass
from typing import Iterable

from experiments.common.cause_taxonomy import CAUSE_LABELS


@dataclass(frozen=True)
class RCAEvaluationCase:
    case_id: str
    true_label: str
    predicted_label: str


@dataclass(frozen=True)
class RCAEvaluationResult:
    total_cases: int
    correct_cases: int
    accuracy: float
    per_class: dict
    confusion_matrix: dict
    errors: list


def evaluate_cases(cases: Iterable[RCAEvaluationCase]) -> RCAEvaluationResult:
    cases = list(cases)

    confusion_matrix = {
        true_label: {pred_label: 0 for pred_label in CAUSE_LABELS}
        for true_label in CAUSE_LABELS
    }

    per_class = {
        label: {
            "total": 0,
            "correct": 0,
            "accuracy": 0.0,
        }
        for label in CAUSE_LABELS
    }

    errors = []
    correct_cases = 0

    for case in cases:
        if case.true_label not in CAUSE_LABELS:
            raise ValueError(
                f"Unknown true label for case {case.case_id}: {case.true_label}"
            )

        if case.predicted_label not in CAUSE_LABELS:
            raise ValueError(
                f"Unknown predicted label for case {case.case_id}: "
                f"{case.predicted_label}"
            )

        confusion_matrix[case.true_label][case.predicted_label] += 1

        per_class[case.true_label]["total"] += 1

        if case.true_label == case.predicted_label:
            correct_cases += 1
            per_class[case.true_label]["correct"] += 1
        else:
            errors.append(
                {
                    "case_id": case.case_id,
                    "true_label": case.true_label,
                    "predicted_label": case.predicted_label,
                }
            )

    for label, metrics in per_class.items():
        if metrics["total"] > 0:
            metrics["accuracy"] = round(
                metrics["correct"] / metrics["total"], 4
            )

    total_cases = len(cases)

    accuracy = (
        round(correct_cases / total_cases, 4)
        if total_cases > 0
        else 0.0
    )

    return RCAEvaluationResult(
        total_cases=total_cases,
        correct_cases=correct_cases,
        accuracy=accuracy,
        per_class=per_class,
        confusion_matrix=confusion_matrix,
        errors=errors,
    )
