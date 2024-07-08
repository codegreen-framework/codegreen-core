The core business logic of codegreen

# Installation 

- Install the package 
  - Using github : `git clone https://github.com/bionetslab/codegreen-core.git`, then `pip install -e .`
- Create a config file (either in the root of the project or the user's root directory): `.codegreencore.config`
- Initial config file:
  ```
  [codegreen]
  ENTSOE_token = 1234
  ```
  - Get ENTSOE token from the [transparency platform](https://transparency.entsoe.eu/dashboard/show)

# Dev related

- Each sub package has a `main.py` where the main methods  are defined 

# API (selected methods)

## `coregreen_core.data` 

- `energy(country,start_time,end_time,type)`
  - This method returns an hourly times series of the energy production mix for the given country over the selected time period. It returns `None` if  no data source is available. 
  - Params : 
    - `country` : the valid 2 letter country code
    - `start_time` : datetime object (will be rounded to nearest hour)
    - `end_time` :  datetime object (will be rounded to the nearest hour)
    - `type` : the type of data to be fetched : `historical` or `forecast`
  - List of countries currently supported is available [here](./codegreen_core/data/country_list.json)
  - Examples :
  ```
  from codegreen_core.data  import energy

  data1 = energy("DE",datetime(2020,1,1),datetime(2020,1,1)) 
  # returns historical energy data by default 

  data2 = energy("ES",datetime(2024,1,1),datetime(2024,1,2),type="forecast")
  ```

  - Output : Pandas dataframe. Data fetched from ENTSOE looks like the following : 
  ```
  startTimeUTC                        object

  Biomass                            float64
  Fossil Hard coal                   float64
  Geothermal                         float64
  Nuclear                            float64
  Other                              float64
  Solar                              float64
  Wind Offshore                      float64
  .... other energy sources 

  # common fields for all countries 
  renewableTotal                     float64
  renewableTotalWS                   float64 # total energy produced from wind and solar energy sources 
  nonRenewableTotal                  float64
  total                              float64

  percentRenewable                     int64
  percentRenewableWS                   int64

  Wind_per                             int64
  Solar_per                            int64
  Nuclear_per                          int64
  Hydroelectricity_per                 int64
  Geothermal_per                       int64
  Natural Gas_per                      int64
  Petroleum_per                        int64
  Coal_per                             int64
  Biomass_per                          int64
  ```
- `carbon_intensity(country,start_time,end_time)`
  - Returns the time series of the carbon intensity values for the selected country over the selected duration 
  - The carbon intensity values are calculated by taking a weighted sum of base intensity value per production type. The weights are the percentage of the energy mix of each production type during that time window. 
  - There are multiple methodologies based on the base values used. Currently, following variants are supported :
    - `ci_codecarbon` : Based on the base values used by the Codecarbon [Link](https://mlco2.github.io/codecarbon/methodology.html#carbon-intensity)
    - `ci_ipcc_lifecycle_min`,`ipcc_lifecycle_mean`,`ipcc_lifecycle_max` : Lifecycle Emissions of electricity supply technologies from  Schlömer S., T. Bruckner, L. Fulton, E. Hertwich, A. McKinnon, D. Perczyk, J. Roy, R. Schaeffer, R. Sims, P. Smith, and R. Wiser, 2014: Annex III: Technology-specific cost and performance parameters. In: Climate Change 2014: Mitigation of Climate Change. Contribution of Working Group III to the Fifth Assessment Report of the Intergovernmental Panel on Climate  Change . [Link](https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_annex-iii.pdf#page=7) 
    - `ci_eu_commission`: Based on N. Scarlat, M. Prussi, and M. Padella, ‘Quantification of the carbon intensity of electricity produced and used in Europe’, Applied Energy, vol. 305, p. 117901, Jan. 2022, doi: 10.1016/j.apenergy.2021.117901 [Link](https://doi.org/10.1016/j.apenergy.2021.117901)
  - If the energy mix percentage is not available, the global average value for that country is returned 

## `codegreen_core.loadshift`
- `predict_optimal_time()` : 
  - Returns the optimal time to start the job based on the inputs provided
  - Params:
  - The process : 
  - Examples :
- `predict_optimal_location()`
  - Returns the optimal location where the job can be run to reduce it's carbon footprint
- `calculate_carbon_footprint_job()`
  - To calculate the carbon footprint of a job based on the where it was run and what it was run on. 
- `calculate_emissions_saved()`
