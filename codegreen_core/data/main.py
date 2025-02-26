import pandas as pd
from datetime import datetime

from ..utilities.message import Message, CodegreenDataError
from ..utilities import metadata as meta
from ..utilities.config import Config

from . import entsoe as et
from . import offline as off

def energy(country, start_time, end_time, type="generation") -> dict:
    """
    Returns hourly time series of energy production mix for a specified country and time range.

    This method fetches the energy data for the specified country between the specified duration.
    It checks if a valid energy data source is available. If not, None is returned. Otherwise, the
    energy data is returned as a pandas DataFrame. The structure of data depends on the energy source.

    For example, if the source is ENTSOE, the data contains:

     ========================== ========== ================================================================
      Column                     type       Description
     ========================== ========== ================================================================
      startTimeUTC               object    Start date in UTC (format YYYYMMDDhhmm)
      startTime                  datetime  Start time in local timezone
      Biomass                    float64 
      Fossil Hard coal           float64
      Geothermal                 float64
      ....more energy sources    float64
      **renewableTotal**         float64    The total based on all renewable sources
      renewableTotalWS           float64    The total production using only Wind and Solar energy sources
      nonRenewableTotal          float64
      total                      float64    Total using all energy sources
      percentRenewable           int64
      percentRenewableWS         int64      Percentage of energy produced using only wind and solar energy
      Wind_per                   int64      Percentages of individual energy sources
      Solar_per                  int64
      Nuclear_per                int64
      Hydroelectricity_per       int64
      Geothermal_per             int64
      Natural Gas_per            int64
      Petroleum_per              int64
      Coal_per                   int64
      Biomass_per                int64
     ========================== ========== ================================================================

    Note : fields marked bold are calculated based on the data fetched.

    :param str country: The 2 alphabet country code.
    :param datetime start_time: The start date for data retrieval. A Datetime object. Note that this date will be rounded to the nearest hour.
    :param datetime end_time: The end date for data retrieval. A datetime object. This date is also rounded to the nearest hour.
    :param str type: The type of data to retrieve; either 'generation' or 'forecast'. Defaults to 'generation'.
    :param boolean interval60: To fix the time interval of data to 60 minutes. True by default. Only applicable for generation data

    :return: A dictionary containing:
      - `error`: A string with an error message, empty if no errors.
      - `data_available`: A boolean indicating if data was successfully retrieved.
      - `data`: A pandas DataFrame containing the energy data if available, empty DataFrame if not.
      - `time_interval` : the time interval of the DataFrame 
    :rtype: dict
    """
    if not isinstance(country, str):
        raise ValueError("Invalid country")
    if not isinstance(start_time, datetime):
        raise ValueError("Invalid start date")
    if not isinstance(end_time, datetime):
        raise ValueError("Invalid end date")
    if type not in ["generation", "forecast"]:
        raise ValueError(Message.INVALID_ENERGY_TYPE)
    # check start<end and both are not same

    if start_time > end_time:
        raise ValueError("Invalid time.End time should be greater than start time")

    e_source = meta.get_country_energy_source(country)
    if e_source == "ENTSOE":
        if type == "generation":
            """
            let local_found= false
            see if caching is enabled, if yes, first check in the cache
            if not, 
                check if offline data is enabled
                if yes, check is data is available locally 
                if no, go online 
            """
            offline_data = off.get_offline_data(country,start_time,end_time)
            if offline_data["available"] is True and offline_data["partial"] is False and offline_data["data"] is not None:
                # todo fix this if partial get remaining data and merge instead of fetching the complete data
                return {"data":offline_data["data"],"data_available":True,"error":"None","time_interval":60,"source":offline_data["source"]}
            else:
                energy_data = et.get_actual_production_percentage(country, start_time, end_time, interval60=True)
                energy_data["data"] = energy_data["data"]
                energy_data["source"] = "public_data"
                return energy_data            
        elif type == "forecast":
            energy_data = et.get_forecast_percent_renewable(country, start_time, end_time)
            energy_data["data"] = energy_data["data"]
            return energy_data
    else:
        raise CodegreenDataError(Message.NO_ENERGY_SOURCE)
    return None
