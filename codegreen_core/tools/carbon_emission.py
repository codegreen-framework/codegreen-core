import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .carbon_intensity import calculate_for_country

def calculate_carbon_footprint_job(
    country: str,
    start_time,
    runtime_minutes: int,
    number_core: int,
    memory_gb: int,
    power_draw_core=15.8,
    usage_factor_core=1,
    power_draw_mem=0.3725,
    power_usage_efficiency=1.6
):
    """ To calculate the carbon footprint of a job given the details of the computer configuration (the number of CPU cores and the memory) and the location and time of where the job was executed.
    This method returns an hourly time series of the carbon emission.
    The carbon emission are calculated based  on J. Grealey et al., ‘The Carbon Footprint of Bioinformatics’, Molecular Biology and Evolution, vol. 39, no. 3, p. msac034, Mar. 2022, doi: 10.1093/molbev/msac034. 
    CF = E_hour * CI
    where CI is a time series  
    :param country : The country code where the job was performed (required to fetch energy data)
    :type country : string

    # Assumptions
    # PUE : Power Usage Efficiency of the data center
    # P_m : Memory power draw,Watts/GB  
    # P_c: In Watts Assuming Core-i5-10600K  ; value taken from http://calculator.green-algorithms.org/
    # u_c : core usage factor 

    """
    end_time = start_time + timedelta(minutes=runtime_minutes)
    ci_ts = calculate_for_country(country, start_time, end_time)
    e = calculate_energy_consumption(runtime_minutes, number_core, power_draw_core,
                                     usage_factor_core, memory_gb, power_draw_mem, power_usage_efficiency)
    e_hour = e/(runtime_minutes*60)
    ci_ts["carbon_emission"] = ci_ts["ci_default"] * e_hour
    ce = round(sum(ci_ts["carbon_emission"]),4) # grams CO2 equivalent 
    return ce,ci_ts


def calculate_energy_consumption(runtime_minutes, number_core, power_draw_core, usage_factor_core, mem_size_gb, power_draw_mem, PUE):
    return round((runtime_minutes/60)*(number_core * power_draw_core * usage_factor_core + mem_size_gb * power_draw_mem) * PUE * 0.001, 2)


def get_saving_same_device(country_code,start_time_request,start_time_predicted,runtime,cpu_cores,cpu_memory):
  
  ce_job1,ci1 = calculate_carbon_footprint_job(country_code,start_time_request,runtime,cpu_cores,cpu_memory) 
  ce_job2,ci2 = calculate_carbon_footprint_job(country_code,start_time_predicted,runtime,cpu_cores,cpu_memory)
  return ce_job1-ce_job2 # ideally this should be positive todo what if this is negative?, make a note in the comments 