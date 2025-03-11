from ..utilities.config import Config
import pandas as pd
from datetime import datetime, timedelta
from entsoe import EntsoePandasClient as entsoePandas

import traceback

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



# helper methods


def _get_API_token() -> str:
    """reads the ENTOSE api token required to access data from the portal. must be defined in the config file"""
    return Config.get("ENTSOE_token")


def _refine_data(options, data1):
    """Returns a refined version of the dataframe.
    The Refining process involves finding missing values and substituting them with average values.
    Additionally, a new column `startTimeUTC` is appended to the dataframe representing the start time in UTC
    :param options
    :param data1 : the dataframe that has to be refined. Assuming it has a datetime index in local time zone with country info
    :returns {"data":Refined data frame, "refine_logs":["list of refinements made"]}
    """
    # calculate the duration of the time series by finding the difference between the
    # first and the second index (which is of the type `datatime``) and convert this into minutes
    #print(data1)
    if len(data1) == 1:
        return {"data": None, "refine_logs": ["Only one record cannot be processed"]}

    durationMin = (data1.index[1] - data1.index[0]).total_seconds() / 60
    # initializing the log list
    refine_logs = []
    refine_logs.append(
        "Row count : Fetched =  " + str(len(data1)) + ", duration : " + str(durationMin)
    )
    """
    Determining the list of records that are absent in the time series by initially creating a set containing all 
    the expected timestamps within the start and end time range. Then, we calculate the difference between 
    this set and the timestamps present in the actual DataFrame.
    """
    start_time = data1.index.min()
    end_time = data1.index.max()
    expected_timestamps = pd.date_range(
        start=start_time, end=end_time, freq=f"{durationMin}min"
    )
    expected_df = pd.DataFrame(index=expected_timestamps)
    missing_indices = expected_df.index.difference(data1.index)
    """ Next, we fill in the missing values. 
    For each absent timestamp, we examine if the entries for the same day exists. 
    If they do, we use the day average for each column in the Dataframe. 
    Else, we use the average of the entire data
    """
    totalAverageValue = data1.mean().fillna(0).round().astype(int)
    for index in missing_indices:
        rows_same_day = data1[data1.index.date == index.date()]
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
        new_row = pd.DataFrame([avg_val], columns=data1.columns, index=[index])
        data1 = pd.concat([data1, new_row])

    """ Currently, the datatime index is set in the time zone of the data's country of origin. 
    We convert it into UTC and add it as a new column named 'startTimeUTC' in the 'YYYYMMDDhhmm' format.
    """
    data1["startTimeUTC"] = (data1.index.tz_convert("UTC")).strftime("%Y%m%d%H%M")
    # data1['startTimeLocal'] = (data1.index).strftime('%Y%m%d%H%M')
    # since missing values are concatenated to the dataframe, it is also sorted based on the datetime index
    data1.sort_index(inplace=True)
    return {"data": data1, "refine_logs": refine_logs}

def _convert_local_to_utc(dte):
    # datetime obj is converted from local time zone to utc 
    local_timezone = datetime.now().astimezone().tzinfo
    return pd.Timestamp(dte,tz=local_timezone).tz_convert('UTC')

def _entsoe_get_actual_generation(options={"country": "", "start": "", "end": ""}):
    """Fetches the aggregated actual generation per production type data (16.1.B&C) for the given country within the given start and end date
    params: options = {country (2 letter country code),start,end} . Both the dates are in the YYYYMMDDhhmm format and the local time zone
    returns : {"data":pd.DataFrame, "duration":duration (in min) of the time series data, "refine_logs":"notes on refinements made" }
    """
    utc_start = _convert_local_to_utc(options["start"]) 
    utc_end =   _convert_local_to_utc(options["end"]) 
    client1 = entsoePandas(api_key=_get_API_token())
    try :
        data1 = client1.query_generation(
            options["country"],
            start = utc_start ,
            end = utc_end ,
            psr_type=None,
        )
    except Exception as e:
        print("Error in fetching data from ENTSOE")
        return {
            "data": None,
            "duration": 0,
        }
    # drop columns with actual consumption values (we want actual aggregated generation values)
    columns_to_drop = [col for col in data1.columns if col[1] == "Actual Consumption"]
    data1 = data1.drop(columns=columns_to_drop)
    # If certain column names are in the format of a tuple like (energy_type, 'Actual Aggregated'),
    # these column names are transformed into strings using the value of energy_type.
    data1.columns = [
        (col[0] if isinstance(col, tuple) else col) for col in data1.columns
    ]
    # refine the dataframe. see the refine method
    data2 = _refine_data(options, data1)
    refined_data = data2["data"]
    
    # finding the duration of the time series data
    if(refined_data is not None):
        refined_data = refined_data.reset_index(drop=True)
        durationMin = (data1.index[1] - data1.index[0]).total_seconds() / 60
    else:
        durationMin = 0 
    return {
        "data": refined_data,
        "duration": durationMin,
        "refine_logs": data2["refine_logs"],
    }


