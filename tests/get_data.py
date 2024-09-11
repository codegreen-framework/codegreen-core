# this file contains the methods to fetch country data to be used to test prediction times 

from codegreen_core.data import energy
from codegreen_core.data.metadata import get_country_metadata
from codegreen_core.data.entsoe import renewableSources,nonRenewableSources

from datetime import datetime
import pandas as pd
import numpy as np
import traceback

def gen_test_case(start,end,label):
  country_list = get_country_metadata()
  cases = []
  for ci in country_list.keys():
    cdata = country_list[ci]
    cdata["country"] = ci
    cdata["start_time"] = start
    cdata["end_time"]=  end
    cdata["file"] = ci+label
    cases.append(cdata)
  return cases

def fetch_data(case):
  data = energy(case["country"],case["start_time"],case["end_time"])
  data.to_csv("./data/"+case["file"]+".csv")
  print(case["file"])

# test_cases_1 = gen_test_case(datetime(2024,1,1),datetime(2024,1,5),"1")
# for c in test_cases_1:
#   fetch_data(c)

# test_cases_2 = gen_test_case(datetime(2023,7,5),datetime(2023,7,10),"2")
# for c in test_cases_2:
#   print(c)
#   fetch_data(c)
   
def test_cases_3():
  cases = [
    {
      "country":"GR",
      "start_time":datetime(2024,1,1),
      "end_time":datetime(2024,6,30),
      "file":"GR3"
    },
    {
      "country":"LT",
      "start_time":datetime(2024,1,1),
      "end_time":datetime(2024,6,30),
      "file":"LT3"
    },
    {
      "country":"DE",
      "start_time":datetime(2024,1,1),
      "end_time":datetime(2024,6,30),
      "file":"DE3"
    }
  ]
  for c in cases:
    fetch_data(c)


# test_cases_3()

# Defining a function to convert and format the datetime
def convert_format(date_str):
    # Convert string to datetime
    date_time_obj = datetime.strptime(date_str, '%d.%m.%Y %H:%M')
    # Format datetime object to the desired format
    return date_time_obj.strftime('%Y%m%d%H%M')

def compute_rrs_error(downloaded,fetched):
  d = pd.read_csv("./data/"+downloaded+".csv")
  d[['startTimeUTC', 'end']] = d['MTU'].str.extract(r'(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}) - (\d{2}\.\d{2}\.\d{4} \d{2}:\d{2})')
  # Applying the conversion function to the start and end columns
  d['startTimeUTC'] = d['startTimeUTC'].apply(convert_format)
  d['startTimeUTC'] = d['startTimeUTC'].astype('int64')
  d['end'] = d['end'].apply(convert_format)
  f = pd.read_csv("./data/"+fetched+".csv")
  all_e = set(renewableSources + nonRenewableSources)
  e_cols = set(f.columns.tolist())
  e_present = list(all_e & e_cols)
  combined = f.merge(d,on="startTimeUTC")
  summary = {}
  for e in e_present:
    #print(f.iloc[0][e])
    d_col = e+"  - Actual Aggregated [MW]"
    res_col = "residual-"+e 
    combined[res_col] = combined[d_col] - combined[e]
    summary[e] = np.sqrt(np.sum(combined[res_col]))
    #print(d.iloc[0][d_col])
  print(summary)
  return summary

#compute_rrs_error("gr_24_actual_downloaded","GR3")
#compute_rrs_error("de_24_actual_downloaded","DE3")
#compute_rrs_error("lt_24_actual_downloaded","LT3")


def get_forecast_for_testing():
  try :
    dates1 = [
      [datetime(2024,1,5),datetime(2024,1,10),1],
      [datetime(2024,3,15),datetime(2024,3,20),3],
      [datetime(2024,5,10),datetime(2024,5,15),5],
      [datetime(2024,8,1),datetime(2024,8,10),8]
    ]
    clist = gen_test_case(datetime(2024,7,5),datetime(2024,7,10),"")
    test_data = pd.DataFrame()
    for c in clist :
      for r in dates1:
        try:
          data = energy(c["country"],r[0],r[1],type="forecast")
          print(c["country"]," ",r[2])
          # data["data"].to_csv("data/"+c["country"]+str(r[2])+"_forecast.csv")
          data["data"]["file_id"] = c["country"]+str(r[2])
          print(data)
          test_data = pd.concat([test_data,data["data"]], ignore_index=True)
        except Exception as e:
          print(traceback.format_exc())
          print(e)
      
      test_data.to_csv("data/prediction_testing_data.csv")
  except Exception :
    print(Exception)

# get_forecast_for_testing()


data = energy("DE",datetime(2024,9,11),datetime(2024,9,12),"generation",False)
print(data)