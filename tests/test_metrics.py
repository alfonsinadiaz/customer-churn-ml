from src.evaluation.metrics import classification_metrics


def test_classification_metrics_returns_confusion_counts():
    metrics = classification_metrics(
        [0, 0, 1, 1],
        [0, 1, 0, 1],
        [0.1, 0.7, 0.4, 0.8],
    )

    assert metrics["tn"] == 1
    assert metrics["fp"] == 1
    assert metrics["fn"] == 1
    assert metrics["tp"] == 1
