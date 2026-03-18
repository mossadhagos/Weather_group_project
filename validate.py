#from tests_scripts import data_handler.ipynb
#import pytest
import pandas as pd


def validate(df: pd.DataFrame) -> tuple [pd.DataFrame, pd.DataFrame]:
    df = df.copy()

    temp_min, temp_max = -70, 50
    today = pd.to_datetime('today')

    def get_reasons(row):
        reasons = []
        if pd.isna(row['created_at']):      reasons.append('missing_date')
        if pd.isna(row['temp']):            reasons.append('missing_temp')
        elif not temp_min <= row['temp'] <= temp_max: reasons.append('temp_out_of_range')
        if pd.notna(row['created_at']) and row['created_at'] > today: reasons.append('future_date')

        return ', '.join(reasons)

    df['invalid'] = df.apply(get_reasons, axis=1)

    def add_duplicate(r):
        if r:
            return r + ', duplicate'
        else:
            return 'duplicate'

    is_dup = df.duplicated(subset=['created_at', 'temp'], keep='first')
    df.loc[is_dup, 'invalid'] = df.loc[is_dup, 'invalid'].apply(add_duplicate)

    is_rejected = df['invalid'] != ''

    df_valid = df[~is_rejected].drop(columns='invalid').copy()
    df_rejected = df[is_rejected].copy()

    return df_valid, df_rejected
