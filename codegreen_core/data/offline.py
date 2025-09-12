import redis
import json
import pandas as pd
from datetime import datetime, timedelta, timezone

from codegreen_core.utilities.config import Config
from codegreen_core.data.entsoe import get_entsoe_production_percentage, get_entsoe_forecast_percent_renewable

def _get_redis_client(redis_url: str) -> object:
    """
    Get the redis client.

    :param str redis_url:
        redis database URL.
    
    :return: Redis client for the given redis_url.
    """
    try:
        return redis.from_url(redis_url, decode_responses=True)
    except redis.RedisError as e:
        print(f"Redis connection error: {e}")
        return None


def _get_data_from_redis(redis_url: str, key: str) -> object:
    """
    Retrieve data from redis database.

    :param str redis_url:
        Redis database url.
    :param str key:
        Key in redis database to retrieve data from.

    :return: Data for the given key.
    """
    client = _get_redis_client(redis_url)
    if client:
        try:
            data = client.get(key)
            return data  # Returns None if key does not exist
        except redis.RedisError as e:
            print(f"Redis error: {e}")
    return None


def _get_country_key_generation(country_code: str) -> str:
    """
    Get the key name for the given country in the redis cache for the generation data.

    :param country_code str:
        2 letter country code.
    
    :return: Key name for the given country in the redis cache.
    :rtype: str
    """
    return "codegreen_generation_public_data_"+ country_code

def _get_country_key_forecast(country_code: str) -> str:
    """
    Get the key name for the given country in the redis cache for the forecast data.

    :param country_code str:
        2 letter country code.
    
    :return: Key name for the given country in the redis cache.
    :rtype: str
    """
    return "codegreen_forecast_public_data_"+ country_code


def _set_key_in_redis(redis_url: str, key: str, value: object) -> None:
    """
    Set the key in redis cache.
    
    :param str redis_url:
        Redis database url.
    :param key str:
        Key to be stored in redis database.
    :param value object:
        Value to be stored in redis database for the key.
    """
    client = _get_redis_client(redis_url)
    if client:
        try:
            client.set(key, value)
        except redis.RedisError as e:
            print(f"Redis error: {e}")


def _get_cache_data(country: str, start_time: datetime, end_time: datetime, type: str, timestamp_now: datetime = datetime.now(timezone.utc)) -> pd.DataFrame:
    """
    Get cache data.
    
    :param str country:
        2 letter country code.
    :param datetime start_time:
        The start date for data retrieval.
    :param datetime end_time:
        The end date for data retrieval.

    :return: Cached data filtered to the timeframe defined by start_time and end_time.
    :rtype: pandas.DataFrame
    """

    cache_end = _get_data_from_redis(
        Config.REDIS_PATH,
        f"{country}_cache_timestamp"
    )
    
    # Cache has never been loaded or cache is not up to date (last update was over an hour ago) --> update cache
    if (cache_end is None) or (timestamp_now - datetime.fromisoformat(json.loads(cache_end)["timestamp"]) > pd.Timedelta(hours=1)):
        _sync_offline_cache(country)
    
    if type == "generation":
        c_key = _get_country_key_generation(country)
    elif type == "forecast":
        c_key = _get_country_key_forecast(country) 
    
    cache_data = pd.DataFrame.from_dict(json.loads(_get_data_from_redis(
        Config.REDIS_PATH,
        c_key
    ))["dataframe"]).set_index("startTimeUTC")
    cache_data.index = cache_data.index.map(datetime.fromisoformat)

    return cache_data.loc[(cache_data.index >= start_time) & (cache_data.index <= end_time)]


def _sync_offline_cache(country: str, timestamp_now: datetime = datetime.now(timezone.utc)) -> None:
    """
    Synchronizes the offline cache.

    :param str country:
        2 letter country code.
    """

    timestamp_now_hour_rounded = timestamp_now.replace(minute=0, second=0, microsecond=0)

    # Get time intervals to sync cache    
    start_time_production = timestamp_now_hour_rounded - timedelta(hours=Config.GENERATION_CACHE_HOUR)
    end_time_forecast = timestamp_now_hour_rounded + timedelta(hours=Config.FORECAST_CACHE_HOUR)

    # Save generation data
    entsoe_generation_data = get_entsoe_production_percentage(
        country, 
        start_time_production,
        timestamp_now_hour_rounded
    )
    entsoe_generation_data.reset_index(names="startTimeUTC", inplace=True)
    cache_generation_data = {"dataframe": entsoe_generation_data.to_dict()}
    _set_key_in_redis(
        Config.REDIS_PATH,
        _get_country_key_generation(country),
        json.dumps(cache_generation_data, default=str)
    )

    # Save forecast data
    entsoe_forecast_data = get_entsoe_forecast_percent_renewable(
        country,
        timestamp_now_hour_rounded,
        end_time_forecast
    )
    entsoe_forecast_data.reset_index(names="startTimeUTC", inplace=True)
    cache_forecast_data = {"dataframe": entsoe_forecast_data.to_dict()}
    _set_key_in_redis(
        Config.REDIS_PATH,
        _get_country_key_forecast(country),
        json.dumps(cache_forecast_data, default=str)
    )

    # Save timestamp
    cache_timestamp = {"timestamp": timestamp_now}
    _set_key_in_redis(
        Config.REDIS_PATH,
        f"{country}_cache_timestamp", 
        json.dumps(cache_timestamp, default=str)
    )
