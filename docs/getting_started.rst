.. getting_started:


How to use codegreen
=====================

Welcome to the guide for getting started with the `codegreen` framework. 
There are four main ways to setup and use Codegreen based on your requirements. 
This document describes in detail the steps involved in each method. 

The four ways to use codegreen:

1. Using `codegreen.world` 
2. Setting up and using the `codegreen_core` package
3. Setting up your own web server 
4. Deploying the web service using the docker container


Using codegreen.world
----------------------

The simplest and fastest way to use Codegreen is through our web service.
This is ideal for beginners and new users looking for an easy way to reduce the carbon emissions of their computations.

1. Visit `www.codegreen.world <https://www.codegreen.world>`_
2. Create and account and log in
3. Generate an API token for your location and server details
4. Use the "Predict Optimal Time" form to get a time prediction for starting a computation in your selected location and server.


Additionally, we  provide `codegreen_client`, a Python package that can automatically start your Python scripts at the optimal time. Please refer to for installation and setup guide for more details. 


The web service also includes a dashboard where you can track how much carbon emission you have saved in each registered location.


Installing the `codegreen_core` package
-----------------------------------------

The `codegreen_core` Python package contains all the core functionalities of the Codegreen framework and can be used as a standalone tool.  
This is ideal for researchers and  developers who need to gather energy data for a country and perform calculations such as carbon intensity analysis.

**Step 1: Installation**

You can install the package using pip : 

.. code-block:: python

  pip install codegreen_core

Alternatively, you can clone the Git repository and install the package manually:  

.. code-block:: bash

  git clone https://github.com/bionetslab/codegreen-core.git
  pip install -e  . 

**Step 2 : Setting up the configuration file**

The package requires a configuration file where all settings are defined.  Create a new file named `.codegreencore.config`` in your root directory. This file will contain all the configurations required to run the package successfully. 

The next section describes how to set up the package based on your requirements.  


Configuring the `codegreen_core` package
-----------------------------------------

The codegreen_core package offers a wide range of functionalities and can be used in many applications.

Below is the template for the basic configuration 

.. code-block:: bash

  [codegreen]
    ENTSOE_token = <token>

This configuration allows you to fetch data online and use it.  
It is recommended to start with the basic setup and explore the available APIs before making advanced customizations.  

The API of the package is available :doc:`here <api>`

The table below summarizes all available configs : 

.. list-table:: Available Configuration Options
   :header-rows: 1
   :widths: 20 50 10 20

   * - Name
     - Description
     - Default 
     - Possible Values
   * - `ENTSOE_token`
     - The token required to fetch data from the ENTSO-E portal. Please follow the steps at https://transparency.entsoe.eu to create a free account and obtain an API token.
     - None
     - String
   * - `default_energy_mode`
     - To decide the source of energy forecasts to be used for making optimal time predictions
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

**Which data is used to predict optimal computation start time ?**

One of the main features of the `codegreen_core` package is the ability to calculate the optimal time for running a computation.  
This calculation depends on forecasts of hourly energy generation data from renewable and non-renewable sources or time series forecasts of the carbon intensity of future energy production.  

While this data is available for some countries, it is typically only provided for short durations (usually 24 hours or less), which limits the accuracy of optimal time predictions.  
To address this limitation, we have trained prediction models that generate time series forecasts for longer periods, allowing for more effective optimization.  

This setting is controlled by the `default_energy_mode` option. **By default**, the package uses publicly available energy data. To use the trained prediction models (if available for a specific country), set `default_energy_mode` to `local_prediction`.  

**How to enable caching of recent energy data?**

Certain tools, such as `predict_optimal_time`, rely on recent energy forecasts / predictions. Fetching the same data multiple times can be avoided by intelligently caching it and updating it at regular intervals.  
Energy data caching can be enabled by setting `enable_energy_caching` to `true`.  

Additionally, this requires a connection to Redis, which is specified using the `energy_redis_path` setting.  
When caching is enabled, the package first attempts to connect to Redis before storing or retrieving data.  

Once enabled, two types of data values are stored in the cache for each available country:  

1. **Hourly time series forecasts** for the upcoming hours.  
2. **Actual energy generation data** for the past 72 hours.


**How to download and use historical energy generation data offline?**



**How to re-train prediction models ?**
TODO


Setting up your own web server
--------------------------------



Deploying the web server using the docker image 
-----------------------------------------------
