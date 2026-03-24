from app.pipeline import clean_weather_data
import pandas as pd 


def test_clean_weather_data():

    """This tests:
    invalid date
    extreme temperature
    future timestamp"""

    data = {
        "created_at": [
            "2024-01-01",
            "2024-01-02",
            "not_a_date",
            "2030-01-01"
        ],
        "temp": [
            "20",
            "150",
            "10",
            "15"
        ]
    }

    df = pd.DataFrame(data)

    df_valid, df_rejected = clean_weather_data(df)

    # Valid rows should be only correct ones
    assert len(df_valid) == 1

    # Rejected rows should include invalid ones
    assert len(df_rejected) == 3

    #Test duplicate removal
def test_duplicates_removed():

    data = {
    "created_at": ["2024-01-01", "2024-01-01"],
    "temp": ["20", "20"]
    }

    df = pd.DataFrame(data)

    df_valid, df_rejected = clean_weather_data(df)

    assert len(df_valid) == 1

#Test numeric conversion
def test_temperature_conversion():

    data = {
        "created_at": ["2024-01-01"],
        "temp": ['"21,5"']
    }

    df = pd.DataFrame(data)

    df_valid, _ = clean_weather_data(df)

    assert df_valid["temp"].iloc[0] == 21.5