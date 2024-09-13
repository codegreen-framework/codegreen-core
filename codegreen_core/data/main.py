import pandas as pd
from datetime import datetime

from ..utilities.message import Message,CodegreenDataError
from ..utilities  import metadata as meta  
from . import entsoe as et
from . import carbon_intensity as ct

def energy(country,start_time,end_time,type="generation",interval60=True)-> pd.DataFrame:
  """ 
  Returns hourly time series of energy production mix for a specified country and time range. 

  This method fetches the energy data for specified country, between the specified duration. 
  It checks if a valid energy data source is available.  If not, None is returned. Otherwise, the energy data is returns as a pandas DataFrame. The structure of data depends on the energy source. 
  For example is the source is ENTSOE,  the data contains :
  ```
    startTimeUTC                        object
    Biomass                            float64
    Fossil Hard coal                   float64
    Geothermal                         float64
    Nuclear                            float64
    Other                              float64
    Solar                              float64
    Wind Offshore                      float64
    .... other energy sources 
    # common fields for all countries 
    renewableTotal                     float64
    renewableTotalWS                   float64 # total energy produced from wind and solar energy sources 
    nonRenewableTotal                  float64
    total                              float64

    percentRenewable                     int64
    percentRenewableWS                   int64

    Wind_per                             int64
    Solar_per                            int64
    Nuclear_per                          int64
    Hydroelectricity_per                 int64
    Geothermal_per                       int64
    Natural Gas_per                      int64
    Petroleum_per                        int64
    Coal_per                             int64
    Biomass_per 
  ```
  
  :param str country: The 2 alphabet country code.
  :param datetime start_time: The start date for data retrieval. A Datetime object. Note that this date will be rounded to the nearest hour. 
  :param datetime end_time: The end date for data retrieval. A datetime object. This date is also rounded to the nearest hour. 
  :param str type: The type of data to retrieve; either 'historical' or 'forecasted'. Defaults to 'historical'.
  :return: A DataFrame containing the hourly energy production mix.
  :rtype: pd.DataFrame

  """
  if not isinstance(country, str):
    raise ValueError("Invalid country")
  if not isinstance(start_time,datetime):
    raise ValueError("Invalid start date")
  if not isinstance(end_time, datetime):
    raise ValueError("Invalid end date")
  if type not in ['generation', 'forecast']:
    raise ValueError(Message.INVALID_ENERGY_TYPE)
  # check start<end and both are not same 
  
  e_source = meta.get_country_energy_source(country)
  if e_source=="ENTSOE" :
    if type == "generation":
      return et.get_actual_production_percentage(country,start_time,end_time,interval60)
    elif type == "forecast":
      return et.get_forecast_percent_renewable(country,start_time,end_time)
  else:
    raise CodegreenDataError(Message.NO_ENERGY_SOURCE)
  return None

def carbon_intensity(country,start_time,end_time)-> pd.DataFrame:
  """
  Returns carbon intensity data calculated based on energy data (if available, else country default)
  """
  e_source = meta.get_country_energy_source(country)
  if e_source=="ENTSOE" :
    energy_data = energy(country,start_time,end_time)
    ci_values = energy_data.apply(lambda row: ct.calculate_carbon_intensity(row.to_dict()),axis=1)
    ci = pd.DataFrame(ci_values.tolist())
    ci = pd.concat([ci,energy_data],axis=1)
    ci["ci_default"] = ci["ci_ipcc_lifecycle_mean"]
    return ci
  else:
    time_series = pd.date_range(start=start_time, end=end_time, freq='H')
    df = pd.DataFrame(time_series, columns=['startTimeUTC'])
    df["ci_default"] = meta.get_default_ci_value(country)
    # TODO check same format for both cases
    return df