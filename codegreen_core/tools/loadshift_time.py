from datetime import datetime, timedelta, timezone
from dateutil import tz
import numpy as np
import pandas as pd

# from greenerai.api.data.utils import Message
from ..utilities.message import Message
from ..utilities.metadata import check_prediction_model_exists
from ..utilities.caching import get_cache_or_update
from ..data import energy
from ..models.predict import predicted_energy
from ..utilities.config import Config
import redis
import json
import traceback

# ========= the main methods  ============


def _get_energy_data(country, start, end):
    """
    Get energy data and check if it must be cached based on the options set

    Check the country data file if models exists
    """
    energy_mode = Config.get("default_energy_mode")
    if Config.get("enable_energy_caching") == True:
        # check prediction is enabled : get cache or update prediction
        try:
            # what if this fails ?
            forecast = get_cache_or_update(country, start, end, energy_mode)
            forecast_data = pd.DataFrame(forecast["data"])
            return forecast_data
        except Exception as e:
            print(traceback.format_exc())
    else:
        if energy_mode == "local_prediction":
            if check_prediction_model_exists(country):
                forecast = predicted_energy(country)
            else:
                # prediction models do not exists , fallback to energy forecasts from public_data
                forecast = energy(country, start, end, "forecast")
        elif energy_mode == "public_data":
            forecast = energy(country, start, end, "forecast")
            # print(forecast)
        else:
            return None
        return forecast["data"]


def predict_now(
    country: str,
    estimated_runtime_hours: int,
    estimated_runtime_minutes: int,
    hard_finish_date: datetime,
    criteria: str = "percent_renewable"
) -> tuple:
    """
    Predicts optimal computation time in the given location starting now

    :param country: The country code
    :type country: str
    :param estimated_runtime_hours: The estimated runtime in hours
    :type estimated_runtime_hours: int
    :param estimated_runtime_minutes: The estimated runtime in minutes
    :type estimated_runtime_minutes: int
    :param hard_finish_date: The latest possible finish time for the task. Datetime object in local time zone
    :type hard_finish_date: datetime
    :param criteria: Criteria based on which optimal time is calculated. Valid value "percent_renewable" or "optimal_percent_renewable"
    :type criteria: str
    :return: Tuple[timestamp, message, average_percent_renewable]
    :rtype: tuple

    **Example usage**:

    .. code-block:: python
    
        from datetime import datetime,timedelta 
        from codegreen_core.tools.loadshift_time import predict_now

        country_code = "DK"
        est_runtime_hour = 10
        est_runtime_min = 0
        now = datetime.now()
        hard_finish_date = now + timedelta(days=1)
        criteria = "percent_renewable"
        per_renewable = 50 

        time = predict_now(country_code,
                            est_runtime_hour,
                            est_runtime_min,
                            hard_finish_date,
                            criteria,
                            per_renewable)
        # (1728640800.0, <Message.OPTIMAL_TIME: 'OPTIMAL_TIME'>, 76.9090909090909)
    

    """
    if criteria == "percent_renewable":
        try:
            start_time = datetime.now()
            # print(start_time,hard_finish_date)
            energy_data = _get_energy_data(country, start_time, hard_finish_date)
            # print(energy_data)
            if energy_data is not None:
                return predict_optimal_time(
                    energy_data,
                    estimated_runtime_hours,
                    estimated_runtime_minutes,
                    hard_finish_date
                )
            else:
                return _default_response(Message.ENERGY_DATA_FETCHING_ERROR)
        except Exception as e:
            print(traceback.format_exc())
            return _default_response(Message.ENERGY_DATA_FETCHING_ERROR)
    else:
        return _default_response(Message.INVALID_PREDICTION_CRITERIA)


# ======= Optimal prediction part =========


