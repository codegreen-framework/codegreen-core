from datetime import datetime, timedelta, timezone
from dateutil import tz
import numpy as np
import pandas as pd
import pytz

# from greenerai.api.data.utils import Message

# from ..utilities.metadata import check_prediction_model_exists
from codegreen_core.data import energy
# from ..models.predict import predicted_energy
from codegreen_core.utilities.config import Config
import traceback
from pathlib import Path


def predict_now(
    country: str, 
    estimated_runtime_hours: int, 
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

    if not isinstance(estimated_runtime_hours, int):
        raise TypeError("estimated_runtime_hours must be an integer")
    if not isinstance(hard_finish_date, datetime):
        raise TypeError("country must be a datetime")
    if not isinstance(criteria, str):
        raise TypeError("criteria must be a str")

    if criteria not in ["percent_renewable", "optimal_percent_renewable"]:
        raise ValueError("criteria must be 'percent_renewable' or 'optimal_percent_renewable'")

    if hard_finish_date.tzinfo is None:
        raise ValueError("hard_finish_date has no timezone information")   

    start_time = datetime.now(hard_finish_date.tzinfo)
    if hard_finish_date <= start_time:
        raise ValueError("Hard finish date is in the past!")

    if criteria == "percent_renewable":
        energy_forecast = energy(country, start_time, hard_finish_date, "forecast")
        if not energy_forecast.empty:
            return predict_optimal_time(
                energy_forecast,
                estimated_runtime_hours,
                hard_finish_date
            )
        else:
            raise RuntimeError("No forecast data was available!")
     
    elif criteria == "optimal_percent_renewable":
        pass
        
    
def predict_optimal_time(
    energy_forecast: pd.DataFrame,
    estimated_runtime_hours: int,
    hard_finish_date: datetime
) -> tuple:
    """
    Predicts the optimal time window to run a task within the given energy data time frame the run time estimate .

    :param energy_data: A DataFrame containing the energy data including startTimeUTC, totalRenewable,total,percent_renewable,posix_timestamp
    :param estimated_runtime_hours: The estimated runtime in hours
    :param hard_finish_date: The latest possible finish time for the task.

    :return: Tuple[timestamp, message, average_percent_renewable]
    :rtype: tuple
    """

    energy_forecast["forward_avg"] = energy_forecast["percentRenewable"][::-1].rolling(estimated_runtime_hours, min_periods=1).mean()[::-1]

    hard_finish_date = hard_finish_date.astimezone(timezone.utc)
    best_starting_time_idx = energy_forecast["forward_avg"][:(hard_finish_date - timedelta(hours=estimated_runtime_hours))].argmax()
    
    best_starting_time = energy_forecast.index[best_starting_time_idx]
    avg_perc_renewable = energy_forecast["forward_avg"].iloc[best_starting_time_idx] 
    
    # best_starting_times = energy_forecast["forward_avg"][:(hard_finish_date - timedelta(hours=estimated_runtime_hours))].sort_values(ascending=False).index.tolist()
   
    if best_starting_time == energy_forecast.index[0]:
        return datetime.now(tz=best_starting_time.tz), avg_perc_renewable
    else:
        return best_starting_time, avg_perc_renewable