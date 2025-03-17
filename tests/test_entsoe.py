import pytest
from codegreen_core.data.entsoe import * 
from codegreen_core.utilities.message import CodegreenDataError
from datetime import datetime
import pandas as pd


class TestEntsoeData:
    def test_actual_time_interval_original(self):
        data = get_actual_production_percentage("DE",datetime.now()-timedelta(hours=2),datetime.now(),interval60=False)
        assert data["time_interval"] == 15 and data["data_available"] == True
    def test_actual_time_interval_60min(self):
        data = get_actual_production_percentage("DE",datetime.now()-timedelta(hours=2),datetime.now())
        assert data["time_interval"] == 60 and data["data_available"] == True
    def test_actual_invalid_country1(self):
        data = get_actual_production_percentage("DE1",datetime.now()-timedelta(hours=3),datetime.now(),True)
        assert data["data_available"] == False # and isinstance(data["error"],ValueError)
    def test_actual_invalid_country2(self):
        data = get_actual_production_percentage(1234,datetime.now()-timedelta(hours=3),datetime.now(),True)
        assert data["data_available"] == False and isinstance(data["error"],ValueError)
    def test_actual_invalid_start(self):
        data = get_actual_production_percentage("DE","invalid",datetime.now(),True)
        assert data["data_available"] == False and isinstance(data["error"],ValueError)
    def test_actual_invalid_end(self):
        data = get_actual_production_percentage("DE",datetime.now(),"invalid",True)
        assert data["data_available"] == False and isinstance(data["error"],ValueError)
    def test_actual_invalid_date_range(self):
        # start > end
        data = get_actual_production_percentage("DE",datetime.now(),datetime.now()-timedelta(hours=3),True)
        assert data["data_available"] == False and isinstance(data["error"],ValueError)
    def test_actual_invalid_date_range2(self):
        # start > now
        data = get_actual_production_percentage("DE",datetime.now()+timedelta(hours=3),datetime.now()+timedelta(hours=4),True)
        assert data["data_available"] == False and isinstance(data["error"],ValueError)
    def test_actual_invalid_date_range3(self):
        # end > now 
        data = get_actual_production_percentage("DE",datetime.now()-timedelta(hours=3),datetime.now()+timedelta(hours=3),True)
        assert data["data_available"] == False and isinstance(data["error"],ValueError)


    def test_forecast_time_interval_60(self):
        data = get_forecast_percent_renewable("FR",datetime.now()-timedelta(hours=2),datetime.now()+timedelta(hours=5))
        assert data["time_interval"] == 60 and data["data_available"] == True
   

class TestActualDataFrame:
    @classmethod
    def setup_class(cls):
        """Fetch data once for all tests."""
        # Simulate fetching data from an API
        cls.country="DE"
        cls.start1 = datetime(2024,5,1)
        cls.end1 = datetime (2024,5,1,10,0,0)
        cls.row_count_check_60 = int(((cls.end1- cls.start1).total_seconds()/60)/60)
        cls.row_count_check_15 = cls.row_count_check_60*4
        # de1 is 15 min interval 
        # de2 is 60 min interval
        cls.de1 = get_actual_production_percentage(cls.country,cls.start1,cls.end1,False)["data"]
        cls.de2 = get_actual_production_percentage(cls.country,cls.start1,cls.end1,True)["data"]
    def test_dataframe_nonempty(self):
        """Test that the DataFrame is not empty."""
        assert not self.de1.empty, "The DataFrame should not be empty."
    def test_dataframe_nonempty1(self):
        """Test that the DataFrame is not empty."""
        assert not self.de2.empty, "The DataFrame should not be empty."
    def test_column_presence(self):
        """Test that required columns are present in the DataFrame."""
        required_columns = ["startTimeUTC", "total", "percentRenewable"]
        for col in required_columns:
            assert col in self.de1.columns
    def test_check_row_count_1(self):
        assert len(self.de2) == self.row_count_check_60
    def test_check_row_count_2(self):
        assert len(self.de1) == self.row_count_check_15
  