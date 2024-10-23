import pytest
from codegreen_core.data import energy
from codegreen_core.data.entsoe import renewableSources
from codegreen_core.utilities.message import CodegreenDataError
from datetime import datetime
import pandas as pd

class TestEnergyData:
  def test_valid_country(self):
    with pytest.raises(ValueError):
      energy(91,datetime(2024,1,1),datetime(2024,1,2))
   
  def test_valid_starttime(self):
    with pytest.raises(ValueError):
      energy("DE","2024,1,1",datetime(2024,1,2))
  
  def test_valid_endtime(self):
    with pytest.raises(ValueError):
      energy("DE",datetime(2024,1,2),"2024,1,1")
  
  def test_valid_type(self):
    with pytest.raises(ValueError):
     energy("DE",datetime(2024,1,1),datetime(2024,1,2),"magic")

  def test_country_no_vaild_energy_source(self):
    with pytest.raises(CodegreenDataError):
     energy("IN",datetime(2024,1,1),datetime(2024,1,2))

  def test_entsoe_generation_data(self):
    cases = [
      {
        "country":"DE",
        "start":datetime(2024,2,1),
        "end":datetime(2024,2,2),
        "dtype": 'generation' ,
        "file": "tests/data/generation_DE_24_downloaded.csv",
        "interval60": False
      },
      {
        "country":"DE",
        "start":datetime(2024,3,20),
        "end":datetime(2024,3,24),
        "dtype": 'generation' ,
        "file": "tests/data/generation_DE_24_downloaded.csv",
        "interval60": False
      },
      # {
      #   "country":"DE",
      #   "start":datetime(2024,1,1),
      #   "end":datetime(2024,1,5),
      #   "dtype": 'generation' ,
      #   "file": "data/DE_24_generation_downloaded.csv",
      #   "interval60": False,
      #   "note":"this has issues,Hydro Pumped Storage values do not match "
      # },
      {
        "country":"GR",
        "start":datetime(2024,3,20),
        "end":datetime(2024,3,24),
        "dtype": 'generation' ,
        "file": "tests/data/generation_GR_24_downloaded.csv",
        "interval60": True
      },
      {
        "country":"GR",
        "start":datetime(2024,1,25),
        "end":datetime(2024,1,28),
        "dtype": 'generation' ,
        "file": "tests/data/generation_GR_24_downloaded.csv",
        "interval60": True
      }

    ]
    for case in cases:
      # intervals = int((case["end"].replace(minute=0, second=0, microsecond=0) - case["start"].replace(minute=0, second=0, microsecond=0)).total_seconds() // 3600)
      # print(intervals)
      if case["dtype"]=="generation":
        d = energy(case["country"],case["start"],case["end"],case["dtype"],case["interval60"])
        data = d["data"]
        data_verify = pd.read_csv(case["file"])
        data_verify['start_date'] = data_verify['MTU'].str.split(' - ').str[0]
        data_verify['end_date'] = data_verify['MTU'].str.split(' - ').str[1].str.replace(' (UTC)', '', regex=False)
        data_verify['start_date'] = pd.to_datetime(data_verify['start_date'], format='%d.%m.%Y %H:%M')
        data_verify['end_date'] = pd.to_datetime(data_verify['end_date'], format='%d.%m.%Y %H:%M')
        start_utc = pd.to_datetime(case["start"])  # case["start"].astimezone(pd.Timestamp.now(tz='UTC').tzinfo) if case["start"].tzinfo is None else case["start"]
        end_utc =  pd.to_datetime(case["end"]) #case["end"].astimezone(pd.Timestamp.now(tz='UTC').tzinfo) if case["end"].tzinfo is None else case["end"]
        filtered_df = data_verify[(data_verify['start_date'] >= start_utc) & (data_verify['start_date'] < end_utc)]
        allCols = data.columns.tolist()
        renPresent = list(set(allCols).intersection(renewableSources))
        for e in renPresent:
          difference = filtered_df[e+"  - Actual Aggregated [MW]"] - data[e]
          sum_of_differences = difference.sum()
          print(e)
          print(sum_of_differences)
          print(filtered_df[e+"  - Actual Aggregated [MW]"].to_list())
          print(data[e].to_list())
          print(difference.to_list())
          print("===")
          assert sum_of_differences == 0.0
      # else :
      #   print("")

""" todo 
- test cases where some data is missing and has to be replaced with average
"""
