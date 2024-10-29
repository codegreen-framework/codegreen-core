import os
from pathlib import Path
from tensorflow.keras.models import load_model
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from sklearn.preprocessing import StandardScaler

from ..utilities.metadata import get_prediction_model_details


# Path to the models directory
models_dir = Path(__file__).parent / "files"


def predicted_energy(country):
    # do the forecast from now , same return format as data.energy
    return {"data": None}


# Function to load a specific model by name
def _load_prediction_model(country, version=None):
    """Load a model by name"""
    model_details = get_prediction_model_details(country, version)
    model_path = models_dir / model_details["name"]
    print(model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Model does not exist.")

    return load_model(model_path, compile=False)


def _run(country, input, model_version=None):
    """Returns the prediction values"""

    seq_length = len(input)
    date = input[["startTimeUTC"]].copy()
    # Convert 'startTimeUTC' column to datetime
    date["startTimeUTC"] = pd.to_datetime(date["startTimeUTC"])
    # Get the last date value
    last_date = date.iloc[-1]["startTimeUTC"]
    # Calculate the next hour
    next_hour = last_date + timedelta(hours=1)
    # Create a range of 48 hours starting from the next hour
    next_48_hours = pd.date_range(next_hour, periods=48, freq="h")
    # Create a DataFrame with the next 48 hours
    next_48_hours_df = pd.DataFrame(
        {"startTimeUTC": next_48_hours.strftime("%Y%m%d%H%M")}
    )

    model_details = get_prediction_model_details(country, model_version)

    lstm = load_prediction_model(
        country, model_version
    )  # load_model(model_path,compile=False)

    scaler = StandardScaler()
    percent_renewable = input["percentRenewable"]
    forecast_values_total = []
    prev_values_total = percent_renewable.values.flatten()
    for _ in range(48):
        scaled_prev_values_total = scaler.fit_transform(
            prev_values_total.reshape(-1, 1)
        )
        x_pred_total = scaled_prev_values_total[-(seq_length - 1) :].reshape(
            1, (seq_length - 1), 1
        )
        # Make the prediction using the loaded model
        predicted_value_total = lstm.predict(x_pred_total, verbose=0)
        # Inverse transform the predicted value
        predicted_value_total = scaler.inverse_transform(predicted_value_total)
        forecast_values_total.append(predicted_value_total[0][0])
        prev_values_total = np.append(prev_values_total, predicted_value_total)
        prev_values_total = prev_values_total[1:]
    # Create a DataFrame
    forecast_df = pd.DataFrame(
        {
            "startTimeUTC": next_48_hours_df["startTimeUTC"],
            "percentRenewableForecast": forecast_values_total,
        }
    )
    forecast_df["percentRenewableForecast"] = (
        forecast_df["percentRenewableForecast"].round().astype(int)
    )
    forecast_df["percentRenewableForecast"] = forecast_df[
        "percentRenewableForecast"
    ].apply(lambda x: 0 if x <= 0 else x)

    input_percentage = input["percentRenewable"].tolist()
    input_start = input.iloc[0]["startTimeUTC"]
    input_end = input.iloc[-1]["startTimeUTC"]

    return {
        "input": {
            "country": country,
            "model": model_details["name"],
            "percentRenewable": input_percentage,
            "start": input_start,
            "end": input_end,
        },
        "output": forecast_df,
    }
