The core business logic of codegreen

# Installation 

- Install the package
- Create a config file : `.codegreencore.config`
- Initial config file:
  ```
  [codegreen]
  ENTSOE_token = 1234
  CO2_SIGNAL_TOKEN =  1234
  ```
  - To get ENTSOE token from the [transparency platform](https://transparency.entsoe.eu/dashboard/show)

# API (selected methods)

## `coregreen_core.data` 

- `energy(country,start_time,end_time,type)`
  - This method returns energy data for the given country for the selected time period. Returns `None` if  no data source is available. 
  - Params : 
    - `country` : the valid 2 letter country code
    - `start_time` : datetime object (will be rounded to nearest hour)
    - `end_time` :  datetime object (will be rounded to the nearest hour)
    - `type` : the type of data to be fetched : `historical` or `forecast`
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
