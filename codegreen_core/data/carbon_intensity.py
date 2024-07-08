import pandas as pd
from .entsoe import get_actual_production_percentage, convert_date_to_entsoe_format
from .metadata import get_country_energy_source, get_default_ci_value

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
        "source": "https://mlco2.github.io/codecarbon/methodology.html#carbon-intensity (values in kb/MWh)"
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
            "Wind": 7.5
        },
        "source": "https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_annex-iii.pdf#page=7"
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
            "Wind": 11.5
        },
        "source": ""
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
            "Wind": 45.5
        },
        "source": ""
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
            "Wind": 11
        },
        "source": "N. Scarlat, M. Prussi, and M. Padella, ‘Quantification of the carbon intensity of electricity produced and used in Europe’, Applied Energy, vol. 305, p. 117901, Jan. 2022, doi: 10.1016/j.apenergy.2021.117901."
    }
}

def calculate_weighted_sum(base,weight):
    """
    Assuming weight are in percentage
    """
    return round((
              base.get("Coal",0)*weight.get("Coal_per",0) 
            + base.get("Petroleum",0)*weight.get("Petroleum_per",0)
            + base.get("Biomass",0)*weight.get("Biomass_per",0)
            + base.get("Natural Gas",0)*weight.get("Natural Gas_per",0)
            + base.get("Geothermal",0)*weight.get("Geothermal_per",0)
            + base.get("Hydroelectricity",0)*weight.get("Hydroelectricity_per",0)
            + base.get("Nuclear",0)*weight.get("Nuclear_per",0)
            + base.get("Solar",0)*weight.get("Solar_per",0)
            + base.get("Wind",0)*weight.get("Wind_per",0))/100,2)

def calculate_carbon_intensity(energy_mix):
    methods = ["codecarbon","ipcc_lifecycle_min","ipcc_lifecycle_mean","ipcc_lifecycle_mean","ipcc_lifecycle_max","eu_comm"]
    values = {}
    for m in methods:
        sum = calculate_weighted_sum(base_carbon_intensity_values[m]["values"],energy_mix)
        values[str("ci_"+m)] = sum
    return values

"""
Note : 1 kg = 1000 grams and 1MWh = 1000 kWh. This means, 1 kg/MWh = 1 kg/(kWh * 1000 )  = 1000 g/ (kWH * 1000) ....(both 1000 cancel each other out) => 1kg/MWh = 1g/kWh         
IPCC values
| type        | average of                                                  | min  | mean | max  |
|-------------|-------------------------------------------------------------|------|------|------|
| coal        | Coal—PC                                                     | 740  | 820  | 910  |
| natural gas | Gas—Combined Cycle                                          | 410  | 490  | 650  |
| biogas      | Biomass—cofiring,Biomass—dedicated                          | 375  | 485  | 655  |
| geothermal  | Geothermal                                                  | 6    | 38   | 79   |
| hydropower  | Hydropower                                                  | 1    | 24   | 2200 |
| nuclear     | Nuclear                                                     | 3.7  | 12   | 110  |
| solar       | Concentrated Solar Power, Solar PV—rooftop,Solar PV—utility | 17.6 | 38.6 | 101  |
| wind        | Wind onshore, Wind offshore                                 | 7.5  | 11.5 | 45.5 |
https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_annex-iii.pdf#page=7
"""
