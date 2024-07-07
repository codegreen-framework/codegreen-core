import json 
import importlib.resources as il
import pandas as pd
from .. import data as dt

def get_country_metadata():
  """
  This method returns the "country_metadata.json" metadata file stored in the data folder.
  This file contains a list of countries for which codegreen can fetch the required data to perform further calculations.
  the key is the country code and the value contains 
    - country name 
    - energy_source : the source that can be used to fetch energy data for this country 
        - as  of now we support fetching energy data from the ENTSOE portal for countries in the European Union
    - carbon_intensity_method : this is the methodology to be used to calculate the CI values based on the energy fetched
      - the current methodologies supported are described in "carbon_intensity.py" file
  """
  with il.open_text(dt,"country_metadata.json") as json_file:
    data = json.load(json_file)
    return data

def get_country_energy_source(country_code):
  """
  Returns the energy source (if available) to gather energy data. These values are stored in the "country_metadata.json" file.
  If the energy source does not exists, None is returned
  """
  metadata = get_country_metadata()
  if country_code in metadata.keys():
    return metadata[country_code]["energy_source"]
  else :
    return None
  
def get_default_ci_value(country_code): 
  """
    This method returns the default average Carbon Intensity for a given country. These values are sourced from the International Electricity Factors, 
    https://www.carbonfootprint.com/international_electricity_factors.html (accessed 5 July 2024)  and are stored in the "ci_default_value.csv" file. 
  """
  with il.open_text(dt,"ci_default_values.csv") as csv_file:
    data = pd.read_csv(csv_file)
    row = data.loc[data['code'] == country_code]
    if not row.empty:
      val = row.iloc[0]['kgCO2e_per_kWh']
      return val
    else :
      return None
