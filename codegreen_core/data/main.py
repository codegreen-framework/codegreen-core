import pandas as pd
from datetime import datetime

from ..utils.message import Message,CodegreenDataError
from .  import metadata as meta  
from . import entsoe as et
from . import carbon_intensity as ct

def energy(country,start_time,end_time,type="historical")-> pd.DataFrame:
  """ To get energy data
  """
  if not isinstance(country, str):
    raise ValueError("Invalid country")
  if not isinstance(start_time, datetime):
    raise ValueError("Invalid discount rate")
  if type not in ['historical', 'forecast']:
    raise ValueError(Message.INVALID_ENERGY_TYPE)
  
  e_source = meta.get_country_energy_source(country)
  if e_source=="ENTSOE" :
    if type == "historical":
      return et.get_actual_production_percentage(country,start_time,end_time)
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
    energy_data = energy(country, et.convert_date_to_entsoe_format(start_time), et.convert_date_to_entsoe_format(end_time))
    ci_values = energy_data.apply(lambda row: ct.calculate_carbon_intensity(row.to_dict()),axis=1)
    ci = pd.DataFrame(ci_values.tolist())
    ci = pd.concat([ci,energy_data],axis=1)
    return ci
  else:
    time_series = pd.date_range(start=start_time, end=end_time, freq='H')
    df = pd.DataFrame(time_series, columns=['startTimeUTC'])
    df["ci_country_default"] = meta.get_default_ci_value(country)
    # TODO check same format for both cases
    return df