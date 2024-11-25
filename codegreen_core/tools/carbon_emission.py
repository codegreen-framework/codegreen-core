import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

from .carbon_intensity import compute_ci


def compute_ce(
    server: dict,
    start_time: datetime,
    runtime_minutes: int,
) -> tuple[float, pd.DataFrame]:
    """
    Calculates the carbon footprint of a job, given its hardware configuration, time, and location.
    This method returns an hourly time series of the carbon emissions.

    The methodology is defined in the documentation.

    :param server: A dictionary containing the details about the server, including its hardware specifications.
        The dictionary should include the following keys:

        - `country` (str): The country code where the job was performed (required to fetch energy data).
        - `number_core` (int): The number of CPU cores.
        - `memory_gb` (float): The size of memory available in Gigabytes.
        - `power_draw_core` (float): Power draw of a computing core in Watts.
        - `usage_factor_core` (float): The core usage factor, a value between 0 and 1.
        - `power_draw_mem` (float): Power draw of memory in Watts.
        - `power_usage_efficiency` (float): Efficiency coefficient of the data center.

    :param start_time: The start time of the job (datetime).
    :param runtime_minutes: Total running time of the job in minutes (int).

    :return: A tuple containing:
        - (float): The total carbon footprint of the job in kilograms of CO2 equivalent.
        - (pandas.DataFrame): A DataFrame containing the hourly time series of carbon emissions.
    """

    # Round to the nearest hour (in minutes)
    # base valued taken from http://calculator.green-algorithms.org/

    rounded_runtime_minutes = round(runtime_minutes / 60) * 60
    end_time = start_time + timedelta(minutes=rounded_runtime_minutes)
    ci_ts = compute_ci(server["country"], start_time, end_time)
    ce_total, ce_df = compute_ce_from_energy(server, ci_ts)
    return ce_total, ce_df


def _compute_energy_used(
    runtime_minutes,
    number_core,
    power_draw_core,
    usage_factor_core,
    mem_size_gb,
    power_draw_mem,
    PUE,
):
    return round(
        (runtime_minutes / 60)
        * (
            number_core * power_draw_core * usage_factor_core
            + mem_size_gb * power_draw_mem
        )
        * PUE
        * 0.001,
        2,
    )


def compute_savings_same_device(
    country_code,
    start_time_request,
    start_time_predicted,
    runtime,
    cpu_cores,
    cpu_memory,
):
    ce_job1, ci1 = compute_ce(
        country_code, start_time_request, runtime, cpu_cores, cpu_memory
    )
    ce_job2, ci2 = compute_ce(
        country_code, start_time_predicted, runtime, cpu_cores, cpu_memory
    )
    return (
        ce_job1 - ce_job2
    )  # ideally this should be positive todo what if this is negative?, make a note in the comments


def compare_carbon_emissions(
    server1, server2, start_time1, start_time2, runtime_minutes
):
    """
    Compares the carbon emissions of running a job with the same duration on two different servers.

    :param server1: A dictionary containing the details of the first server's hardware and location specifications.
        Required keys include:

        - `country` (str): The country code for the server's location (used for energy data).
        - `number_core` (int): The number of CPU cores.
        - `memory_gb` (float): The memory available in Gigabytes.
        - `power_draw_core` (float): Power draw of each computing core in Watts.
        - `usage_factor_core` (float): The core usage factor, a value between 0 and 1.
        - `power_draw_mem` (float): Power draw of memory in Watts.
        - `power_usage_efficiency` (float): Efficiency coefficient of the data center.

    :param server2: A dictionary containing the details of the second server's hardware and location specifications.
        Required keys are identical to those in `server1`:

        - `country` (str): The country code for the server's location.
        - `number_core` (int): The number of CPU cores.
        - `memory_gb` (float): The memory available in Gigabytes.
        - `power_draw_core` (float): Power draw of each computing core in Watts.
        - `usage_factor_core` (float): The core usage factor, a value between 0 and 1.
        - `power_draw_mem` (float): Power draw of memory in Watts.
        - `power_usage_efficiency` (float): Efficiency coefficient of the data center.

    :param start_time1: The start time of the job on `server1` (datetime).
    :param start_time2: The start time of the job on `server2` (datetime).
    :param runtime_minutes: The total running time of the job in minutes (int).

    :return: A dictionary with the carbon emissions for each server and the percentage difference, structured as follows:
        - `emissions_server1` (float): Total carbon emissions for `server1` in kilograms of CO2 equivalent.
        - `emissions_server2` (float): Total carbon emissions for `server2` in kilograms of CO2 equivalent.
        - `absolute_difference` (float): The absolute difference in emissions between the two servers.
        - `higher_emission_server` (str): Indicates which server has higher emissions ("server1" or "server2").
    """
    ce1, ce1_ts = compute_ce(server1, start_time1, runtime_minutes)
    ce2, ce2_ts = compute_ce(server2, start_time2, runtime_minutes)
    abs_difference = ce2 - ce1
    if ce1 > ce2:
        higher_emission_server = "server1"
    elif ce2 > ce1:
        higher_emission_server = "server2"
    else:
        higher_emission_server = "equal"

    return ce1, ce2, abs_difference, higher_emission_server


