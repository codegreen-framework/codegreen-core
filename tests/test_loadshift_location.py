from codegreen_core.tools.loadshift_location import predict_optimal_location,predict_optimal_location_now
from datetime import datetime,timedelta
import pandas as pd
import pytz

def test_location_now():
 a,b,c,d =   predict_optimal_location_now(["DE","HU","AT","FR","AU","NO"],5,0,50,datetime(2024,9,13))
 print(a,b,c,d)

# test_location_now()

def fetch_data(month_no,countries):
  data = pd.read_csv("data/prediction_testing_data.csv")
  forecast_data = {}
  for c in countries:
    filter = data["file_id"] == c+""+str(month_no)
    d = data[filter].copy()
    if(len(d)>0):
      forecast_data[c] = d
  return forecast_data
 
def test_locations():
  cases = [
  {
   "month":1,
   "c":["DE","NO","SW","ES","IT"],
   "h":5,
   "m":0,
   "p":50,
   "s":"2024-01-05 02:00:00",
   "e": 10
  }
  ]
  for case in cases:
    data = fetch_data(case["month"],case["c"])
    start_utc = datetime.strptime(case["s"], '%Y-%m-%d %H:%M:%S')
    start_utc = pytz.UTC.localize(start_utc)
    start = start_utc.astimezone(pytz.timezone('Europe/Berlin'))
    end = (start + timedelta(hours=case["e"]))
    a,b,c,d = predict_optimal_location(data,case["h"],case["m"],case["p"],end,start)
    print(a,b,c,d)

# test_locations()