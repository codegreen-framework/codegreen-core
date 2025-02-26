from datetime import datetime, timedelta, timezone
from dateutil import tz
import pandas as pd
from ..data import energy
from ..models.predict import predicted_energy
from .config import Config
from .metadata import check_prediction_model_exists
import redis
import json
import traceback
import warnings


def _get_country_key(country_code, energy_mode="pubic_data"):
    return "codegreen_optimal_" + energy_mode + "_" + country_code


def get_cache_or_update(country, start, deadline, energy_mode="public_data"):
    """
    The cache contains an entry for every country. It holds the country code,
    the last update time, the timestamp of the last entry and the data time series.

    The function first checks if the requested final time stamp is available, if not
    it attempts to pull the data from ENTSOE, if the last update time is at least one hour earlier.
    """
    cache = redis.from_url(Config.get("energy_redis_path"))
    if cache.exists(_get_country_key(country, energy_mode)):
        print("cache has country")
        json_string = cache.get(_get_country_key(country, energy_mode)).decode("utf-8")
        data_object = json.loads(json_string)
        last_prediction_time = datetime.fromtimestamp(
            data_object["last_prediction"], tz=timezone.utc
        )
        deadline_time = deadline.astimezone(
            timezone.utc
        )  # datetime.strptime("202308201230", "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
        last_cache_update_time = datetime.fromtimestamp(
            data_object["last_updated"], tz=timezone.utc
        )
        current_time_plus_one = datetime.now(timezone.utc) + timedelta(hours=-1)
        # utc_dt = utc_dt.astimezone(timezone.utc)
        # print(data_object)
        if data_object["data_available"] and last_prediction_time > deadline_time:
            return data_object
        else:
            # check if the last update has been at least one hour earlier,
            if last_cache_update_time < current_time_plus_one:
                print("cache must be updated")
                return _pull_data(country, start, deadline, energy_mode)
            else:
                return data_object
    else:
        print("caches has no country, calling _pull_data(country, start, deadline)")
        # print(energy_mode)
        return _pull_data(country, start, deadline, energy_mode)


def _pull_data(country, start, end, energy_mode="public_data"):
    """Fetches the data  and updates the cache"""
    print("_pull_data function started")
    try:
        cache = redis.from_url(Config.get("energy_redis_path"))
        if energy_mode == "public_data":
            forecast_data = energy(country, start, end, "forecast")
        elif energy_mode == "local_prediction":
            if check_prediction_model_exists(country):
                forecast_data = predicted_energy(country)
            else:
                warnings.warn(
                    "Predication model for " + country + " do not exist in the system."
                )
                return None
        else:
            return None
        last_update = datetime.now().timestamp()
        #if forecast_data["data_available"]:
        #    last_prediction = forecast_data["data"].iloc[-1]["startTimeUTC"]
        #else:
        #    last_prediction = pd.Timestamp(datetime.now(), tz="UTC")

        df = forecast_data["data"]
        del df["startTime"]  
        df["startTimeUTC"] = pd.to_datetime(df["startTimeUTC"])
        df["startTimeUTC"] = df["startTimeUTC"].dt.strftime("%Y%m%d%H%M").astype("str")
        last_col = forecast_data["data"].iloc[-1]["startTimeUTC"]
        last_prediction = int(datetime.strptime(last_col, "%Y%m%d%H%M").timestamp())
        cached_object = {
            "data": df.to_dict(),
            "time_interval": forecast_data["time_interval"],
            "data_available": forecast_data["data_available"],
            "last_updated": int(last_update),
            "last_prediction": int(last_prediction),
        }
        #print(cached_object)
        cache.set(_get_country_key(country, energy_mode), json.dumps(cached_object))
        return cached_object

    except Exception as e:
        print(traceback.format_exc())
        print(e)
        return None
