import json
from pathlib import Path
import pandas as pd
from codegreen_core.utilities.metadata import get_country_energy_source, get_default_ci_value
from codegreen_core.data import energy
from datetime import datetime

# constant values
with open(Path(__file__).parent / "base_carbon_intensity_values.json", "r") as f:
    base_carbon_intensity_values = json.load(f)


def _calculate_weighted_sum(base: dict, weight: dict) -> float:
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


def _calculate_ci_from_energy_mix(energy_mix: dict) -> dict[str, float]:
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


def compute_ci(
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
        raise TypeError("Invalid energy data.")

    if not isinstance(default_method, str):
        raise TypeError("Invalid default_method")

    if base_values:
        energy_data["ci_default"] = energy_data.apply(
            lambda row: _calculate_weighted_sum(row.to_dict(), base_values), axis=1
        )
        return energy_data
    else:
        ci_values = energy_data.apply(
            lambda row: _calculate_ci_from_energy_mix(row.to_dict()), axis=1
        )
        ci = pd.DataFrame(ci_values.tolist(), index=ci_values.index)
        ci = pd.concat([ci, energy_data], axis=1)
        ci["ci_default"] = ci[default_method]
        return ci
