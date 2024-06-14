import json 
import importlib.resources as il
from .. import data as dt

def get_country_metadata():
  with il.open_text(dt,"country_metadata.json") as json_file:
    data = json.load(json_file)
    return data


def get_country_energy_source(country_code):
  metadata = get_country_metadata()
  if country_code in metadata.keys():
    return metadata[country_code]["energy_source"]
  else :
    return None
  
  