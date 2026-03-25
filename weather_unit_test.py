from app.weather_pipeline import clean_weather_data
import pandas as pd


def test_clean_weather_data():
    """
    Tests the clean_weather_data function.

    - Checks that valid rows are separated correctly
    - Checks that reject reasons are assigned properly
    """

    # Prepare a small sample dataframe

    data = {
        "col1": ["1961-01-01", "1961-01-02", "1961-01-03", "bad-date", "1961-01-04"],
        "col2": ["0.0", "0.0", "0.0", "0.0", "0.0"],  # precipitation, will be dropped
        "col3": ["1.5", "abc", "70", "5", "10"]  # temp column with one invalid, one extreme
    }

    df = pd.DataFrame(data)

    # Step 2: Call the cleaning function
    df_valid, df_rejected = clean_weather_data(df)

    #  Assertions

    # Check that valid dataframe contains only correct rows
    assert "bad-date" not in df_valid["created_at"].astype(str).tolist(), "Invalid date should be rejected"
    assert "70" not in df_valid["temp"].astype(str).tolist(), "Extreme temperature should be rejected"

    # Check rejected dataframe
    rejected_reasons = df_rejected["reject_reason"].tolist()
    assert any("invalid_date" in r for r in rejected_reasons), "Should flag invalid dates"
    assert any("invalid_temp" in r for r in rejected_reasons), "Should flag non-numeric temps"
    assert any("extreme_temp" in r for r in rejected_reasons), "Should flag extreme temps"

    # Check that precipitation column is removed in valid dataframe
    assert "precipitation" not in df_valid.columns, "Precipitation column should be removed"