def _entsoe_get_total_forecast(options={"country": "", "start": "", "end": ""}):
    """Fetches the aggregated day ahead total generation forecast data (14.1.C) for the given country within the given start and end date
    params: options = {country (2 letter country code),start,end} . Both the dates are in the YYYYMMDDhhmm format and the local time zone
    returns : {"data":pd.DataFrame, "duration":duration (in min) of the time series data, "refine_logs":"notes on refinements made" }
    """
    client = entsoePandas(api_key=_get_API_token())
    data = client.query_generation_forecast(
        options["country"],
        start=_convert_local_to_utc(options["start"]) ,
        end=_convert_local_to_utc(options["end"]) 
    )
    # if the data is a series instead of a dataframe, it will be converted to a dataframe
    if isinstance(data, pd.Series):
        data = data.to_frame(name="Actual Aggregated")
    durationMin = (data.index[1] - data.index[0]).total_seconds() / 60
    # refining the data
    data2 = _refine_data(options, data)
    refined_data = data2["data"]
    # rename the single column
    newCol = {"Actual Aggregated": "total"}
    refined_data.rename(columns=newCol, inplace=True)
    refined_data = refined_data.reset_index(drop=True)
    return {
        "data": refined_data,
        "duration": durationMin,
        "refine_logs": data2["refine_logs"],
    }


def _entsoe_get_wind_solar_forecast(options={"country": "", "start": "", "end": ""}):
    """Fetches the aggregated day ahead wind and solar generation forecast data  (14.1.D) for the given country within the given start and end date
    params: options = {country (2 letter country code),start,end} . Both the dates are in the YYYYMMDDhhmm format and the local time zone
    returns : {"data":pd.DataFrame, "duration":duration (in min) of the time series data, "refine_logs":"notes on refinements made" }
    """
    client = entsoePandas(api_key=_get_API_token())
    data = client.query_wind_and_solar_forecast(
        options["country"],
        start=_convert_local_to_utc(options["start"]) ,
        end=_convert_local_to_utc(options["end"]) 
    )
    durationMin = (data.index[1] - data.index[0]).total_seconds() / 60
    # refining the data
    data2 = _refine_data(options, data)
    refined_data = data2["data"]
    # calculating the total renewable consumption value
    validCols = ["Solar", "Wind Offshore", "Wind Onshore"]
    existingCol = []
    for col in validCols:
        if col in refined_data.columns:
            existingCol.append(col)
    refined_data["totalRenewable"] = refined_data[existingCol].sum(axis=1)
    refined_data = refined_data.reset_index(drop=True)
    return {
        "data": refined_data,
        "duration": durationMin,
        "refine_logs": data2["refine_logs"],
    }


def _convert_to_60min_interval(rawData):
    """Given the rawData obtained from the ENTSOE API methods, this function converts the DataFrame into
    60-minute time intervals by aggregating data from multiple rows."""
    duration = rawData["duration"]
    if duration == 60:
        """If the duration is already 60, return data"""
        return rawData["data"]
    elif duration < 60:
        """
        First, we determine the number of rows needed to combine in order to obtain data in a 60-minute format.
        It is important to note that the rows are combined by taking the average of the row data, rather than the sum.
        """
        # determining how many rows need to be combined to get data in 60 min format.
        groupingFactor = int(60 / duration)
        oldData = rawData["data"]
        # check if there is enough data to convert to 60 min
        if (len(oldData) < groupingFactor):
            raise ValueError("Data cannot be converted into 60 min interval since there is inadequate number of rows in the data")
        
        oldData["startTimeUTC"] = pd.to_datetime(oldData["startTimeUTC"])
        start_time = oldData["startTimeUTC"].min()
        end_time = oldData["startTimeUTC"].max()
        durationMin = 60
        # removing the old timestamps (which are not 60 mins apart)
        dataColToRemove = ["startTimeUTC"]
        # dataColToRemove = ['startTimeUTC','startTimeLocal']
        oldData = oldData.drop(dataColToRemove, axis=1)

        oldData["group_id"] = oldData.index // groupingFactor
        newGroupedData = oldData.groupby("group_id").mean()
        # new timestamps which are 60 min apart
        new_timestamps = pd.date_range(
            start=start_time, end=end_time, freq=f"{durationMin}min", tz="UTC"
        )
        new_timestamps = new_timestamps.strftime("%Y%m%d%H%M")
        newGroupedData["startTimeUTC"] = new_timestamps
        return newGroupedData


