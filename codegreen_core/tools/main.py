from datetime import datetime
import pandas as pd
# from ..utils.message import Message, CodegreenDataError
from . import loadshift_time as t
from . import loadshift_location as l
from . import carbon_emission as ce
from . import carbon_intensity as ct


def predict_optimal_job_time(
    country: str,
    estimated_runtime_hours: int,
    estimated_runtime_minutes: int,
    hard_finish_date: datetime,
    criteria: str = "percent_renewable",
    percent_renewable: int = 50,
):
    """ Predicts optimal time for a job 
    """
    return t.predict_now(country, estimated_runtime_hours, estimated_runtime_minutes, hard_finish_date, criteria, percent_renewable)


def predict_optimal_location():
    """
    To predict optimal time location 
    """
    return l.predict_optimal_location()

def calculate_carbon_footprint(
        country: str,
        start_time,
        runtime_minutes: int,
        number_core: int,
        memory_gb: int,
        power_draw_core=15.8,
    usage_factor_core=1,
    power_draw_mem=0.3725,
    power_usage_efficiency=1.6):
    """
    To calculate the carbon footprint of the job
    """
    return ce.calculate_carbon_footprint_job(country, start_time, runtime_minutes, number_core, memory_gb, power_draw_core, usage_factor_core, power_draw_mem, power_usage_efficiency)


def calculate_emissions_saved():
    """
    To calcualated emissions saved
    """
    print()


def calculate_carbon_intensity(country,start_time,end_time)-> pd.DataFrame:
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