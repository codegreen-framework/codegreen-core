# run this as :  poetry run python -m codegreen_core.tools.test

# import matplotlib
# # matplotlib.use('TkAgg')  # Or 'Qt5Agg'

# from .carbon_emission import plot_ce_jobs
# from datetime import datetime 
# server1 = {
#     "country":"DE",
#     "number_core":16,
#     "memory_gb": 254,
# }
# jobs = [
#     {
#         "start_time":datetime(2024,11,10),
#         "runtime_minutes" : 120
#     }
# ]


# plot_ce_jobs(server1,jobs)

from codegreen_core.tools.loadshift_time import predict_now
from datetime import datetime, timedelta

cases = [
  {
    "country":"DE",
    "h": 5,
    "hd": datetime.now()+ timedelta(hours=20) 
  },
  {
    "country":"DE",
    "h": 4,
    "hd": datetime.now()+ timedelta(hours=15) 
  },
  {
    "country":"DK",
    "h": 4,
    "hd": datetime.now()+ timedelta(hours=15) 
  },
  {
    "country":"FR",
    "h": 4,
    "hd": datetime.now()+ timedelta(hours=15) 
  },
  {
    "country":"SE",
    "h": 4,
    "hd": datetime.now()+ timedelta(hours=15) 
  }
]

for c in cases:
  print(predict_now(c["country"],c["h"],0,c["hd"]))
