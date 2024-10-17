import pandas as pd
from datetime import datetime

from ..utilities.message import Message,CodegreenDataError
from ..utilities  import metadata as meta  
from . import entsoe as et

def energy(country,start_time,end_time,type="generation",interval60=True)-> pd.DataFrame:
  """
    Returns hourly time series of energy production mix for a specified country and time range.

    This method fetches the energy data for the specified country between the specified duration.
    It checks if a valid energy data source is available. If not, None is returned. Otherwise, the
    energy data is returned as a pandas DataFrame. The structure of data depends on the energy source.

    For example, if the source is ENTSOE, the data contains:

     ========================== ========== ================================================================ 
      Column                     type       Description                                                     
     ========================== ========== ================================================================ 
      startTimeUTC               datetime   Start date in UTC (60 min interval)                             
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
