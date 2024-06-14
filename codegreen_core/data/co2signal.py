import requests
from datetime import datetime, timezone
from ..utils.config import Config

def get_co2_intensity(CC):
    CO2_SIGNAL_TOKEN = Config.get("CO2_SIGNAL_TOKEN")
    url = f"https://api.co2signal.com/v1/latest?countryCode={CC}"
    response = requests.request(
        "GET", url, headers={"auth-token": CO2_SIGNAL_TOKEN}, data={}
    )
    data = response.json()

    if data["status"] == "ok":
        data = data["data"]
        data["coutry_code"] = CC
        if "carbonIntensity" not in data.keys():
            data["carbonIntensity"] = -1
        if "fossilFuelPercentage" not in data.keys():
            data["fossilFuelPercentage"] = -1
        if "datetime" not in data.keys():
            # Get the current UTC time
            current_time_utc = datetime.now(timezone.utc)
            # Format the datetime object to the required string format
            timestamp_string = current_time_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            data["datetime"] = timestamp_string
        return data
    else:
        print("Error fetching data")
