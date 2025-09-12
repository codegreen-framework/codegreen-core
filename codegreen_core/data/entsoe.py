import pandas as pd
from datetime import datetime, timezone
from entsoe import EntsoePandasClient as entsoePandas

import traceback

from codegreen_core.utilities.config import Config

# constant values
renewableSources = [
    "Biomass",
    "Geothermal",
    "Hydro Pumped Storage",
    "Hydro Run-of-river and poundage",
    "Hydro Water Reservoir",
    "Marine",
    "Other renewable",
    "Solar",
    "Waste",
    "Wind Offshore",
    "Wind Onshore",
]
windSolarOnly = ["Solar", "Wind Offshore", "Wind Onshore"]
nonRenewableSources = [
    "Fossil Brown coal/Lignite",
    "Fossil Coal-derived gas",
    "Fossil Gas",
    "Fossil Hard coal",
    "Fossil Oil",
    "Fossil Oil shale",
    "Fossil Peal",
    "Nuclear",
    "Other",
]
energy_type = {
    "Wind": ["Wind Offshore", "Wind Onshore"],
    "Solar": ["Solar"],
    "Nuclear": ["Nuclear"],
    "Hydroelectricity": [
        "Hydro Pumped Storage",
        "Hydro Run-of-river and poundage",
        "Hydro Water Reservoir",
    ],
    "Geothermal": ["Geothermal"],
    "Natural Gas": ["Fossil Coal-derived gas", "Fossil Gas"],
    "Petroleum": ["Fossil Oil", "Fossil Oil shale"],
    "Coal": ["Fossil Brown coal/Lignite", "Fossil Hard coal", "Fossil Peal"],
    "Biomass": ["Biomass"],
}


