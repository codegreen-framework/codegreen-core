import pytest
from codegreen_core.utilities.message import CodegreenDataError, Message
from datetime import datetime, timezone, timedelta
import codegreen_core.tools.loadshift_time as ts
import pandas as pd
import pytz


# Optimal time predications
class TestOptimalTimeCore:

    # some common data for testing
    dummy_energy_data_1 = pd.DataFrame(
        {
            "startTimeUTC": [1, 2, 3],
            "totalRenewable": [1, 2, 3],
            "percent_renewable": [1, 2, 3],
        }
    )
    request_time_1 = datetime(2024, 1, 5, 0, 0)
    request_time_2 = datetime(2024, 1, 10, 0, 0)
    hard_finish_time_1 = datetime(2024, 1, 5, 15, 0)
    hard_finish_time_2 = datetime(2024, 1, 15, 15, 0)

    def test_energy_data_blank(self):
        """test if no energy data is provided, the result defaults to the request time"""
        timestamp, message, average_percent_renewable = ts.predict_optimal_time(
            None, 1, 1, self.hard_finish_time_1, self.request_time_1
        )
        # print(timestamp, message, average_percent_renewable)
        assert timestamp == int(self.request_time_1.timestamp())
        assert message == Message.NO_DATA
        assert average_percent_renewable == 0

    def test_neg_hour(self):
        """test if negative hour value is provided, the result defaults to the request time"""
        timestamp, message, average_percent_renewable = ts.predict_optimal_time(
            self.dummy_energy_data_1,
            -1,
            1,
            self.hard_finish_time_1,
            self.request_time_1
        )
        assert timestamp == int(self.request_time_1.timestamp())
        assert message == Message.INVALID_DATA
        assert average_percent_renewable == 0

    def test_zero_hour(self):
        """test if hour value is 0, the result defaults to the request time"""
        timestamp, message, average_percent_renewable = ts.predict_optimal_time(
            self.dummy_energy_data_1,
            0,
            1,
            self.hard_finish_time_1,
            self.request_time_1
        )
        assert timestamp == int(self.request_time_1.timestamp())
        assert message == Message.INVALID_DATA
        assert average_percent_renewable == 0

    def test_neg_min(self):
        """test if negative hour value is provided, the result defaults to the request time"""
        timestamp, message, average_percent_renewable = ts.predict_optimal_time(
            self.dummy_energy_data_1,
            1,
            -1,
            self.hard_finish_time_1,
            self.request_time_1
        )
        assert timestamp == int(self.request_time_1.timestamp())
        assert message == Message.INVALID_DATA
        assert average_percent_renewable == 0

    def test_zero_per_renew(self):
        """test if 0 % renewable , the result defaults to the request time"""
        dummy_energy_data_2 = pd.DataFrame(
        {
            "startTimeUTC": [1, 2, 3],
            "totalRenewable": [1, 2, 3],
            "percent_renewable": [0, 0, 0],
        }
        )
        timestamp, message, average_percent_renewable = ts.predict_optimal_time(
            dummy_energy_data_2,
            1,
            0,
            self.hard_finish_time_1,
            self.request_time_1,
        )
        assert timestamp == int(self.request_time_1.timestamp())
        assert message == Message.NEGATIVE_PERCENT_RENEWABLE
        assert average_percent_renewable == 0

    def test_neg_per_renew(self):
        """test if negative -ve % renew is provided, the result defaults to the request time"""
        dummy_energy_data_3 = pd.DataFrame(
            {
                "startTimeUTC": [1, 2, 3],
                "totalRenewable": [1, 2, 3],
                "percent_renewable": [-1, -4, -5],
            }
        )
        timestamp, message, average_percent_renewable = ts.predict_optimal_time(
            dummy_energy_data_3,
            1,
            0,
            self.hard_finish_time_1,
            self.request_time_1
        )
        assert timestamp == int(self.request_time_1.timestamp())
        assert message == Message.NEGATIVE_PERCENT_RENEWABLE
        # assert average_percent_renewable == 0

    def test_less_energy_data(self):
        """to test if the request time + running time > hard finish , then return the request time"""
        timestamp, message, average_percent_renewable = ts.predict_optimal_time(
            self.dummy_energy_data_1,
            20,
            0,
            self.hard_finish_time_1,
            self.request_time_1
        )
        assert timestamp == int(self.request_time_1.timestamp())
        assert message == Message.RUNTIME_LONGER_THAN_DEADLINE_ALLOWS

    def test_if_incorrect_data_provided(self):
        """this is to test if  energy data provided does not contain the data for the request time"""
        data = pd.read_csv("tests/data/DE_forecast1.csv")
        timestamp, message, average_percent_renewable = ts.predict_optimal_time(
            data, 20, 0, self.hard_finish_time_2, self.request_time_2
        )
        assert timestamp == int(self.request_time_2.timestamp())
        assert message == Message.NO_DATA

    def test_multiple(self):
        data = pd.read_csv("tests/data/DE_forecast1.csv")
        hard_finish_time = datetime(2024, 1, 7, 0, 0)
        request_time = datetime(2024, 1, 5, 0, 0)
        cases = [
            {
                "hd": hard_finish_time,
                "rd": request_time,
                "h": 1,
                "p": 30,
                "start": 1704412800,
            },
            {
                "hd": hard_finish_time,
                "rd": request_time,
                "h": 2,
                "p": 30,
                "start": 1704412800,
            },
            {
                "hd": hard_finish_time,
                "rd": request_time,
                "h": 10,
                "p": 30,
                "start": 1704412800,
            },
            {
                "hd": hard_finish_time,
                "rd": request_time,
                "h": 20,
                "p": 30,
                "start": 1704412800,
            },
            {
                "hd": hard_finish_time,
                "rd": request_time,
                "h": 2,
                "p": 40,
                "start": 1704420000,
            },
            {
                "hd": hard_finish_time,
                "rd": request_time,
                "h": 5,
                "p": 40,
                "start": 1704420000,
            },
            {
                "hd": hard_finish_time,
                "rd": request_time,
                "h": 5,
                "p": 42,
                "start": 1704423600,
            },
            {
                "hd": hard_finish_time,
                "rd": request_time,
                "h": 1,
                "p": 45,
                "start": 1704445200,  # percent renewable  prioritized over the start time
            },
            {
                "hd": hard_finish_time,
                "rd": request_time,
                "h": 5,
                "p": 45,
                "start": 1704445200,
            },
            {
                "hd": hard_finish_time,
                "rd": request_time,
                "h": 5,
                "p": 50,
                "start": 1704452400,  # why 1704427200
            },
            {
                "hd": hard_finish_time,
                "rd": request_time,
                "h": 10,
                "p": 50,
                "start": 1704452400,
            },
            {
                "hd": hard_finish_time,
                "rd": request_time,
                "h": 1,
                "p": 50,
                "start": 1704445200,
            },
            # {
            #  "hd":hard_finish_time,
            #  "rd":request_time,
            #  "h":10,
            #  "p":60,
            #  "start":1704412800 # no match , just start now
            #  }
        ]
        assert 1 == 1

    def test_data_validation_country(self):
        timestamp1 = int(datetime.now(timezone.utc).timestamp())
        timestamp, message, average_percent_renewable = ts.predict_now(
            "UFO", 10, 0, datetime(2024, 9, 7), "percent_renewable"
        )
        print(timestamp1, timestamp, message)
        assert timestamp - timestamp1 <= 10
        assert message == Message.ENERGY_DATA_FETCHING_ERROR

    # def test_all_country_test(self):
    #   test_cases = pd.read_csv("./data/test_cases_time.csv")
    #   data = pd.read_csv("./data/prediction_testing_data.csv")
    #   for index, row in test_cases.iterrows():
    #     edata_filter = data["file_id"] == row["country"]
    #     energy_data = data[edata_filter].copy()
    #     start = datetime.strptime(row["start_time"], '%Y-%m-%d %H:%M:%S')
    #     end = (start + timedelta(hours=row["hard_deadline_hour"]))
    #     a,b,c = ts.predict_optimal_time(energy_data,row["runtime_hour"],row["runtime_min"],row["percent_renewable"],end,start)
    #     print(a,b,c)
    #     assert int(a) ==  row["expected_timestamp"]

    # for case in cases:
    #   #print(case)
    #   print(str(case["p"])+"%,"+str(case["h"])+" h")
    #   timestamp, message, average_percent_renewable = ts.predict_optimal_time(data,case["h"],0,case["p"],case["hd"],case["rd"])
    #   print(timestamp)
    #   assert timestamp == case["start"]


