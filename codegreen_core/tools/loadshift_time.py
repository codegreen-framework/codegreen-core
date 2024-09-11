from datetime import datetime, timedelta, timezone
from dateutil import tz
import numpy as np
import pandas as pd
# from greenerai.api.data.utils import Message
from ..utils.message import Message
from ..utils.log import time_prediction as log_time_prediction
from ..data.metadata import get_country_energy_source
from ..data import  entsoe as e # get_forecast_percent_renewable,get_current_date_entsoe_format,add_hours_to_entsoe_data
from ..data import energy 
from ..utils.config import Config
import redis
import json
import traceback


# ======= Caching energy data in redis ============

def get_country_key(country_code):
    return "codegreen_"+country_code

def get_cache_or_update(country, start, deadline):
    """
    The cache contains an entry for every country. It holds the country code,
    the last update time, the timestamp of the last entry and the data time series.

    The function first checks if the requested final time stamp is available, if not
    it attempts to pull the data from ENTSOE, if the last update time is at least one hour earlier.
    """
    print("get_cache_or_update started")
    cache = redis.from_url(Config.get("energy_redis_path"))
    if cache.exists(get_country_key(country)):
        print("cache has country")
        json_string = cache.get(get_country_key(country)).decode("utf-8")
        data_object = json.loads(json_string)
        last_prediction_time  =  datetime.fromtimestamp(data_object["last_prediction"], tz=timezone.utc) 
        deadline_time =  deadline.astimezone(timezone.utc) # datetime.strptime("202308201230", "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
        last_cache_update_time = datetime.fromtimestamp(data_object["last_updated"], tz=timezone.utc) 
        current_time_plus_one = datetime.now(timezone.utc)+timedelta(hours=-1)
        # utc_dt = utc_dt.astimezone(timezone.utc)  
        # print(data_object)
        if data_object["data_available"] and last_prediction_time > deadline_time:
            return data_object
        else:
            # check if the last update has been at least one hour earlier, 
            if last_cache_update_time < current_time_plus_one:
                print("cache must be updated")
                return pull_data(country, start, deadline)
            else:
                return data_object
    else:
        print("caches has no country, calling pull_data(country, start, deadline)")
        return pull_data(country, start, deadline)


def pull_data(country, start, end):
    """Fetches the data from ENTSOE and updated the cache"""
    print("pull_data function started")
    try:
        cache = redis.from_url(Config.get("energy_redis_path"))
        forecast_data = energy(country,start,end,"forecast")
        # print(forecast_data)
        last_update = datetime.now().timestamp()
        if forecast_data["data_available"]:
            last_prediction = forecast_data["data"].iloc[-1]["posix_timestamp"]
        else:
            last_prediction = pd.Timestamp(datetime.now(), tz="UTC")
        # print(last_prediction)
        # forecast_data["data"]["startTimeUTC"] = forecast_data["data"]['startTimeUTC'].dt.strftime('%Y%m%d%H%M').astype("str")
        df = forecast_data["data"]
        df['startTimeUTC'] = pd.to_datetime(df['startTimeUTC'])
        df['startTimeUTC'] = df['startTimeUTC'].dt.strftime('%Y%m%d%H%M').astype("str")
        cached_object = {
            "data": df.to_dict(),
            "time_interval": forecast_data["time_interval"],
            "data_available": forecast_data["data_available"],
            "last_updated": int(last_update),
            "last_prediction": int(last_prediction),
        }
        cache.set(get_country_key(country), json.dumps(cached_object))
        # print(
        #     "caching object with updated last_update key , result is %s",
        #     str(cached_object),
        # )
        return cached_object

    except Exception as e:
        print(traceback.format_exc())
        print(e)
        return None


# ========= the main methods  ============

def get_energy_data(country,start,end):
    """
    Get energy data and check if it must be cached based on the options set 
    """
    if Config.get("enable_energy_caching")==True: 
        try :
            forecast = get_cache_or_update(country, start, end)
            #print(forecast)
            forecast_data = pd.DataFrame(forecast["data"])
            #print("====")
            #print(forecast_data)
            return forecast_data
        except Exception as e :
            print(traceback.format_exc())
    else: 
        forecast =   energy(country,start,end,"forecast")
        return forecast["data"]