def _impute_data(entsoe_data: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Imputes entsoe data by substituting missing values with the averages over the day or over the whole time.
    Args:
        entsoe_data (Pandas.DataFrame): Pulled Entsoe data.
    Returns:
        Imputed entsoe data.
    """
    # calculate the duration of the time series by finding the difference between the
    # first and the second index (which is of the type `datatime``) and convert this into minutes
    #print(data1)
    if len(entsoe_data) == 1:
        return entsoe_data, ["Only one record cannot be processed"]

    durationMin = entsoe_data.index.diff().min().total_seconds() / 60
    # initializing the log list
    refine_logs = []
    refine_logs.append(
        "Row count : Fetched =  " + str(len(entsoe_data)) + ", duration : " + str(durationMin)
    )
    
    # Determining the list of records that are absent in the time series by initially creating a set containing all 
    # the expected timestamps within the start and end time range. Then, we calculate the difference between 
    # this set and the timestamps present in the actual DataFrame.
    
    start_time = entsoe_data.index.min()
    end_time = entsoe_data.index.max()
    expected_timestamps = pd.date_range(
        start=start_time, end=end_time, freq=f"{durationMin}min"
    )
    expected_df = pd.DataFrame(index=expected_timestamps)
    missing_indices = expected_df.index.difference(entsoe_data.index)
    
    # Next, we fill in the missing values. 
    # For each absent timestamp, we examine if the entries for the same day exists. 
    # If they do, we use the day average for each column in the Dataframe. 
    # Else, we use the average of the entire data
    
    totalAverageValue = entsoe_data.mean().fillna(0).round().astype(int)
    for index in missing_indices:
        rows_same_day = entsoe_data[entsoe_data.index.date == index.date()]
        if len(rows_same_day) > 0:
            avg_val = rows_same_day.mean().fillna(0).round().astype(int)
            avg_type = "average day value " + str(rows_same_day.index[0].date()) + " "
        else:
            avg_val = totalAverageValue
            avg_type = "whole data average "
        refine_logs.append(
            "Missing value: "
            + str(index)
            + "      replaced with "
            + avg_type
            + " : "
            + " ".join(avg_val.astype(str))
        )
        new_row = pd.DataFrame([avg_val], columns=entsoe_data.columns, index=[index])
        entsoe_data = pd.concat([entsoe_data, new_row])
    
    # since missing values are concatenated to the dataframe, it is also sorted based on the datetime index
    entsoe_data.sort_index(inplace=True)

    return entsoe_data, refine_logs


def _convert_to_hourly_intervals(entsoe_raw_data: pd.DataFrame) -> pd.DataFrame:
    """
    Given the raw entsoe data. This function converts the DataFrame into hourly time intervals by aggregating.
    Args:
        entsoe_raw_data (pandas.Dataframe): Pulled raw entsoe data.
    Returns:
        Aggregated entsoe data into 60 minute time intervals.
    """
    duration = entsoe_raw_data.index.diff().min().total_seconds() / 60
    if duration == 60.0:
        return entsoe_raw_data
    
    entsoe_raw_data["date"] = entsoe_raw_data.index.date
    entsoe_raw_data["hour"] = entsoe_raw_data.index.hour

    entsoe_data = (
        entsoe_raw_data
        .groupby(["date", "hour"], as_index=False)
        .sum(numeric_only=True)
    )

    entsoe_data.index = [datetime(date.year, date.month, date.day, hour).astimezone(timezone.utc) for date, hour in zip(entsoe_data["date"], entsoe_data["hour"])]
    entsoe_data.drop(columns=["date", "hour"], inplace=True)

    return entsoe_data


def _entsoe_get_production(country: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
    """
    Fetches the aggregated actual generation per production type data (16.1.B&C) for the given country within the given start and end date from entso-e.
    Args:
        country (str): 2 letter country code.
        start (datetime): Start date to get data.
        end (datetime): End date to get data. 
    Returns:
        entsoe_data (pandas.DataFrame): Pulled and imputed Entsoe data.
        imputation_logs (list): Imputation logs.  
    """
    # print(start_time)
    # print(end_time)
    entsoe_client = entsoePandas(api_key = Config.ENTSOE_TOKEN)
    try :
        entsoe_data = entsoe_client.query_generation(
            country,
            start = pd.Timestamp(start_time),
            end = pd.Timestamp(end_time),
            psr_type = None,
        )
    except Exception as e:
        raise e("Error in fetching data from ENTSOE.")
    
    # drop columns with actual consumption values (we want actual aggregated generation values)
    columns_to_drop = [col for col in entsoe_data.columns if col[1] == "Actual Consumption"]
    entsoe_data = entsoe_data.drop(columns=columns_to_drop)
    # If certain column names are in the format of a tuple like (energy_type, 'Actual Aggregated'),
    # these column names are transformed into strings using the value of energy_type.
    entsoe_data.columns = [
        (col[0] if isinstance(col, tuple) else col) for col in entsoe_data.columns
    ]

    # Impute missing values
    entsoe_data, imputation_logs = _impute_data(entsoe_data)
    
    # if Config.get("enable_logging"):
    #     pass

    return entsoe_data


def _entsoe_get_total_forecast(country: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
    """
    Fetches the aggregated day ahead total generation forecast data (14.1.C) for the given country within the given start and end date
    Args:
        country (str): 2 letter country code.
        start (datetime): The start date for data retrieval.
        end (datetime): The end date for data retrieval.
    Returns:
        entsoe_data (pandas.DataFrame): Pulled and imputed Entsoe data.
        imputation_logs (list): Imputation logs.  
    """
    client = entsoePandas(api_key = Config.ENTSOE_TOKEN)
    try:
        entsoe_raw_data = client.query_generation_forecast(
            country,
            start = pd.Timestamp(start_time),
            end = pd.Timestamp(end_time) 
        )
    except Exception as e:
        raise e("Error in fetching data from ENTSOE.")
    # if the data is a series instead of a dataframe, it will be converted to a dataframe
    if isinstance(entsoe_raw_data, pd.Series):
        entsoe_raw_data = entsoe_raw_data.to_frame(name = "Actual Aggregated")
    
    # refining the data
    entsoe_data, imputation_log = _impute_data(entsoe_raw_data)
    
    # if Config.get("enable_logging"):
    #     pass
    
    # rename the single column
    entsoe_data.rename(
        columns = {"Actual Aggregated": "total"}, 
        inplace=True
    )
    # refined_data = refined_data.reset_index(drop=True)
    return entsoe_data


def _entsoe_get_wind_solar_forecast(country: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
    """
    Fetches the aggregated day ahead wind and solar generation forecast data  (14.1.D) for the given country within the given start and end date
    Args:
        country (str): 2 letter country code.
        start (datetime): The start date for data retrieval.
        end (datetime): The end date for data retrieval.
    Returns:
        entsoe_data (pandas.DataFrame): Pulled and imputed Entsoe data.
        imputation_logs (list): Imputation logs.   
    """
    client = entsoePandas(api_key = Config.ENTSOE_TOKEN)
    
    try:
        entsoe_raw_data = client.query_wind_and_solar_forecast(
            country,
            start = pd.Timestamp(start_time),
            end = pd.Timestamp(end_time) 
        )
    except Exception as e:
        raise e("Error in fetching data from ENTSOE.")
    
    # Impute missing data
    entsoe_data, imputation_logs = _impute_data(entsoe_raw_data)

    # if Config.get("enable_logging"):
    #     pass

    # calculating the total renewable consumption value
    validCols = set(["Solar", "Wind Offshore", "Wind Onshore"])
    existingCol = list(set(entsoe_data.columns).intersection(validCols))
    entsoe_data["totalRenewable"] = entsoe_data[existingCol].sum(axis=1)
    
    return entsoe_data


def get_entsoe_production_percentage(country: str, start_time: datetime, end_time: datetime, convert_to_hourly_intervals: bool = True) -> pd.DataFrame:
    """
    Returns time series data containing the percentage of energy generated from various sources for the specified country within the selected time period.
    It also includes the percentage of energy from renewable and non renewable sources. The data is transformed into hourly time intervals if the flag is set.
    Args:
        country (str): 2 letter country code.
        start (datetime): The start date for data retrieval.
        end (datetime): The end date for data retrieval.
        convert_to_hourly_intervals (bool): Convert the data to 60 minute intervals. (default: True)
    Returns:
        A pandas.DataFrame containing the hourly energy production mix and percentage of energy generated from renewable and non renewable sources.
    """

    entsoe_raw_data = _entsoe_get_production(
        country,
        start_time,
        end_time
    )
    
    if convert_to_hourly_intervals:
        entsoe_data = _convert_to_hourly_intervals(entsoe_raw_data)
    else:
        entsoe_data = entsoe_raw_data

    allCols = entsoe_data.columns.tolist()
    # find out which columns are present in the data out of all the possible columns in the defined categories
    renPresent = list(set(allCols).intersection(renewableSources))
    renPresentWS = list(set(allCols).intersection(windSolarOnly))
    nonRenPresent = list(set(allCols).intersection(nonRenewableSources))
    # find total renewable, total non renewable and total energy values
    entsoe_data["renewableTotal"] = entsoe_data[renPresent].sum(axis=1)
    entsoe_data["renewableTotalWS"] = entsoe_data[renPresentWS].sum(axis=1)
    entsoe_data["nonRenewableTotal"] = entsoe_data[nonRenPresent].sum(axis=1)
    entsoe_data["total"] = entsoe_data["nonRenewableTotal"] + entsoe_data["renewableTotal"]
    # calculate percent renewable
    entsoe_data["percentRenewable"] = (entsoe_data["renewableTotal"] / entsoe_data["total"]) * 100
    # refine percentage values : replacing missing values with 0 and converting to integer
    entsoe_data["percentRenewable"] = entsoe_data["percentRenewable"].fillna(0).round().astype(int)
    entsoe_data["percentRenewableWS"] = (entsoe_data["renewableTotalWS"] / entsoe_data["total"]) * 100
    entsoe_data["percentRenewableWS"] = entsoe_data["percentRenewableWS"].fillna(0).round().astype(int)

    # individual energy source percentage calculation
    allAddkeys = list(energy_type.keys())

    for ky in allAddkeys:
        keys_available = list(set(allCols).intersection(energy_type[ky]))
        fieldName = ky + "_per"
        entsoe_data[fieldName] = entsoe_data[keys_available].sum(axis=1)
        entsoe_data[fieldName] = (entsoe_data[fieldName] / entsoe_data["total"]) * 100
        entsoe_data[fieldName] = entsoe_data[fieldName].fillna(0).astype(int)

    return entsoe_data


def get_entsoe_forecast_percent_renewable(country: str, start_time: datetime, end_time: datetime, convert_to_hourly_intervals: bool = True) -> pd.DataFrame:
    """
    Returns time series data  comprising the forecast of the percentage of energy generated from
    renewable sources (specifically, wind and solar) for the specified country within the selected time period.
    - The data source is the  ENTSOE APIs and involves combining data from 2 APIs : total forecast, wind and solar forecast.
    - the data frame includes : `totalRenewable`,`total`,`percent_renewable`,`posix_timestamp`

    :param str country: The 2 alphabet country code.
    :param datetime start_time: The start date for data retrieval. A Datetime object. Note that this date will be rounded to the nearest hour.
    :param datetime end_time: The end date for data retrieval. A datetime object. This date is also rounded to the nearest hour.
    :param bool convert_to_hourly_intervals: Convert retrieved data to hourly intervals. Defaults to ``True``. 
    :return: A pandas DataFrame containing the retrieved data. 
    :rtype: pandas.DataFrame
    """
    
    entsoe_data = _entsoe_get_total_forecast(country, start_time, end_time)
    if convert_to_hourly_intervals:
        entsoe_data = _convert_to_hourly_intervals(entsoe_data)
    
    entsoe_wind_solar_data = _entsoe_get_wind_solar_forecast(country, start_time, end_time)
    if convert_to_hourly_intervals:
        entsoe_wind_solar_data = _convert_to_hourly_intervals(entsoe_wind_solar_data)
        
    entsoe_wind_solar_data["total"] = entsoe_data["total"]
    entsoe_wind_solar_data["percentRenewable"] = (entsoe_wind_solar_data["totalRenewable"] / entsoe_wind_solar_data["total"]) * 100
    entsoe_wind_solar_data["percentRenewable"] = entsoe_wind_solar_data["percentRenewable"].fillna(0).round().astype(int)
    # entsoe_wind_solar_data = entsoe_wind_solar_data.rename(columns={"percentRenewable": "percent_renewable"})

    return entsoe_wind_solar_data