def _convert_date_to_entsoe_format(dt: datetime):
    """ rounds the date to nearest hour """
    return dt.replace(minute=0, second=0, microsecond=0).strftime("%Y%m%d%H%M")


def _format_energy_data(df):
    start_time_column = df.pop("startTimeUTC")
    df.insert(0, "startTime", start_time_column)
    local_timezone = datetime.now().astimezone().tzinfo
    df["startTime"] = pd.to_datetime(df["startTime"], format="%Y%m%d%H%M").dt.tz_localize("UTC").dt.tz_convert(local_timezone)
    df.insert(1, "startTimeUTC", start_time_column)
    return df


# the main methods


def get_actual_production_percentage(country, start, end, interval60=True) -> dict:
    """Returns time series data containing the percentage of energy generated from various sources for the specified country within the selected time period.
    It also includes the percentage of energy from renewable and non renewable sources. The data is fetched from the APIs is subsequently refined.
    To obtain data in 60-minute intervals (if not already available), set 'interval60' to True

    :param str country: The 2 alphabet country code.
    :param datetime start: The start date for data retrieval. A Datetime object. Note that this date will be rounded to the nearest hour.
    :param datetime end: The end date for data retrieval. A datetime object. This date is also rounded to the nearest hour.
    :param boolean interval60: To convert the data into 60 min time interval. True by default 
    :return: A DataFrame containing the hourly energy production mix and percentage of energy generated from renewable and non renewable sources.
    :return: A dictionary containing:
      - `error`: A string with an error message, empty if no errors.
      - `data_available`: A boolean indicating if data was successfully retrieved.
      - `data`: A pandas DataFrame containing the energy data if available, empty DataFrame if not.
      - `time_interval` : the time interval of the DataFrame
      - `columns` :  a dict with column description
    :rtype: dict
    """
    try:
        if not isinstance(country, str):
            raise ValueError("Invalid country")
        if not isinstance(start, datetime):
            raise ValueError("Invalid start date")
        if not isinstance(end, datetime):
            raise ValueError("Invalid end date")

        if start > datetime.now():
            raise ValueError("Invalid start date. Generation data is only available for the past and not the future. Use the forecast API instead")

        if start > end :
            raise ValueError("Invalid date range. End date must be greater than the start date")
        
        # if end date is in the future and the start date is in the past , only data till the available moment will be returned.
        if end > datetime.now():
            raise ValueError("Invalid end date. Generation data is only available for the past and not the future. Use the forecast API instead")
            # this is not allowed because the entsoe-py returns error if it's greater than the present
            #warnings.warn("End date is in the future. Will fetch data only till the present")

        options = {
            "country": country,
            "start": start.replace(minute=0,second=0),
            "end": end.replace(second=0,minute=0),
            "interval60": interval60,
        }
        # print(options)
        # get actual generation data per production type and convert it into 60 min interval if required
        totalRaw = _entsoe_get_actual_generation(options)
        total = totalRaw["data"]
        
        if total is None :
            # no data to process further 
            return {
                "data": None,
                "data_available": False,
                "error": "Data is not available"
            }

        duration = totalRaw["duration"]
        if options["interval60"] == True and totalRaw["duration"] != 60.0:
            table = _convert_to_60min_interval(totalRaw)
            duration = 60
        else:
            table = total
        # finding the percent renewable
        allCols = table.columns.tolist()
        # find out which columns are present in the data out of all the possible columns in both the categories
        renPresent = list(set(allCols).intersection(renewableSources))
        renPresentWS = list(set(allCols).intersection(windSolarOnly))
        nonRenPresent = list(set(allCols).intersection(nonRenewableSources))
        # find total renewable, total non renewable and total energy values
        table["renewableTotal"] = table[renPresent].sum(axis=1)
        table["renewableTotalWS"] = table[renPresentWS].sum(axis=1)
        table["nonRenewableTotal"] = table[nonRenPresent].sum(axis=1)
        table["total"] = table["nonRenewableTotal"] + table["renewableTotal"]
        # calculate percent renewable
        table["percentRenewable"] = (table["renewableTotal"] / table["total"]) * 100
        # refine percentage values : replacing missing values with 0 and converting to integer
        table["percentRenewable"] = table["percentRenewable"].fillna(0)
        table["percentRenewable"] = table["percentRenewable"].round().astype(int)
        table["percentRenewableWS"] = (table["renewableTotalWS"] / table["total"]) * 100
        table["percentRenewableWS"] = table["percentRenewableWS"].fillna(0)
        table["percentRenewableWS"] = table["percentRenewableWS"].round().astype(int)

        # individual energy source percentage calculation
        allAddkeys = [
            "Wind",
            "Solar",
            "Nuclear",
            "Hydroelectricity",
            "Geothermal",
            "Natural Gas",
            "Petroleum",
            "Coal",
            "Biomass",
        ]
        for ky in allAddkeys:
            keys_available = list(set(allCols).intersection(energy_type[ky]))
            # print(keys_available)
            fieldName = ky + "_per"
            # print(fieldName)
            table[fieldName] = table[keys_available].sum(axis=1)
            table[fieldName] = (table[fieldName] / table["total"]) * 100
            table[fieldName] = table[fieldName].fillna(0)
            table[fieldName] = table[fieldName].astype(int)

        return {
            "data": _format_energy_data(table),
            "data_available": True,
            "time_interval": duration,
            "columns":gen_cols_from_data(table)
        }
    except Exception as e:
        # print(e)
        print(traceback.format_exc())
        return {
            "data": None,
            "data_available": False,
            "error": e,
            "time_interval": 0,
            "columns":None
        }

