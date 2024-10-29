from .loadshift_time import predict_optimal_time
from datetime import datetime
from ..data import energy
from ..utilities.message import CodegreenDataError


def predict_optimal_location_now(
    country_list: list,
    estimated_runtime_hours: int,
    estimated_runtime_minutes: int,
    percent_renewable: int,
    hard_finish_date: datetime,
) -> tuple:
    """
    Given a list of countries, returns the best location where a computation can be run based on the input criteria
    """
    print()
    # first get data
    start_time = datetime.now()
    forecast_data = (
        {}
    )  # will contain energy data for each country for which data is available
    for country in country_list:
        try:
            print(country)
            energy_data = energy(country, start_time, hard_finish_date, "forecast")
            forecast_data[country] = energy_data["data"]
        except CodegreenDataError as c:
            print(c)
    # print(forecast_data)
    return predict_optimal_location(
        forecast_data,
        estimated_runtime_hours,
        estimated_runtime_minutes,
        percent_renewable,
        hard_finish_date,
    )


def predict_optimal_location(
    forecast_data,
    estimated_runtime_hours,
    estimated_runtime_minutes,
    percent_renewable,
    hard_finish_date,
    request_date=None,
):
    """
    Determines the optimal location and time  to run a computation using  energy data of the selected locations
    """
    ## obtain the optimal start time for each country
    best_values = {}
    current_best = -1
    best_country = "UTOPIA"
    for country in forecast_data:
        print(country)
        optimal_start, message, avg_percentage_renewable = predict_optimal_time(
            forecast_data[country],
            estimated_runtime_hours,
            estimated_runtime_minutes,
            percent_renewable,
            hard_finish_date,
            request_date,
        )
        best = {
            "optimal_start": optimal_start,
            "message": message,
            "avg_percentage_renewable": avg_percentage_renewable,
        }
        print(best)
        if avg_percentage_renewable > current_best:
            best_country = country
            best_values = best
            current_best = avg_percentage_renewable
            print("Update")

    return (
        best_values["optimal_start"],
        best_values["message"],
        best_values["avg_percentage_renewable"],
        best_country,
    )