def predict_now(country: str, estimated_runtime_hours: int, estimated_runtime_minutes:int, hard_finish_date:datetime, criteria:str = "percent_renewable", percent_renewable: int = 50)->tuple:
    """
    Predicts optimal computation time in the given location starting now 

    :param country: The country code 
    :type country: str
    :param estimated_runtime_hours: The estimated runtime in hours
    :type estimated_runtime_hours: int
    :param estimated_runtime_minutes: The estimated runtime in minutes 
    :type estimated_runtime_minutes: int
    :param hard_finish_date: The latest possible finish time for the task
    :type hard_finish_date: datetime
    :param criteria: Criteria based on which optimal time is calculated. Valid value "percent_renewable"
    :type criteria: str
    :param percent_renewable: The minimum percentage of renewable energy desired during the runtime
    :type percent_renewable: int    
    :return: Tuple[timestamp, message, average_percent_renewable]
    :rtype: tuple
    
    """
    if criteria == "percent_renewable":
        try:
            start_time = datetime.now()
            energy_data = get_energy_data(country,start_time,hard_finish_date)
            if energy_data is not None :
                return predict_optimal_time(
                    energy_data,
                    estimated_runtime_hours,
                    estimated_runtime_minutes,
                    percent_renewable,
                    hard_finish_date
                )
            else:
                return default_response(Message.ENERGY_DATA_FETCHING_ERROR)
        except Exception as e:
            print(traceback.format_exc())
            return default_response(Message.ENERGY_DATA_FETCHING_ERROR)
    else:
        return default_response(Message.INVALID_PREDICTION_CRITERIA)

# ======= Optimal prediction part =========    

