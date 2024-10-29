from enum import Enum


# this mod contains all the messages in the system
class Message(Enum):
    OPTIMAL_TIME = "OPTIMAL_TIME"
    NO_DATA = "NO_DATA"
    RUNTIME_LONGER_THAN_DEADLINE_ALLOWS = ("RUNTIME_LONGER_THAN_DEADLINE_ALLOWS",)
    COUNTRY_404 = "COUNTRY_404"
    INVALID_PREDICTION_CRITERIA = "INVALID_PREDICTION_CRITERIA"  # valid criteria : "percent_renewable","carbon_intensity"
    ZERO_OR_NEGATIVE_RUNTIME = "ZERO_OR_NEGATIVE_RUNTIME"
    NEGATIVE_PERCENT_RENEWABLE = "NEGATIVE_PERCENT_RENEWABLE"
    INVALID_ENERGY_TYPE = "INVALID_ENERGY_TYPE"
    NO_ENERGY_SOURCE = ("No energy source found for the country",)
    INVALID_DATA = ("Invalid data provided",)
    ENERGY_DATA_FETCHING_ERROR = "Error in fetching energy data for the country"


class CodegreenDataError(Exception):
    pass