# test if request time is none current time is being used
def test_all_country():
    test_cases = pd.read_csv("tests/data/test_cases_time.csv")
    data = pd.read_csv("tests/data/prediction_testing_data.csv")
    for _, row in test_cases.iterrows():
        print(row)
        edata_filter = data["file_id"] == row["country"]
        energy_data = data[edata_filter].copy()

        start_utc = datetime.strptime(row["start_time"], "%Y-%m-%d %H:%M:%S")
        start_utc = pytz.UTC.localize(start_utc)
        start = start_utc.astimezone(pytz.timezone("Europe/Berlin"))
        end = start + timedelta(hours=row["hard_deadline_hour"])

        a, b, c = ts.predict_optimal_time(
            energy_data,
            row["runtime_hour"],
            row["runtime_min"],
            end,
            start,
        )
        print(a, b, c)
        assert int(a) == row["expected_timestamp"]
        print("====")


# test_all_country()


# def data_validation_country():
#     timestamp1  = int(datetime.now(timezone.utc).timestamp())
#     timestamp, message, average_percent_renewable = ts.predict_now("DE",10,0,datetime(2024,9,7),"percent_renewable",30)
#     print(timestamp1,timestamp, message)
#     #assert timestamp - timestamp1 <= 10
#     #assert message == Message.ENERGY_DATA_FETCHING_ERROR

# data_validation_country()
# a,b,c = ts.predict_now("DE",2,30,datetime.fromtimestamp(1726092000),percent_renewable=50)
