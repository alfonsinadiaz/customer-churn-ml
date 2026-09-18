import pandas as pd

from src.features.preprocessing import build_preprocessor


def test_preprocessor_handles_missing_and_unknown_categories():
    train = pd.DataFrame(
        {
            "tenure": [1, 2],
            "MonthlyCharges": [20.0, 40.0],
            "TotalCharges": [20.0, None],
            "Contract": ["Month-to-month", "One year"],
        }
    )
    new_data = pd.DataFrame(
        {
            "tenure": [3],
            "MonthlyCharges": [50.0],
            "TotalCharges": [None],
            "Contract": ["Two year"],
        }
    )

    preprocessor = build_preprocessor(train)
    preprocessor.fit(train)
    transformed = preprocessor.transform(new_data)

    assert transformed.shape[0] == 1
