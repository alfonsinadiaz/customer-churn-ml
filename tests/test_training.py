from src.training.train import model_candidates


def test_six_reasoned_candidates_are_defined():
    candidates = model_candidates()

    assert len(candidates) == 6
    assert {candidate["family"] for candidate in candidates} >= {
        "baseline",
        "linear",
        "tree",
    }
