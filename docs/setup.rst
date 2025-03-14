Setting up the package
=======================

The package requires a configuration file where all settings are defined.  
Create a new file named `.codegreencore.config` in your root directory or project root. 
This file will contain all the configurations required to run the package successfully. 

This section describes how to set up the package. 

Configuration options available
--------------------------------

The table below summarizes all available configs : 

.. list-table:: Available Configuration Options
   :header-rows: 1
   :widths: 20 50 10 20

   * - Name
     - Description
     - Default 
     - Possible Values
   * - `ENTSOE_token`
     - The token required to fetch data from the ENTSO-E portal. Follow the steps at https://transparency.entsoe.eu to create a free account and obtain an API token.
     - None
     - String
   * - `default_energy_mode`
     - Defines the source of energy forecasts to be used for making optimal time predictions
     - public_data
     - public_data / local_prediction
   * - `enable_energy_caching`
     - Enables or disables local caching of energy data
     - false
     - true/false
   * - `energy_redis_path`
     - Path to Redis instance for caching
     - None
     - String (Redis URL, redis://localhost:6379 )
   * - `enable_offline_energy_generation`
     - To enable storing and periodic update of historical energy in csv files
     - false
     - true/false
   * - `offline_data_dir_path`
     - Path to the folder where historical energy data will be stored
     - None
     - String 
   * - `offline_data_start_date`
     - The start date from which historical energy data must be downloaded and stored
     - None
     - String (`YYYY-mm-dd` format) 



Basic Configuration 
--------------------
Below is the template for the basic configuration 

.. code-block:: bash

  [codegreen]
    ENTSOE_token = token-here

This configuration will allow you to fetch data online and use it.  
It is recommended to start with the basic setup and explore the available APIs before making advanced customizations.  
Please refer to the above table for details about the configuration options. 

Using predication models for energy forecasts 
-----------------------------------------------

By default we use energy data that is available from public sources. While this data is very useful, it may sometimes by inadequate to make better decisions. 

The codegreen_core package includes built in predication models that generate energy forecasts. One advantage of our models is that we have trained different models for each country. They also provide forecasts for more that 24 hours in the future. 

To enable the use  prediction model where the package requires energy forecast data, set the `default_energy_mode` to `local_prediction`

Note : This feature is still under development and models may not be available for all countries. If a model is unavailable, the system will fall back to using publicly available energy data.

Setting up energy data caching
---------------------------

Some methods in the tools module rely of energy data provided by the data module. 
By default, every time a method is called, data is fetched from online sources. 
To avoid repeatedly fetching the same data, the package allows storing recent energy data in a Redis cache.

**To enable this feature**  

- Set `enable_energy_caching` to `true` 
- Provide the path to Redis cache in `energy_redis_path` configuration
- Ensure that the Redis cache is running ; otherwise an exception will be thrown.

**How caching works** 

Forecast data is synced in the cache whenever a method request data. The first request may take some time as it triggers the cache sync process.

To sync energy generation data run the following piece of code (either manually or via a CRON Job):

.. code-block:: python

  from codegreen_core.data import sync_offline_data
  sync_offline_data(cache=True)

Cached data includes : 

- Recent energy forecasts for all available countries (up to 24 hours ahead)
- Recent energy production data ( last 72 hours up until 5 hours before the last sync time since different countries have different upload schedules) 
- Recent forecast data generated by the predication models  (up to 72 hours ahead in time, if that option is enabled)


Setting offline storage of energy data
---------------------------------------

If you work with energy generation data for longer periods , you have the option to store it offline for quick access. 
The package  supports long term storage of generation data only.

**To enable this feature**

- Set `enable_offline_energy_generation` to `true`
- Provide a folder path in `offline_data_dir_path` where data will be stored. 
- Specify the start date from which  data should be stored using  `offline_data_start_date`  configuration in `YYYY-MM-DD` format. 

After configuring these settings , manually start the initial sync using following code :

.. code-block:: python

  from codegreen_core.data import sync_offline_data
  sync_offline_data(file=True)

**How Offline Storage Works**

This  setup  will create initial files for each available country. 
Each  country will have two files : A CSV file with the data and JSON containing metadata for easier syncing. 
Syncing may take time depending on the selected start date.

If you want to back fill data from an earlier time, modify `offline_data_start_date` 


**Keeping offline storage up-to-date**

Date files needs to be updated with latest data regularly. You can update them manually (by running the above command) or set up a CRON job to call the sync method periodically 



**Using Preprocessed Data for Faster Setup**

Since initial setup can take a long time, you can also download preprocessed data from our Github repo and use it as a starting point. 

Steps : 

- Download the zip file
- Extract the folder and place the data in the desired location 
- Update the config file if required (`offline_data_dir_path` and `offline_data_start_date`)
- Run the sync code to ensure the files are updated with the latest available data.

Available preprocessed data: 

- Data since Jan 1, 2025 : Link to the zip file   https://github.com/codegreen-framework/energy-data/raw/refs/heads/main/2025.zip
- Data since Jan 1, 2020 : Under development
