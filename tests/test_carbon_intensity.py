import pytest
from datetime import datetime
import codegreen_core.tools.carbon_intensity as ci


class TestCarbonIntensity:
    def test_if_incorrect_data_provided1(self):
        with pytest.raises(ValueError):
            ci.compute_ci("DE", datetime(2024, 1, 2), "2024,1,1")

    def test_if_incorrect_data_provided2(self):
        with pytest.raises(ValueError):
            ci.compute_ci("DE", 123, datetime(2024, 1, 2))

    def test_if_incorrect_data_provided3(self):
        with pytest.raises(ValueError):
            ci.compute_ci(123, datetime(2024, 1, 2), datetime(2024, 1, 3))

    def test_if_incorrect_data_provided4(self):
        with pytest.raises(ValueError):
            ci.compute_ci_from_energy("DE", datetime(2024, 1, 2), "2024,1,1")

    def test_if_incorrect_data_provided5(self):
        with pytest.raises(ValueError):
            ci.compute_ci_from_energy("DE", 123, datetime(2024, 1, 2))

    def test_if_incorrect_data_provided6(self):
        with pytest.raises(ValueError):
            ci.compute_ci_from_energy(123, datetime(2024, 1, 2), datetime(2024, 1, 3))
