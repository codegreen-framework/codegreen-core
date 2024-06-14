from enum import Enum

# this mod contains all the messages in the system 
class Message(Enum):
    OPTIMAL_TIME = "OPTIMAL_TIME"
    NO_DATA = "NO_DATA"
    RUNTIME_LONGER_THAN_DEADLINE_ALLOWS = "RUNTIME_LONGER_THAN_DEADLINE_ALLOWS",
    COUNTRY_404 = "COUNTRY_404"
    INVALID_PREDICTION_CRITERIA = "INVALID_PREDICTION_CRITERIA" # valid criteria : "percent_renewable","carbon_intensity"