def gen_cols_from_data(df):
    """generates list of columns for the given energy generation dataframe"""
    allAddkeys = [
            "Wind",
            "Solar",
            "Nuclear",
            "Hydroelectricity",
            "Geothermal",
            "Natural Gas",
            "Petroleum",
            "Coal",
            "Biomass",
    ]

    allCols = df.columns.tolist()
    # find out which columns are present in the data out of all the possible columns in both the categories
    renPresent = list(set(allCols).intersection(renewableSources))
    nonRenPresent = list(set(allCols).intersection(nonRenewableSources))

    cols = {
            "renewable" : renPresent,
            "nonRenewable": nonRenPresent,
            "percentage":[]
        }
    for ky in allAddkeys:
            fieldName = ky + "_per"
            cols["percentage"].append(fieldName)
    return cols


def get_forecast_percent_renewable(
    country: str, start: datetime, end: datetime
) -> dict:
    """Returns time series data  comprising the forecast of the percentage of energy generated from
    renewable sources (specifically, wind and solar) for the specified country within the selected time period.

    - The data source is the  ENTSOE APIs and involves combining data from 2 APIs : total forecast, wind and solar forecast.
    - The time interval is 60 min
    - the data frame includes : `startTimeUTC`, `totalRenewable`,`total`,`percent_renewable`,`posix_timestamp`

    :param str country: The 2 alphabet country code.
    :param datetime start: The start date for data retrieval. A Datetime object. Note that this date will be rounded to the nearest hour.
    :param datetime end: The end date for data retrieval. A datetime object. This date is also rounded to the nearest hour.
    :return: A dictionary containing:
      - `error`: A string with an error message, empty if no errors.
      - `data_available`: A boolean indicating if data was successfully retrieved.
      - `data`: A DataFrame containing `startTimeUTC`, `totalRenewable`,`total`,`percent_renewable`,`posix_timestamp`.
      - `time_interval` : the time interval of the DataFrame
    :rtype: dict
    """
    try:
        # print(country,start,end)
        if not isinstance(country, str):
            raise ValueError("Invalid country")
        if not isinstance(start, datetime):
            raise ValueError("Invalid start date")
        if not isinstance(end, datetime):
            raise ValueError("Invalid end date")
        
        start = _convert_date_to_entsoe_format(start)
        end = _convert_date_to_entsoe_format(end)
        options = {"country": country, "start": start, "end": end}
        totalRaw = _entsoe_get_total_forecast(options)
        if totalRaw["duration"] != 60:
            total = _convert_to_60min_interval(totalRaw)
        else:
            total = totalRaw["data"]
        windsolarRaw = _entsoe_get_wind_solar_forecast(options)
        if windsolarRaw["duration"] != 60:
            windsolar = _convert_to_60min_interval(windsolarRaw)
        else:
            windsolar = windsolarRaw["data"]
        windsolar["total"] = total["total"]
        windsolar["percentRenewable"] = (
            windsolar["totalRenewable"] / windsolar["total"]
        ) * 100
        windsolar["percentRenewable"] = windsolar["percentRenewable"].fillna(0)
        windsolar["percentRenewable"] = (
            windsolar["percentRenewable"].round().astype(int)
        )
        windsolar = windsolar.rename(columns={"percentRenewable": "percent_renewable"})
        windsolar["startTimeUTC"] = pd.to_datetime(
            windsolar["startTimeUTC"], format="%Y%m%d%H%M"
        )
        windsolar["posix_timestamp"] = windsolar["startTimeUTC"].astype(int) // 10**9
        return {"data": _format_energy_data(windsolar), "data_available": True, "time_interval": 60}
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return {
            "data": None,
            "data_available": False,
            "error": Exception,
            "time_interval": 60,
        }