def predict_optimal_time(
    energy_data: pd.DataFrame,
    estimated_runtime_hours: int,
    estimated_runtime_minutes: int,
    percent_renewable: int,
    hard_finish_date: datetime.timestamp,
    request_time : datetime = None
) -> tuple:
    """
    Predicts the optimal time window to run a task based in energy data, run time estimates and renewable energy target.

    :param energy_data: A DataFrame containing the energy data including startTimeUTC, totalRenewable,total,percent_renewable,posix_timestamp
    :param estimated_runtime_hours: The estimated runtime in hours
    :param estimated_runtime_minutes: The estimated runtime in minutes 
    :param percent_renewable: The minimum percentage of renewable energy desired during the runtime
    :param hard_finish_date: The latest possible finish time for the task
    :param request_time: The time at which the prediction is requested. Defaults to None, then the current time is used

    :return: Tuple[timestamp, message, average_percent_renewable]
    :rtype: tuple
    """

    granularity =  60 # assuming that the granularity of time series is 60 minutes
    
    #  ============ data validation   =========
    if not isinstance(hard_finish_date,datetime):
        raise ValueError("Invalid hard_finish_date. it must be a datetime object")

    if request_time is not None:
        if not isinstance(request_time,datetime):
            raise ValueError("Invalid request_time. it must be a datetime object")
    if energy_data is None:
        return default_response(Message.NO_DATA,request_time)
    if percent_renewable <= 0:
        return default_response(Message.NEGATIVE_PERCENT_RENEWABLE,request_time)
    if estimated_runtime_hours <= 0:
        # since energy data is for 60 min interval, it does not make sense to optimize jobs less than an hour
        return default_response(Message.INVALID_DATA,request_time)
    if estimated_runtime_minutes < 0:
        # min val can be 0 
        return default_response(Message.INVALID_DATA,request_time)
    
    total_runtime_in_minutes = estimated_runtime_hours * 60 + estimated_runtime_minutes

    if total_runtime_in_minutes <= 0:
        return default_response(Message.ZERO_OR_NEGATIVE_RUNTIME,request_time)
        
    if request_time is None:
      # request time will be the current time 
      # dial back by 60 minutes to avoid waiting unnecessarily for the next full quarterhour.
      current_time = int((datetime.now(timezone.utc) - timedelta(minutes=granularity)).timestamp())
      estimated_finish_time = int((datetime.now(timezone.utc) + timedelta(minutes=total_runtime_in_minutes)).timestamp())      
    else :
      # else, the current time value is the request time converted to utc time stamp
      request_time_utc =  request_time.astimezone(tz.tzutc())
      current_time = (request_time_utc - timedelta(minutes=granularity)).timestamp()
      estimated_finish_time = (request_time_utc + timedelta(minutes=total_runtime_in_minutes)).timestamp()

    #print(estimated_finish_time)
    #print(type(estimated_finish_time))
    #print(estimated_finish_time, int(hard_finish_date.timestamp()))
    if estimated_finish_time >= int(hard_finish_date.timestamp()):
        return default_response(Message.RUNTIME_LONGER_THAN_DEADLINE_ALLOWS,request_time)


    # ========== the predication part ===========
    # this is to make the old code from the web repo compatible with the new one. TODO refine it 
    my_predictions = energy_data
    
    # Reduce data to the relevant time frame
    my_predictions = my_predictions[my_predictions["posix_timestamp"] >= current_time]
    my_predictions = my_predictions[my_predictions["posix_timestamp"] <= hard_finish_date.timestamp()]

    # Possible that data has not been reported
    if my_predictions.shape[0] == 0:
        return default_response(Message.NO_DATA,request_time)

    my_predictions = my_predictions.reset_index()

    # needs to be computed every time, because when time runs, the number of
    # renewable timeslots above a certain threshold is reduced.
    # This can potentially be improved to avoid duplicate computation all the
    # time but for now it is easy
    time_units = (total_runtime_in_minutes // granularity) + 1

    my_predictions = compute_percentages(my_predictions, percent_renewable)
    my_predictions = compute_rolling_average(
        my_predictions=my_predictions, time_units=time_units
    )
    # how many time units do I need to allocate?
    # returns the position of the cumulative quarterhour count
    column_name = "windows" + str(percent_renewable)

    # Try to find the optimal time
    # Follow the requirement blindly
    # index of starting time fullfilling the requirements
    time_slot = my_predictions[column_name].ge(time_units).argmax() - (time_units - 1)

    #print("time_slot is: " + str(time_slot))
    #print("time_slot is: " + str(time_slot))

    # print(f"time_slot = {time_slot}")
    # print(f"timeunits: {time_units}")
    # return the maximum
    alternative_time = -1
    n = my_predictions.shape[0]
    pointer = 0

    if time_units < n:
        alternative_time = my_predictions["rolling_average_pr"][
            (time_units - 1) : n
        ].argmax() - (time_units - 1)
    else:
        alternative_time = time_slot

    potential_times = {
        "requirement_fulfilled": {"time_index": time_slot},
        "max_percentage": {"time_index": alternative_time},
    }
    print(f"alternative = {alternative_time}")

    for potential_time in potential_times:
        if potential_times[potential_time]["time_index"] >= 0:
            potential_times[potential_time][
                "avg_percentage_renewable"
            ] = my_predictions["rolling_average_pr"][time_slot + time_units - 1]

    if (
        0
        < potential_times["max_percentage"]["time_index"]
        < potential_times["requirement_fulfilled"]["time_index"]
    ) and potential_times["max_percentage"][
        "avg_percentage_renewable"
    ] > potential_times[
        "requirement_fulfilled"
    ][
        "avg_percentage_renewable"
    ]:
        print("Return max percent")
        return optimal_response(
            my_predictions, potential_times["max_percentage"]["time_index"], time_units
        )

    # If there is a window which fulfills the request, return this window.
    if potential_times["requirement_fulfilled"]["time_index"] >= 0:
        print("returning requested timeslot")
        return optimal_response(my_predictions, time_slot, time_units)
    elif potential_times["max_percentage"]["time_index"] >= 0:
        print("returning optimum")

        return optimal_response(my_predictions, alternative_time, time_units)
    else:
        return optimal_response(my_predictions, 0, time_units)


def optimal_response(my_predictions, time_slot, time_units):
    # print("optimal_response function started, data/prediction.py")
    average_percent_renewable = my_predictions["percent_renewable"][
        time_slot : (time_slot + time_units)
    ].mean()
    timestamp = datetime.fromtimestamp(
        my_predictions.posix_timestamp.iloc[time_slot]
    ).timestamp()
    message = Message.OPTIMAL_TIME
    return timestamp, message, average_percent_renewable


def default_response(message,request_time=None):
    average_percent_renewable = 0
    if request_time is None :
        timestamp = int(datetime.now(timezone.utc).timestamp())
    else :
        timestamp = int(request_time.timestamp())
    
    return timestamp, message, average_percent_renewable

def compute_percentages(my_predictions, percent_renewable):
    """
    Compute the percentage of renewables requested.
    This creates a column with the cumulative number of timeslots
    over a certain threshold called eg. windows_0.1 for 0.1 renewable
    energy.
    """
    # for percent_renewable in [0.1, 0.2, 0.3, 0.4, 0.5,
    #  0.6, 0.7, 0.8, 0.9, 1.0]:
    column_name = "above_threshold" + str(percent_renewable)
    # True false column whether percentage of renewables is high enough.
    my_predictions[column_name] = (
        my_predictions["percent_renewable"] > percent_renewable
    )
    # Cummulative number of consequtive quarterhours at the given threshold
    cumsum = 0
    new_colum = []
    binarized_column = list(my_predictions[column_name])
    # Count number of true values
    for p in binarized_column:
        # reset if no value
        if np.isnan(p):
            cumsum = 0
        # count +1 if true
        elif int(p) == 1:
            cumsum = cumsum + 1
        # reset to zero if false
        else:
            cumsum = 0
        # append current cumulative value to the data frame
        new_colum.append(cumsum)

    # append this column as a new column in the data frame and return.
    my_predictions["windows" + str(percent_renewable)] = new_colum
    return my_predictions


def compute_rolling_average(
    my_predictions: pd.DataFrame, time_units: int
) -> pd.DataFrame:
    """Compute the rolling average over the number of time units.

    :param my_predictions: prediction data frame to compute the rolling average for
    :type my_predictions: pd.DataFrame
    :return: pandas data frame with the new column
    :rtype: pd.DataFrame
    """
    if not my_predictions is None:
        my_predictions["rolling_average_pr"] = (
            my_predictions["percent_renewable"]
            .rolling(time_units, min_periods=1)
            .mean()
        )
    if "percent_renewable" not in my_predictions.columns:
        return my_predictions
    return my_predictions
