from datetime import datetime, timedelta, timezone
from dateutil import tz
import numpy as np
import pandas as pd
# from greenerai.api.data.utils import Message
from ..utils.message import Message
from ..utils.country_meta import get_country_energy_source
from ..data import  entsoe as e # get_forecast_percent_renewable,get_current_date_entsoe_format,add_hours_to_entsoe_data

def predict_now(
        country: str,
        estimated_runtime_hours: int,
        estimated_runtime_minutes:int,
        hard_finish_date:datetime,
        criteria:str = "percent_renewable",
        percent_renewable: int = 50,
):
    if criteria == "percent_renewable":
        e_source = get_country_energy_source(country)
        if e_source == "ENTSOE":
          start_time = e.get_current_date_entsoe_format()
          # print(start_time)
          end_time = e.add_hours_to_entsoe_data(start_time,24)
          # print(end_time)
          energy_data = e.get_forecast_percent_renewable(country,start_time,end_time)
          # print(energy_data[["percent_renewable","posix_timestamp","startTimeUTC"]])
          return predict_optimal_time(
              energy_data,
              estimated_runtime_hours,
              estimated_runtime_minutes,
              percent_renewable,
              hard_finish_date
          )
        else :
          return default_response(Message.COUNTRY_404)
    else:
        return default_response(Message.INVALID_PREDICTION_CRITERIA)
    

def predict_optimal_time(
    energy_data: pd.DataFrame,
    estimated_runtime_hours: int,
    estimated_runtime_minutes: int,
    percent_renewable: int,
    hard_finish_date: datetime,
    granularity: int = 60,
    request_time : datetime = None,
):
    # check if data is available
    if energy_data is None:
        return default_response(Message.NO_DATA)
    
    total_runtime_in_minutes = estimated_runtime_hours * 60 + estimated_runtime_minutes
    
    if request_time is None:
      # request time will be the current time 
      # dial back by 60 minutes to avoid waiting unnecessarily for the next full quarterhour.
      current_time = (
        datetime.now(timezone.utc) - timedelta(minutes=granularity)
      ).timestamp()

      estimated_finish_time = (
        datetime.now(timezone.utc) + timedelta(minutes=total_runtime_in_minutes)
      ).timestamp()
    else :
      # else, the current time value is the request time converted to utc time stamp
      request_time_utc =  request_time.astimezone(tz.tzutc())

      current_time = (
          request_time_utc - timedelta(minutes=granularity) 
      ).timestamp()
      
      estimated_finish_time = (
        request_time_utc + timedelta(minutes=total_runtime_in_minutes)
      ).timestamp()

    hard_finish_date_utc = hard_finish_date.astimezone(tz.tzutc()).timestamp()
    

    if estimated_finish_time >= hard_finish_date_utc:
        return default_response(Message.RUNTIME_LONGER_THAN_DEADLINE_ALLOWS)
    # Reduce data to the relevant time frame
    energy_data = energy_data[energy_data["posix_timestamp"] >= current_time]
    energy_data = energy_data[
        energy_data["posix_timestamp"] <= hard_finish_date_utc
    ]

    # Possible that data has not been reported
    if energy_data.shape[0] == 0:
        return default_response(Message.NO_DATA)

    energy_data = energy_data.reset_index()

    # needs to be computed every time, because when time runs, the number of
    # renewable timeslots above a certain threshold is reduced.
    # This can potentially be improved to avoid duplicate computation all the
    # time but for now it is easy
    time_units = (total_runtime_in_minutes // granularity) + 1

    energy_data = compute_percentages(energy_data, percent_renewable)
    energy_data = compute_rolling_average(
        energy_data=energy_data, time_units=time_units
    )
    # how many time units do I need to allocate?
    # returns the position of the cumulative quarterhour count
    column_name = "windows" + str(percent_renewable)

    # Try to find the optimal time
    # Follow the requirement blindly
    # index of starting time fullfilling the requirements
    time_slot = energy_data[column_name].ge(time_units).argmax() - (time_units - 1)
    print(f"time_slot = {time_slot}")
    print(f"timeunits: {time_units}")
    # return the maximum
    alternative_time = -1
    n = energy_data.shape[0]
    print(n)
    print(energy_data)
    pointer = 0

    if time_units < n:
        alternative_time = energy_data["rolling_average_pr"][
            (time_units - 1) : n
        ].argmax() - (time_units - 1)
    else:
        alternative_time = time_slot

    potential_times = {
        "requirement_fulfilled": {"time_index": time_slot},
        "max_percentage": {"time_index": alternative_time},
    }
    print(f"alternative = {alternative_time}")
    # print(energy_data)

    print(potential_times)

    for potential_time in potential_times:
        if potential_times[potential_time]["time_index"] >= 0:
            potential_times[potential_time][
                "avg_percentage_renewable"
            ] = energy_data["rolling_average_pr"][time_slot + time_units - 1]

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
            energy_data, ["max_percentage"]["time_index"], time_units
        )

    # If there is a window which fulfills the request, return this window.
    if potential_times["requirement_fulfilled"]["time_index"] >= 0:
        print("returning requested timeslot")
        return optimal_response(energy_data, time_slot, time_units)
    elif potential_times["max_percentage"]["time_index"] >= 0:
        print("returning optimum")
        return optimal_response(energy_data, alternative_time, time_units)
    else:
        return optimal_response(energy_data, 0, time_units)


def optimal_response(energy_data, time_slot, time_units):
    average_percent_renewable = energy_data["percent_renewable"][
        time_slot : (time_slot + time_units)
    ].mean()
    timestamp = datetime.fromtimestamp(
        energy_data.posix_timestamp.iloc[time_slot]
    ).timestamp()
    message = Message.OPTIMAL_TIME
    return timestamp, message, average_percent_renewable


def default_response(message):
    average_percent_renewable = 0
    timestamp = int(datetime.now(timezone.utc).timestamp())
    return timestamp, message, average_percent_renewable




def compute_percentages(energy_data, percent_renewable):
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
    energy_data[column_name] = (
        energy_data["percent_renewable"] > percent_renewable
    )
    # Cummulative number of consequtive quarterhours at the given threshold
    cumsum = 0
    new_colum = []
    binarized_column = list(energy_data[column_name])
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
    energy_data["windows" + str(percent_renewable)] = new_colum
    return energy_data


def compute_rolling_average(
    energy_data: pd.DataFrame, time_units: int
) -> pd.DataFrame:
    """Compute the rolling average over the number of time units.

    :param energy_data: prediction data frame to compute the rolling average for
    :type energy_data: pd.DataFrame
    :return: pandas data frame with the new column
    :rtype: pd.DataFrame
    """

    if not energy_data is None:
        energy_data["rolling_average_pr"] = (
            energy_data["percent_renewable"]
            .rolling(time_units, min_periods=1)
            .mean()
        )
    if "percent_renewable" not in energy_data.columns:
        return energy_data
    return energy_data