def predict_optimal_time(
    energy_data: pd.DataFrame,
    estimated_runtime_hours: int,
    estimated_runtime_minutes: int,
    hard_finish_date: datetime,
    request_time: datetime = None,
) -> tuple:
    """
    Predicts the optimal time window to run a task based in energy data, run time estimates and renewable energy target.

    :param energy_data: A DataFrame containing the energy data including startTimeUTC, totalRenewable,total,percent_renewable,posix_timestamp
    :param estimated_runtime_hours: The estimated runtime in hours
    :param estimated_runtime_minutes: The estimated runtime in minutes
    :param hard_finish_date: The latest possible finish time for the task.
    :param request_time: The time at which the prediction is requested. Defaults to None, then the current time is used. Assumed to be in local timezone

    :return: Tuple[timestamp, message, average_percent_renewable]
    :rtype: tuple
    """

    granularity = 60  # assuming that the granularity of time series is 60 minutes
    # print(percent_renewable)
    #  ============ data validation   =========
    if not isinstance(hard_finish_date, datetime):
        raise ValueError("Invalid hard_finish_date. it must be a datetime object")

    if request_time is not None:
        if not isinstance(request_time, datetime):
            raise ValueError("Invalid request_time. it must be a datetime object")
    if energy_data is None:
        return _default_response(Message.NO_DATA, request_time)
    percent_renewable =  int(energy_data["percent_renewable"].max())  #assuming we want the max possible percent renewable 
    if percent_renewable <= 0:
        return _default_response(Message.NEGATIVE_PERCENT_RENEWABLE, request_time)
    if estimated_runtime_hours <= 0:
        # since energy data is for 60 min interval, it does not make sense to optimize jobs less than an hour
        return _default_response(Message.INVALID_DATA, request_time)
    if estimated_runtime_minutes < 0:
        # min val can be 0
        return _default_response(Message.INVALID_DATA, request_time)

    total_runtime_in_minutes = estimated_runtime_hours * 60 + estimated_runtime_minutes

    if total_runtime_in_minutes <= 0:
        return _default_response(Message.ZERO_OR_NEGATIVE_RUNTIME, request_time)

    if request_time is not None:
        # request time is provided in local time zone, first convert to utc then use it
        req_time_utc = request_time.astimezone(tz.tzutc())
    else:
        # request time is current time in utc
        req_time_utc = datetime.now(timezone.utc)

    # if req_time_utc.minute  >= granularity/2 :
    #     current_time = (request_time_utc - timedelta(minutes=granularity)).timestamp()
    # else :
    #     current_time = (request_time_utc).timestamp()

    current_time_hour = req_time_utc.replace(minute=0, second=0, microsecond=0)
    current_time = int(current_time_hour.timestamp())

    # dial back by 60 minutes to avoid waiting unnecessarily for the next full quarterhour.
    # current_time = int((datetime.now(timezone.utc) - timedelta(minutes=granularity)).timestamp()) # current time is unix timestamp
    estimated_finish_hour = current_time_hour + timedelta(
        minutes=total_runtime_in_minutes
    )
    estimated_finish_time = int(estimated_finish_hour.timestamp())  # unix timestamp

    print(req_time_utc, current_time_hour, estimated_finish_hour)
    # hard_finish_date is in local time zone  so it's converted to timestamp
    if estimated_finish_time >= int(hard_finish_date.timestamp()):
        return _default_response(
            Message.RUNTIME_LONGER_THAN_DEADLINE_ALLOWS, request_time
        )

    # ========== the predication part ===========
    # this is to make the old code from the web repo compatible with the new one. TODO refine it
    my_predictions = energy_data

    # Reduce data to the relevant time frame
    my_predictions = my_predictions[my_predictions["posix_timestamp"] >= current_time]
    my_predictions = my_predictions[
        my_predictions["posix_timestamp"] <= hard_finish_date.timestamp()
    ]

    # Possible that data has not been reported
    if my_predictions.shape[0] == 0:
        return _default_response(Message.NO_DATA, request_time)

    my_predictions = my_predictions.reset_index()
    # needs to be computed every time, because when time runs, the number of
    # renewable timeslots above a certain threshold is reduced.
    # This can potentially be improved to avoid duplicate computation all the
    # time but for now it is easy
    time_units = (total_runtime_in_minutes // granularity) + 1

    my_predictions = _compute_percentages(my_predictions, percent_renewable)
    my_predictions = _compute_rolling_average(
        my_predictions=my_predictions, time_units=time_units
    )
    # how many time units do I need to allocate?
    # returns the position of the cumulative quarterhour count
    column_name = "windows" + str(percent_renewable)

    # Try to find the optimal time
    # Follow the requirement blindly
    # index of starting time fullfilling the requirements
    time_slot = my_predictions[column_name].ge(time_units).argmax() - (time_units - 1)

    # print("time_slot is: " + str(time_slot))
    # print("time_slot is: " + str(time_slot))

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
            potential_times[potential_time]["avg_percentage_renewable"] = (
                my_predictions["rolling_average_pr"][time_slot + time_units - 1]
            )

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
        return _optimal_response(
            my_predictions, potential_times["max_percentage"]["time_index"], time_units
        )

    # If there is a window which fulfills the request, return this window.
    if potential_times["requirement_fulfilled"]["time_index"] >= 0:
        print("returning requested timeslot")
        return _optimal_response(my_predictions, time_slot, time_units)
    elif potential_times["max_percentage"]["time_index"] >= 0:
        print("returning optimum")

        return _optimal_response(my_predictions, alternative_time, time_units)
    else:
        return _optimal_response(my_predictions, 0, time_units)


def _optimal_response(my_predictions, time_slot, time_units):
    # print("_optimal_response function started, data/prediction.py")
    average_percent_renewable = my_predictions["percent_renewable"][
        time_slot : (time_slot + time_units)
    ].mean()
    timestamp = datetime.fromtimestamp(
        my_predictions.posix_timestamp.iloc[time_slot]
    ).timestamp()
    message = Message.OPTIMAL_TIME
    return timestamp, message, average_percent_renewable


def _default_response(message, request_time=None):
    average_percent_renewable = 0
    if request_time is None:
        timestamp = int(datetime.now(timezone.utc).timestamp())
    else:
        # request time in local time is converted to utc timestamp
        timestamp = int(request_time.timestamp())

    return timestamp, message, average_percent_renewable


def _compute_percentages(my_predictions, percent_renewable):
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


def _compute_rolling_average(
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
