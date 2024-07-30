from datetime import datetime
import pandas as pd
# from ..utils.message import Message, CodegreenDataError
from . import time as t
from . import location as l
from . import carbon_emission as ce


def predict_optimal_time(
    country: str,
    estimated_runtime_hours: int,
    estimated_runtime_minutes: int,
    hard_finish_date: datetime,
    criteria: str = "percent_renewable",
    percent_renewable: int = 50,
):
    return t.predict_now(country, estimated_runtime_hours, estimated_runtime_minutes, hard_finish_date, criteria, percent_renewable)


def predict_optimal_location():
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
    return ce.calculate_carbon_footprint_job(country, start_time, runtime_minutes, number_core, memory_gb, power_draw_core, usage_factor_core, power_draw_mem, power_usage_efficiency)


def calculate_emissions_saved():
    print()
