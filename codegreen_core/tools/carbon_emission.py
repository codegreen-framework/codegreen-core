import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .carbon_intensity import compute_ci 

def compute_ce(
    country: str,
    start_time:datetime,
    runtime_minutes: int,
    number_core: int,
    memory_gb: int,
    power_draw_core:float=15.8,
    usage_factor_core:int=1,
    power_draw_mem:float=0.3725,
    power_usage_efficiency:float=1.6
):
    """ 
    Calculates the carbon footprint of a job, given its hardware config, time and location of the job. 
    This method returns an hourly time series of the carbon emission.
    The methodology is defined in the documentation

    :param country: The country code where the job was performed (required to fetch energy data)
    :param start_time: The starting time of the computation as datetime object in local time zone
    :param runtime_minutes: running time in minutes
    :param number_core: the number of core
    :param memory_gb: the size of memory available (in Gigabytes)
    :param power_draw_core: power draw of a computing core (Watt)
    :param usage_factor_core: the core usage factor (between 0 and 1)
    :param power_draw_mem: power draw of memory (Watt)
    :param power_usage_efficiency: efficiency coefficient of the data center
    """
    # Round to the nearest hour (in minutes)
    # base valued taken from http://calculator.green-algorithms.org/ 
    rounded_runtime_minutes = round(runtime_minutes / 60) * 60
    end_time = start_time + timedelta(minutes=rounded_runtime_minutes)
    ci_ts = compute_ci(country, start_time, end_time)
    ce_total,ce_df = compute_ce_from_energy(ci_ts, number_core,memory_gb,power_draw_core,usage_factor_core,power_draw_mem,power_usage_efficiency)
    return ce_total,ce_df 

def compute_energy_used(runtime_minutes, number_core, power_draw_core, usage_factor_core, mem_size_gb, power_draw_mem, PUE):
    return round((runtime_minutes/60)*(number_core * power_draw_core * usage_factor_core + mem_size_gb * power_draw_mem) * PUE * 0.001, 2)

def compute_savings_same_device(country_code,start_time_request,start_time_predicted,runtime,cpu_cores,cpu_memory):
  ce_job1,ci1 = compute_ce(country_code,start_time_request,runtime,cpu_cores,cpu_memory) 
  ce_job2,ci2 = compute_ce(country_code,start_time_predicted,runtime,cpu_cores,cpu_memory)
  return ce_job1-ce_job2 # ideally this should be positive todo what if this is negative?, make a note in the comments 


def compute_ce_from_energy(
    ci_data:pd.DataFrame,
    number_core: int,
    memory_gb: int,
    power_draw_core:float=15.8,
    usage_factor_core:int=1,
    power_draw_mem:float=0.3725,
    power_usage_efficiency:float=1.6):
    
    """ 
        Calculates the carbon footprint for energy consumption time series  
        This method returns an hourly time series of the carbon emission.
        The methodology is defined in the documentation

        :param ci_data: DataFrame of energy consumption. Required cols : startTimeUTC, ci_default
        :param number_core: the number of core
        :param memory_gb: the size of memory available (in Gigabytes)
        :param power_draw_core: power draw of a computing core (Watt)
        :param usage_factor_core: the core usage factor (between 0 and 1)
        :param power_draw_mem: power draw of memory (Watt)
        :param power_usage_efficiency: efficiency coefficient of the data center
    """
    time_diff = ci_data['startTimeUTC'].iloc[-1] - ci_data['startTimeUTC'].iloc[0]
    runtime_minutes =  time_diff.total_seconds() / 60
    energy_consumed = compute_energy_used(runtime_minutes, number_core, power_draw_core,
                                     usage_factor_core, memory_gb, power_draw_mem, power_usage_efficiency)
    e_hour = energy_consumed/(runtime_minutes*60)
    ci_data["carbon_emission"] = ci_data["ci_default"] * e_hour
    ce = round(sum(ci_data["carbon_emission"]),4) # grams CO2 equivalent 
    return ce,ci_data