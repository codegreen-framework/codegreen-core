import os
import json
import redis
import pandas as pd
from datetime import datetime, timedelta

from ..utilities.config import Config
from ..utilities import metadata as meta

from . import entsoe as et
from ..utilities.log import log_stuff


def _get_redis_client(redis_url):
    try:
        return redis.from_url(redis_url, decode_responses=True)
    except redis.RedisError as e:
        print(f"Redis connection error: {e}")
        return None
    

def _get_key_from_redis(redis_url, key):
    client = _get_redis_client(redis_url)
    if client:
        try:
            return client.get(key)  # Returns None if key does not exist
        except redis.RedisError as e:
            print(f"Redis error: {e}")
    return None


def _set_key_in_redis(redis_url, key, value, expiry=None):
    client = _get_redis_client(redis_url)
    if client:
        try:
            if expiry:
                client.set(key, value, ex=expiry)  # Set key with expiry
            else:
                client.set(key, value)  # Set key without expiry
        except redis.RedisError as e:
            print(f"Redis error: {e}")


def _get_country_key(country_code):
    """Returns the key name for the given country to be stored in redis cache"""
    return "codegreen_generation_public_data_"+ country_code

def _round_to_nearest_hour(dt):
    """ Rounds a given datetime to the nearest hour."""
    return dt.replace(minute=0, second=0, microsecond=0) 

def _get_time_range(nHours):
    """ Returns a tuple (start_date, end_date) where:  start_date is current datetime minus nHours,  end_date is the current datetime """
    end_date = _round_to_nearest_hour(datetime.now().replace(microsecond=0))
    start_date = end_date - timedelta(hours=nHours)
    return start_date, end_date

def _gather_energy_data(country, start_time, end_time):
    """ Gets energy data form public energy sources (online) """
    energy_data = et.get_actual_production_percentage(country, start_time, end_time,interval60=True)["data"]
    return energy_data

def _get_filtered_data(dataframe, start_time, end_time):
    """Function that returns a tuple (partial: True/False, data: DataFrame/None)  indicating if the data is partially available and the corresponding data.
    """
    if dataframe.empty:
        return (False, None)
    
    # Convert startTime column to datetime
    dataframe["startTime"] = pd.to_datetime(dataframe["startTime"])
    dataframe["startTime"] = dataframe["startTime"].dt.tz_localize(None)
    
    # Determine the available data range
    data_start = dataframe["startTime"].min()
    data_end = dataframe["startTime"].max()
    
    start_time_1 = start_time.replace(minute=0, second=0, microsecond=0)
    end_time_1 = end_time.replace(minute=0, second=0, microsecond=0)
    
    # Check different cases for data availability
    if end_time_1 < data_start or start_time_1 > data_end:
        return (False, None)  # No data available
    
    filtered_df = dataframe[(dataframe["startTime"] >= start_time_1) & (dataframe["startTime"] <= end_time_1)]
    
    partial = not (start_time_1 >= data_start and end_time_1 <= data_end)
    
    return (partial, filtered_df if not filtered_df.empty else None)