def compute_ce_from_energy(server, ci_data: pd.DataFrame):
    """
    Calculates the carbon footprint for energy consumption over a time series.
    This method returns an hourly time series of the carbon emissions.

    The methodology is defined in the documentation. Note that the start and end
    times for the computation are derived from the first and last rows of the
    `ci_data` DataFrame.

    :param server: A dictionary containing details about the server, including its hardware specifications.
        The dictionary should include:

        - `number_core` (int): The number of CPU cores.
        - `memory_gb` (float): The size of memory available in Gigabytes.
        - `power_draw_core` (float): Power draw of a computing core in Watts.
        - `usage_factor_core` (float): The core usage factor, a value between 0 and 1.
        - `power_draw_mem` (float): Power draw of memory in Watts.
        - `power_usage_efficiency` (float): Efficiency coefficient of the data center.

    :param ci_data: A pandas DataFrame of energy consumption over time.
        The DataFrame should include the following columns:

        - `startTimeUTC` (datetime): The start time of each energy measurement in UTC.
        - `ci_default` (float): Carbon intensity values for the energy consumption.

    :return: A tuple containing:
        - (float): The total carbon footprint of the job in kilograms of CO2 equivalent.
        - (pandas.DataFrame): A DataFrame containing the hourly time series of carbon emissions.
    """
    date_format = "%Y%m%d%H%M"  # Year, Month, Day, Hour, Minute


    server =  _add_server_defaults(server)  # set defaults if not provided
    # print(server)
    # to make sure startTimeUTC is in date format
    if not pd.api.types.is_datetime64_any_dtype(ci_data["startTimeUTC"]):
        ci_data["startTimeUTC"] = pd.to_datetime(ci_data["startTimeUTC"])

    end = ci_data["startTimeUTC"].iloc[-1]
    start = ci_data["startTimeUTC"].iloc[0]

    # note that the run time is calculated based on the energy data frame provided
    time_diff = end - start
    runtime_minutes = time_diff.total_seconds() / 60

    energy_consumed = _compute_energy_used(
        runtime_minutes,
        server["number_core"],
        server["power_draw_core"],
        server["usage_factor_core"],
        server["memory_gb"],
        server["power_draw_mem"],
        server["power_usage_efficiency"],
    )

    e_hour = energy_consumed / (
        runtime_minutes * 60
    )  # assuming equal energy usage throughout the computation
    ci_data["carbon_emission"] = ci_data["ci_default"] * e_hour
    ce = round(sum(ci_data["carbon_emission"]), 4)  # grams CO2 equivalent
    return ce, ci_data


def _compute_ce_bulk(server, jobs):
    for job in jobs:
        job['end_time'] = job["start_time"] + timedelta(minutes=job["runtime_minutes"])

    min_start_date = min(job["start_time"] for job in jobs)
    max_end_date = max(job["end_time"] for job in jobs)
    # print(min_start_date)
    # print(max_end_date)
    energy_data = compute_ci(server["country"], min_start_date, max_end_date)
    energy_data["startTimeUTC"] = pd.to_datetime(energy_data["startTimeUTC"])
    for job in jobs:
        filtered_energy = energy_data[
            (energy_data["startTimeUTC"] >= job["start_time"])
            & (energy_data["startTimeUTC"] <= job["end_time"])
        ]
        job["emissions"], temp = compute_ce_from_energy(
            server,
            filtered_energy
        )
    return energy_data, jobs, min_start_date, max_end_date

def _add_server_defaults(server):
    server_defaults = {
        "power_draw_core": 15.8,
        "usage_factor_core": 1,
        "power_draw_mem": 0.3725,
        "power_usage_efficiency": 1.6,
    }
    server = server_defaults | server  # set defaults if not provided
    return server    

def plot_ce_jobs(server, jobs):
    energy_data, jobs, min_start_date, max_end_date = _compute_ce_bulk(_add_server_defaults(server), jobs)
    Color = {
        "red": "#D6A99A",
        "green": "#99D19C",
        "blue": "#3DA5D9",
        "yellow": "#E2C044",
        "black": "#0F1A20",
    }
    fig, ax1 = plt.subplots(figsize=(10, 6))
    plt.title("Green Energy and Jobs")
    end = energy_data["startTimeUTC"].iloc[-1]
    start = energy_data["startTimeUTC"].iloc[0]
    ax1.plot(
        energy_data["startTimeUTC"],
        energy_data["percentRenewable"],
        color=Color["green"],
        label="Percentage of Renewable Energy",
    )
    ax1.set_xlabel("Time")
    ax1.set_ylabel("% Renewable energy")
    ax1.tick_params(axis="y")

    # Set x-axis to show dates properly
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m %H:%M"))
    plt.xticks(rotation=45)

    # # Create a second y-axis
    ax2 = ax1.twinx()

    # Define y-values for each job (e.g., 1 for Job A, 2 for Job B, etc.)
    for idx, job in enumerate(jobs):
        lbl = str(job["emissions"])
        ax2.plot(
            [job["start_time"], job["end_time"]],
            [idx + 1, idx + 1],
            marker="o",
            linewidth=25,
            label=lbl,
            color=Color["blue"],
        )
        # Calculate the midpoint for the text placement
        labelpoint = (
            job["start_time"] + (job["end_time"] - job["start_time"]) / 2
        )  # + timedelta(minutes=100)
        ax2.text(
            labelpoint,
            idx + 1,
            lbl,
            color="black",
            ha="center",
            va="center",
            fontsize=12,
        )

    # Adjust y-axis labels to match the number of jobs
    ax2.set_yticks(range(1, len(jobs) + 1))

    # Add legend and show the plot
    fig.tight_layout()
    # plt.legend(loc='lower right')
    plt.show(block=True)
    # plt.pyplot.show()
