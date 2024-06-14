from .time import predict_optimal_time

def predict_optimal_location(
    forecast_data,
    estimated_runtime_hours,
    estimated_runtime_minutes,
    percent_renewable,
    hard_finish_date,
    timeintervals,
):
    ## obtain the optimal start time for each country
    optimal_start_times = {}
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
            granularity=timeintervals[country],
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