def _sync_offline_file(country):
    if not Config.get("enable_offline_energy_generation"):
        raise Exception("This method cannot be used to get data since enable_offline_energy_generation option is not enabled")
    
    # print("syncs offline file for the given country")
    time_config = Config.get("offline_data_start_date")
    # print(time_config)
    start_time = datetime.strptime(time_config,"%Y-%m-%d")
    base_dir = Config.get("offline_data_dir_path")
    os.makedirs(base_dir, exist_ok=True)

    json_file_path = os.path.join(base_dir, f"{country}_status.json")
    csv_file_path = os.path.join(base_dir, f"{country}_generation.csv")

    current_time = datetime.now()
    # storing data from 5 hours from now.
    end_time =   _round_to_nearest_hour(current_time) - timedelta(hours=5)
    print(country)
    print("Checking for file ",json_file_path)
    if not (os.path.exists(json_file_path) and os.path.exists(csv_file_path)):
        print("Files do not exist. Gathering new data.")
        try:
          data = _gather_energy_data(country, start_time, end_time)
          if data :   
            data.to_csv(csv_file_path, index=False)
            first_start_time1 = data.iloc[0]["startTime"]
            last_start_time1 = data.iloc[-1]["startTime"]
            metadata = {
                "country": country,
                "first_start_time": int(first_start_time1.timestamp()),
                "last_start_time": int(last_start_time1.timestamp()),
                "created_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message" : f"Data ranges from {first_start_time1.strftime('%Y-%m-%d %H:%M:%S')} to {last_start_time1.strftime('%Y-%m-%d %H:%M:%S')}"

            }
            with open(json_file_path, "w") as f:
                json.dump(metadata, f, indent=4)
            log_stuff("Successfully created new offline file for "+country)
            return data
          else:
              print("Data not available") 
        except Exception as e:
            print(e)
    else:
        print("Files exist. Updating data.")
        with open(json_file_path, "r") as f:
            metadata = json.load(f)

        current_start_time = datetime.fromtimestamp(metadata["first_start_time"])   
        current_end_time = datetime.fromtimestamp(metadata["last_start_time"])   + timedelta(hours=1)
        start_diff = current_start_time - start_time
        end_diff = end_time - current_end_time
        df = pd.read_csv(csv_file_path)
        
        update_required = False
        if start_diff.total_seconds() > 0:
            print("Gathering missing data before current start time in the file.")
            new_data = _gather_energy_data(country, start_time, current_start_time )
            df = pd.concat([new_data, df], ignore_index=True)
            update_required = True
        if end_diff.total_seconds() > 0:
            try:
                print("Gathering missing data after current end time in the file.")
                new_data = _gather_energy_data(country, current_end_time, end_time)
                #print(new_data)
                if new_data is not None : 
                    df = pd.concat([df, new_data], ignore_index=True)
                    update_required = True
                else : 
                    print("  No new data available")
            except Exception as e : 
                print("Error in fetching current data. This is possibly because there is no new data to fetch.")
                print(e)

        if update_required:
          df["startTime"] = pd.to_datetime(df["startTime"])
          df = df.sort_values(by="startTime")
          df.to_csv(csv_file_path, index=False)
          first_start_time = df.iloc[0]["startTime"]
          last_start_time = df.iloc[-1]["startTime"]
          metadata["first_start_time"] = int(first_start_time.timestamp())
          metadata["last_start_time"] = int(last_start_time.timestamp())
          metadata["updated_on"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          metadata["message"] = f"Data ranges from {first_start_time.strftime('%Y-%m-%d %H:%M:%S')} to {last_start_time.strftime('%Y-%m-%d %H:%M:%S')}"
          with open(json_file_path, "w") as f:
            json.dump(metadata, f, indent=4)
          log_stuff("Successfully synced offline file for "+country)
        else:
            print("No update required")
    #last_72_hours = end_time - timedelta(hours=72)
    #recent_data = df[pd.to_datetime(df["timestamp"]) >= last_72_hours]
    

def _sync_offline_cache(country):
    # print("syncs offline cache for the given country")
    if not Config.get("enable_energy_caching"):
        raise Exception("This method cannot be used to get data since enable_energy_caching option is not enabled")
    
    c_key = _get_country_key(country)
    hour_count = int(Config.get("generation_cache_hour")) 
    quarter_time = hour_count/4
    data = _get_key_from_redis(Config.get("energy_redis_path"),c_key)
    update_required = False
    s,e = _get_time_range(hour_count)
    if data is not None:
        metadata = json.loads(data)
        dataframe = pd.DataFrame.from_dict(metadata["dataframe"])
        dataframe["startTime"] = pd.to_datetime(dataframe["startTime"]) 
        last_start_time = pd.to_datetime(dataframe.iloc[-1]["startTime"])
        # Calculate the difference in hours
        time_difference = abs((e - last_start_time).total_seconds()) / 3600
        if quarter_time <= time_difference :
            update_required = True           
    else:
        update_required = True
        
    if update_required  :
        # todo  :  see if offline data have the required data 
        dataframe = _gather_energy_data(country,s,e)
        dataframe["startTime"] = pd.to_datetime(dataframe["startTime"])
        dataframe["startTime"] = dataframe["startTime"].dt.tz_localize(None)
        metadata = {
            "country": country,
            "first_start_time": int(dataframe.iloc[0]["startTime"].timestamp()),
            "last_start_time": int(dataframe.iloc[-1]["startTime"].timestamp()),
            "created_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dataframe":dataframe.to_dict()
          }
        _set_key_in_redis(Config.get("energy_redis_path"),c_key,json.dumps(metadata, default=str))


def _get_offline_file_data(country,start_time, end_time):
    """
    Returns energy generation data stored in offline file for the given country for the give time range
    This assumes data files already exists and synced with latest data
    Returns a tuple (partial: True/False, data: DataFrame/None)  indicating if the data is partially available and the corresponding data.
    """
    if not Config.get("enable_offline_energy_generation"):
        raise Exception("This method cannot be used to get data since enable_offline_energy_generation option is not enabled")
    base_dir = Config.get("offline_data_dir_path")
    os.makedirs(base_dir, exist_ok=True)

    if not Config.get("enable_offline_energy_generation"):
        raise Exception("This method cannot be used to get data since enable_offline_energy_generation option is not enabled")
    
    json_file_path = os.path.join(base_dir, f"{country}_status.json")
    csv_file_path = os.path.join(base_dir, f"{country}_generation.csv")

    if not (os.path.exists(json_file_path) and os.path.exists(csv_file_path)):
        return (False, None)
    
    local_data = pd.read_csv(csv_file_path)
    return _get_filtered_data(local_data, start_time, end_time)


def _get_offline_cache_data(country,start,end):
    print("offline cache data")
    if not Config.get("enable_energy_caching"):
        raise Exception("This method cannot be used to get data since enable_energy_caching option is not enabled")
    data = _get_key_from_redis(Config.get("energy_redis_path"),_get_country_key(country))
    # print(data)
    if data is not None:
        metadata = json.loads(data)
        # print(metadata)
        dataframe = pd.DataFrame.from_dict(metadata["dataframe"])
        dataframe["startTime"] = pd.to_datetime(dataframe["startTime"])  # Converts to pandas.Timestamp
        return _get_filtered_data(dataframe, start, end)
    else:
        return False,None
        

def get_offline_data(country,start,end,sync_first=False)->dict:
    """
    This method returns locally stored energy data.

    Data is stored in two sources:

    1. **Redis cache**: Contains data for a limited number of hours from the last sync.
    2. **CSV files**: Contain data for longer durations.

    Both storage options can be configured in the configuration file.

    **Note**: Unless you specify the ``sync_first`` flag, the method assumes that syncing of the data sources is handled separately. If ``sync_first`` is set to ``True`` and data files are not initialized in advance, the method may take longer to complete

    :return: A dictionary with the following keys:
        - **available** (*bool*): Indicates if the data is available.
        - **data** (*pandas.DataFrame*): The energy data, if available. Otherwise, an empty DataFrame.

    :rtype: dict

    """

    output = {"available":False,"data":None, "partial":False,"source":""}
    offline = Config.get("enable_offline_energy_generation")
    cache =  Config.get("enable_energy_caching")
    
    if offline == False and cache == False :
        # no offline data configured 
        return output
    
    if cache :
        # first look in the cache
        if(sync_first):
            #print("will first sync the cache to get the latest data")
            _sync_offline_cache(country)
        partial,data = _get_offline_cache_data(country,start,end)   
        if data is not None and partial is False:
            output["partial"] = partial
            output["data"] = data
            output["available"] = True
            output["source"] = "cache"
            print("data from cache")
            return output
        
    if offline:
        # first look if data files are available, if yes, return data 
        if(sync_first):
            #print("will first sync the offline files to get the latest data")
            _sync_offline_file(country)
        partial,data = _get_offline_file_data(country,start,end)
        output["partial"] = partial
        output["data"] = data
        output["available"] = True
        output["source"] = "offline_file"
        #print("just got the data from offline file")
    
    return output
    

def sync_offline_data(file=False,cache=False):
    """
    This method syncs offline data for offline sources enabled in the configuration file. The data is synced for all available countries. 
    
    You need to run this method before retrieving offline data. It is also possible to set up a CRON job to call this method at regular intervals to keep data synchronized.
    
    The sync operation can take some time, depending on the data size and the selected sync options (file, cache, or both).

    :param bool file: If ``True``, sync data in offline files. Defaults to ``False``.
    :param bool cache: If ``True``, sync data in the cache. Defaults to ``False``.
    """
    c_keys = meta.get_country_metadata()
    if  Config.get("enable_offline_energy_generation") == True  and file == True:
        for key in c_keys:
            try:
                _sync_offline_file(key)
            except Exception as e:
                log_stuff("Error in syncing offline file for "+key+". Message"+ str(e))
    if  Config.get("enable_energy_caching") == True and cache == True :
        for key in c_keys:
            try:
                _sync_offline_cache(key)
            except Exception as e:
                log_stuff("Error in syncing offline file for "+key+". Message: "+ str(e))
