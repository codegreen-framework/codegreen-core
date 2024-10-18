# to log stuff

from .config import Config
from datetime import datetime
import os
import csv


def time_prediction(data):
  if Config.get("enable_time_prediction_logging")==True:
    current_date = datetime.now()
    file_name = f"{current_date.strftime('%B')}_{current_date.year}.csv"
    file_location = os.path.join(Config.get("time_prediction_log_folder_path"), file_name)
    file_exists = os.path.exists(file_location)
    # Open the file in append mode
    with open(file_location, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data.keys())
        # If the file doesn't exist, write the header
        if not file_exists:
            writer.writeheader()
        # Append the data to the file
        writer.writerow(data)
  else:
    print("Logging not enabled")