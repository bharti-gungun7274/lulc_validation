import numpy as np
from sklearn.metrics import (
    accuracy_score,
    cohen_kappa_score,
    precision_score,
    recall_score,
    f1_score,
)


VALID_CLASSES = list(range(9))


def calculate_metrics(reference, predicted):
    """
    Calculate LULC validation accuracy metrics.

    Reference = manually assigned reference/ground-truth class
    Predicted = Dynamic World classified class
    """

    reference = np.asarray(reference)
    predicted = np.asarray(predicted)

    if len(reference) != len(predicted):
        raise ValueError(
            "Reference and predicted arrays must have the same length."
        )

    if len(reference) == 0:
        raise ValueError("No valid validation points available.")

    # Overall Accuracy
    overall_accuracy = accuracy_score(
        reference,
        predicted
    )

    # Kappa
    kappa = cohen_kappa_score(
        reference,
        predicted,
        labels=VALID_CLASSES
    )

    # User Accuracy = Precision
    user_accuracy = precision_score(
        reference,
        predicted,
        labels=VALID_CLASSES,
        average=None,
        zero_division=0
    )

    # Producer Accuracy = Recall
    producer_accuracy = recall_score(
        reference,
        predicted,
        labels=VALID_CLASSES,
        average=None,
        zero_division=0
    )

    # F1 Score
    f1 = f1_score(
        reference,
        predicted,
        labels=VALID_CLASSES,
        average=None,
        zero_division=0
    )

    class_metrics = {}

    for i, class_id in enumerate(VALID_CLASSES):
        class_metrics[class_id] = {
            "user_accuracy": float(user_accuracy[i]),
            "producer_accuracy": float(producer_accuracy[i]),
            "f1_score": float(f1[i]),
        }

    return {
        "overall_accuracy": float(overall_accuracy),
        "kappa": float(kappa),
        "class_metrics": class_metrics,
    }