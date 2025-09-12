import pandas as pd
from datetime import datetime, timezone, timedelta
from pathlib import Path

from codegreen_core.data.entsoe import get_entsoe_production_percentage, get_entsoe_forecast_percent_renewable
from codegreen_core.data.offline import _get_cache_data 
from codegreen_core.utilities.config import Config
from codegreen_core.utilities.metadata import get_country_energy_source, get_country_metadata

def energy(country: str, start_time: datetime, end_time: datetime, type: str = "generation") -> pd.DataFrame:
    """
    Returns an hourly time series of the energy production mix for a specified country and time range, 
    if a valid energy data source is available.

    The data is returned as a pandas DataFrame along with additional metadata.  
    The columns vary depending on the data source. For example, if the source is ENTSOE, 
    the data includes fields such as "Biomass", "Geothermal", "Hydro Pumped Storage", 
    "Hydro Run-of-river and Poundage", "Hydro Water Reservoir", etc.

    However, some fields remain consistent across data sources:

    ========================= ========== ================================================================
    Column                     Type       Description
    ========================= ========== ================================================================
    startTimeUTC              object     Start time in UTC (format: YYYYMMDDhhmm)
    startTime                 datetime   Start time in local timezone
    renewableTotal            float64    The total production from all renewable sources
    renewableTotalWS          float64    Total production using only Wind and Solar energy sources
    nonRenewableTotal         float64    Total production from non-renewable sources
    total                     float64    Total energy production from all sources
    percentRenewable          int64      Percentage of total energy from renewable sources
    percentRenewableWS        int64      Percentage of energy from Wind and Solar only
    Wind_per                  int64      Percentage contribution from Wind energy
    Solar_per                 int64      Percentage contribution from Solar energy
    Nuclear_per               int64      Percentage contribution from Nuclear energy
    Hydroelectricity_per      int64      Percentage contribution from Hydroelectricity
    Geothermal_per            int64      Percentage contribution from Geothermal energy
    Natural Gas_per           int64      Percentage contribution from Natural Gas
    Petroleum_per             int64      Percentage contribution from Petroleum
    Coal_per                  int64      Percentage contribution from Coal
    Biomass_per               int64      Percentage contribution from Biomass
    ========================= ========== ================================================================

    :param str country: 
        The 2-letter country code (e.g., "DE" for Germany, "FR" for France, etc.).  
    :param datetime start_time: 
        The start date for data retrieval (rounded to the date hour).  
    :param datetime end_time: 
        The end date for data retrieval (rounded to the date hour).  
    :param str type: 
        The type of data to retrieve; either 'generation' or 'forecast'. Defaults to 'generation'.  

    :return: A dictionary containing the following keys:

        - **error** (*str*): An error message, empty if no errors occurred.
        - **data_available** (*bool*): Indicates whether data was successfully retrieved.
        - **data** (*pandas.DataFrame*): The retrieved energy data if available; an empty DataFrame otherwise.
        - **time_interval** (*int*): The time interval of the DataFrame (constant value: ``60``).
        - **source** (*str*): Specifies the origin of the retrieved data. Defaults to ``'public_data'``, indicating it was fetched from an external source. If the offline storage feature is enabled, this value may change if the data is available locally.
        - **columns** : a dict of columns for renewable and non renewable energy sources in the data

    :rtype: dict

    **Example Usage:**

    Get generation data for Germany 
    .. code-block:: python

        from datetime import datetime
        from codegreen_core.data import energy
        result = energy(country="DE", start_time=datetime(2025, 1, 1), end_time=datetime(2025, 1, 2), type="generation")

    Get forecast data for Norway 

    .. code-block:: python

        from datetime import datetime
        from codegreen_core.data import energy
        result = energy(country="NO", start_time=datetime(2025, 1, 1), end_time=datetime(2025, 1, 2), type="forecast")
    
    """
    ## TODO: ENERGY
    # TODO: Improve error messaging
    # TODO: Add offline saving 
    # TODO: Check ENTSOE query
    # DONE: edge case datetime.now() close to 72 hours --> proprage datetime.now from here 
    # TODO: Fix _impute_data: Running average instead of day average
    # TODO: Move code from entsoe pull method to entsoe postprocess (generation and forecast)
    # TODO: Mean vs Sum in _convert_to_hourly_intervals --> Check output type from entsoe
    # TODO: Constants auslagern 
    # TODO: Fix get_entsoe_production_percentage fill methode
    # TODO: Check ENTSOE website vs returned pandas dataframe.
    # TODO: Change hardcoded values to config values

    ## TODO: PREDICT_NOW
    # TODO: Change start_time timezone to hard_finish_date timezone.

    ## TODO: Carbon intensity
    # TODO: Compute carbon intensity as post processing of energy -> Remove the one function
    if not isinstance(country, str):
        raise TypeError("country must be a str")
    if not isinstance(start_time, datetime):
        raise TypeError("start_time must be a datetime")
    if not isinstance(end_time, datetime):
        raise TypeError("end_time must be a datetime")
    if not isinstance(type, str):
        raise TypeError("type must be a str")
   
    if type not in ["generation", "forecast"]:
        raise ValueError("type must be 'generation' or 'forecast'")
    
    if start_time.tzinfo is None:
        raise ValueError("start_time has no timezone information")
    if end_time.tzinfo is None:
        raise ValueError("end_time has no timezone information")
    if start_time > end_time:
        raise ValueError("Invalid start time and end time. End time must be greater than start time")
    original_start_tz = start_time.tzinfo
    original_end_tz = end_time.tzinfo
    if original_start_tz != original_end_tz:
        raise ValueError("Start time and end time use different time zones")

    timestamp_now = datetime.now(timezone.utc) 

    start_time = start_time.replace(minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    end_time = end_time.replace(minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    
    e_source = get_country_energy_source(country)
    if e_source == "ENTSOE":
        if type == "generation":
            # Only use Cache iff cache is enabled and the request is within the last 72 hours.
            if Config.ENABLE_ENERGY_CACHING and timestamp_now - start_time <= timedelta(hours=Config.GENERATION_CACHE_HOUR):
                data = _get_cache_data(country, start_time, end_time, type, timestamp_now)
            else:
                data = get_entsoe_production_percentage(country, start_time, end_time, type)
        elif type == "forecast":
            # Only use Cache iff cache is enabled and the request is for the next 24 hours.
            if Config.ENABLE_ENERGY_CACHING and end_time - timestamp_now <= timedelta(hours=Config.FORECAST_CACHE_HOUR):
                data = _get_cache_data(country, start_time, end_time, type, timestamp_now) 
            else:
                data = get_entsoe_forecast_percent_renewable(country, start_time, end_time)
    else:
        # raise CodegreenDataError(Message.NO_ENERGY_SOURCE)
        raise Exception("Error occured")
    
    # return to original timezone
    data.index = data.index.map(lambda x: pd.Timestamp(x).tz_convert(original_start_tz))

    return data


def info()-> list:
    """
    Returns a list of countries (in two-letter codes) and energy sources for which data can be fetched using the package.
    
    :return: A list of dictionary containing:

      - name of the country
      - `energy_source` : the publicly available energy data source 
      - `carbon_intensity_method` : the methodology used to calculate carbon intensity 
      - `code` : the 2 letter country code 
    
    :rtype: list
    """
    data = get_country_metadata()
    data_list = []
    for key , value in data.items():
        c = value
        c["code"]  = key
        data_list.append(c)
    return  data_list