import pandas as pd
from ..utilities.metadata import get_country_energy_source, get_default_ci_value
from ..data import energy
from datetime import datetime

base_carbon_intensity_values = {
    "codecarbon": {
        "values": {
            "Coal": 995,
            "Petroleum": 816,
            "Natural Gas": 743,
            "Geothermal": 38,
            "Hydroelectricity": 26,
            "Nuclear": 29,
            "Solar": 48,
            "Wind": 26,
        },
        "source": "https://mlco2.github.io/codecarbon/methodology.html#carbon-intensity (values in kb/MWh)",
    },
    "ipcc_lifecycle_min": {
        "values": {
            "Coal": 740,
            "Natural Gas": 410,
            "Biomass": 375,
            "Geothermal": 6,
            "Hydroelectricity": 1,
            "Nuclear": 3.7,
            "Solar": 17.6,
            "Wind": 7.5,
        },
        "source": "https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_annex-iii.pdf#page=7",
    },
    "ipcc_lifecycle_mean": {
        "values": {
            "Coal": 820,
            "Biomass": 485,
            "Natural Gas": 490,
            "Geothermal": 38,
            "Hydroelectricity": 24,
            "Nuclear": 12,
            "Solar": 38.6,
            "Wind": 11.5,
        },
        "source": "",
    },
    "ipcc_lifecycle_max": {
        "values": {
            "Coal": 910,
            "Biomass": 655,
            "Natural Gas": 650,
            "Geothermal": 79,
            "Hydroelectricity": 2200,
            "Nuclear": 110,
            "Solar": 101,
            "Wind": 45.5,
        },
        "source": "",
    },
    "eu_comm": {
        "values": {
            "Coal": 970,  # sold fuels
            "Petroleum": 790,  # oil
            "Biomass": 65,
            "Natural Gas": 425,
            "Geothermal": 38,
            "Hydroelectricity": 19,
            "Nuclear": 24,
            "Solar": 40,
            "Wind": 11,
        },
        "source": "N. Scarlat, M. Prussi, and M. Padella, 'Quantification of the carbon intensity of electricity produced and used in Europe', Applied Energy, vol. 305, p. 117901, Jan. 2022, doi: 10.1016/j.apenergy.2021.117901.",
    },
}


def _calculate_weighted_sum(base, weight):
    """
    Assuming weight are in percentage
    weignt and base are dictionaries with the same keys
    """
    return round(
        (
            base.get("Coal", 0) * weight.get("Coal_per", 0)
            + base.get("Petroleum", 0) * weight.get("Petroleum_per", 0)
            + base.get("Biomass", 0) * weight.get("Biomass_per", 0)
            + base.get("Natural Gas", 0) * weight.get("Natural Gas_per", 0)
            + base.get("Geothermal", 0) * weight.get("Geothermal_per", 0)
            + base.get("Hydroelectricity", 0) * weight.get("Hydroelectricity_per", 0)
            + base.get("Nuclear", 0) * weight.get("Nuclear_per", 0)
            + base.get("Solar", 0) * weight.get("Solar_per", 0)
            + base.get("Wind", 0) * weight.get("Wind_per", 0)
        )
        / 100,
        2,
    )


def _calculate_ci_from_energy_mix(energy_mix):
    """
    To calculate multiple CI values for a data frame row (for the `apply` method)
    """
    methods = [
        "codecarbon",
        "ipcc_lifecycle_min",
        "ipcc_lifecycle_mean",
        "ipcc_lifecycle_mean",
        "ipcc_lifecycle_max",
        "eu_comm",
    ]
    values = {}
    for m in methods:
        sum = _calculate_weighted_sum(
            base_carbon_intensity_values[m]["values"], energy_mix
        )
        values[str("ci_" + m)] = sum
    return values


def compute_ci(country: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
    """
    Computes carbon intensity data for a given country and time period.

    If energy data is available, the carbon intensity is calculated from actual energy data for the specified  time range.
    If energy data is not available for the country, a default carbon intensity value is used instead.
    The default CI values for all countries are stored in utilities/ci_default_values.csv.

    """
    if not isinstance(country, str):
        raise ValueError("Invalid country")

    if not isinstance(start_time, datetime):
        raise ValueError("Invalid start_time")

    if not isinstance(end_time, datetime):
        raise ValueError("Invalid end_time")

    e_source = get_country_energy_source(country)
    if e_source == "ENTSOE":
        data = energy(country, start_time, end_time)
        energy_data = data["data"]
        ci_values = compute_ci_from_energy(energy_data)
        return ci_values
    else:
        time_series = pd.date_range(start=start_time, end=end_time, freq="H")
        df = pd.DataFrame(time_series, columns=["startTimeUTC"])
        df["ci_default"] = get_default_ci_value(country)
        return df


def compute_ci_from_energy(
    energy_data: pd.DataFrame,
    default_method="ci_ipcc_lifecycle_mean",
    base_values: dict = None,
) -> pd.DataFrame:
    """
    Given the energy time series, computes the carbon intensity for each row.
    You can choose the base value from several sources available or use your own base values.

    :param energy_data: A pandas DataFrame that must include the following columns, representing
                        the percentage of energy generated from each source:

        - `Coal_per` (float): Percentage of energy generated from coal.
        - `Petroleum_per` (float): Percentage of energy generated from petroleum.
        - `Biomass_per` (float): Percentage of energy generated from biomass.
        - `Natural Gas_per` (float): Percentage of energy generated from natural gas.
        - `Geothermal_per` (float): Percentage of energy generated from geothermal sources.
        - `Hydroelectricity_per` (float): Percentage of energy generated from hydroelectric sources.
        - `Nuclear_per` (float): Percentage of energy generated from nuclear sources.
        - `Solar_per` (float): Percentage of energy generated from solar sources.
        - `Wind_per` (float): Percentage of energy generated from wind sources.

    :param default_method: This parameter allows you to choose the base values for each energy source.
                          By default, the IPCC lifecycle mean values are used. Available options include:

        - `codecarbon` (Ref [6])
        - `ipcc_lifecycle_min` (Ref [5])
        - `ipcc_lifecycle_mean` (default)
        - `ipcc_lifecycle_max`
        - `eu_comm` (Ref [4])

    :param base_values(optional): A dictionary of custom base carbon intensity values for energy sources.
                        Must include the following keys:

        - `Coal` (float): Base carbon intensity value for coal.
        - `Petroleum` (float): Base carbon intensity value for petroleum.
        - `Biomass` (float): Base carbon intensity value for biomass.
        - `Natural Gas` (float): Base carbon intensity value for natural gas.
        - `Geothermal` (float): Base carbon intensity value for geothermal energy.
        - `Hydroelectricity` (float): Base carbon intensity value for hydroelectricity.
        - `Nuclear` (float): Base carbon intensity value for nuclear energy.
        - `Solar` (float): Base carbon intensity value for solar energy.
        - `Wind` (float): Base carbon intensity value for wind energy.
    """

    if not isinstance(energy_data, pd.DataFrame):
        raise ValueError("Invalid energy data.")

    if not isinstance(default_method, str):
        raise ValueError("Invalid default_method")

    if base_values:
        energy_data["ci_default"] = energy_data.apply(
            lambda row: _calculate_weighted_sum(row.to_dict(), base_values), axis=1
        )
        return energy_data
    else:
        ci_values = energy_data.apply(
            lambda row: _calculate_ci_from_energy_mix(row.to_dict()), axis=1
        )
        ci = pd.DataFrame(ci_values.tolist())
        ci = pd.concat([ci, energy_data], axis=1)
        ci["ci_default"] = ci[default_method]
        return ci
