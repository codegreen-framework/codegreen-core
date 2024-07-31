import pytest
from codegreen_core.data import entsoe,energy,carbon_intensity
from codegreen_core.utils.message import CodegreenDataError
from datetime import datetime

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

