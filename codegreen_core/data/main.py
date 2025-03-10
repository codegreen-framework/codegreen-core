import pandas as pd
from datetime import datetime

from ..utilities.message import Message, CodegreenDataError
from ..utilities import metadata as meta
from ..utilities.config import Config

from . import entsoe as et
from . import offline as off

def energy(country, start_time, end_time, type="generation") -> dict:
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
        The start date for data retrieval (rounded to the nearest hour).  
    :param datetime end_time: 
        The end date for data retrieval (rounded to the nearest hour).  
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
            offline_data = off.get_offline_data(country,start_time,end_time)
            if offline_data["available"] is True and offline_data["partial"] is False and offline_data["data"] is not None:
                # todo fix this if partial get remaining data and merge instead of fetching the complete data
                return {"data":offline_data["data"],"data_available":True,"error":"None","time_interval":60,"source":offline_data["source"],"columns":et.gen_cols_from_data(offline_data["data"])}
            else:
                energy_data = et.get_actual_production_percentage(country, start_time, end_time, interval60=True)
                #energy_data["data"] = energy_data["data"]
                energy_data["source"] = "public_data"
                #energy_data["columns"] = 
                return energy_data            
        elif type == "forecast":
            energy_data = et.get_forecast_percent_renewable(country, start_time, end_time)
            # energy_data["data"] = energy_data["data"]
            return energy_data
    else:
        raise CodegreenDataError(Message.NO_ENERGY_SOURCE)
    return None

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
    data = meta.get_country_metadata()
    data_list = []
    for key , value in data.items():
        c = value
        c["code"]  = key
        data_list.append(c)
    return  data_list