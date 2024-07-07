import pandas as pd
from . metadata import metadata as meta  
from ..utils.message import Message,CodegreenDataError
from . import entsoe as et


def energy(country,start_time,end_time,type="historical")-> pd.DataFrame:
  """ To get energy data
  TODO implement interval_min other than 60
  """
  e_source = meta.get_country_energy_source(country)
  if e_source=="ENTSOE" :
    if type == "historical":
      return et.get_actual_production_percentage(country,start_time,end_time)
    elif type == "forecast":
      return et.get_forecast_percent_renewable(country,start_time,end_time)
    else:
      raise CodegreenDataError(Message.INVALID_ENERGY_TYPE)
  return None

def carbon_intensity(country,start_time,end_time)-> pd.DataFrame:
  """
  to get carbon intensity data
  """