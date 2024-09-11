from .loadshift_time import predict_optimal_time

def predict_optimal_location(
    forecast_data,
    estimated_runtime_hours,
    estimated_runtime_minutes,
    percent_renewable,
    hard_finish_date,
    timeintervals,
):
    """
    Determines the optimal location and time  to run a computation using  energy data of the selected locations
    """
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



def predict_optimal_location_now():
    print()



def get_location_forecast(
    estimated_runtime_hours,
    estimated_runtime_minutes,
    percent_renewable,
    hard_finish_date,
    area_codes,
    request_logging,
    project_hash,
):
    # generate a string with cache data for the current day
    api_token = get_location_forecast.token

    print("Starting prediction")
    # parse the parameters
    start = datetime.now(timezone.utc)
    start = start - timedelta(minutes=start.minute % 60)
    start = start.strftime("%Y%m%d%H%M")
    deadline = datetime.fromtimestamp(hard_finish_date)
    deadline = (deadline - timedelta(minutes=deadline.minute % 60)).strftime(
        "%Y%m%d%H%M"
    )

    forecast_data = {}
    co2_intensity = {}
    timeintervals = {}
    for a in area_codes:
        country = a[0]

        data = energy(country, start, deadline) # todo fix
        if data["data_available"]:
            forecast_data[country] = data["data"]
            timeintervals[country] = data["timeInterval"]
            co2_intensity[country] = pull_current_co2_intensity(country)

    (
        suggested_start_timestamp,
        message,
        avg_perc_ren,
        suggested_country,
    ) = predict_optimal_location(
        forecast_data,
        estimated_runtime_hours,
        estimated_runtime_minutes,
        percent_renewable,
        hard_finish_date,
        timeintervals,
    )

    time_request = True
    location_request = True
    carbon_intensity = co2_intensity[suggested_country]["carbonIntensity"]
    fossil_fuel_percent = co2_intensity[suggested_country]["fossilFuelPercentage"]
    date_co2_signal_update = parser.parse(co2_intensity[suggested_country]["datetime"])

    a_code = [str(a[1]) for a in area_codes]
    a_code = ",".join(a_code)
    countries = [a[0] for a in area_codes]
    countries = ",".join(countries)

    try:
        if request_logging:
            print("Logging request")
            time_request = True
            location_request = True
            # Log the request and the predicted for documentation purposes
            random_process_hash = log_request(
                api_token,
                estimated_runtime_hours,
                estimated_runtime_minutes,
                percent_renewable,
                hard_finish_date,
                a_code,
                suggested_start_timestamp,
                message.value,
                time_request,
                location_request,
                carbon_intensity,
                fossil_fuel_percent,
                date_co2_signal_update,
                project_hash,
                suggested_country,
                countries,
            )
        else:
            random_process_hash = "none"

        response = _create_time_location_response(
            HTTPStatus.OK,
            message.value,
            suggested_start_timestamp,
            random_process_hash,
            suggested_country,
            avg_perc_ren,
        )

    except Exception:
        # No matter what happens otherwise the valid prediction will be the current time
        response = _create_time_location_response(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Failure",
            int(datetime.now(timezone.utc).timestamp()),
            random_process_hash,
            "UTOPIA",
            0,
        )

    return response
