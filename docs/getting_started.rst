.. getting_started:


Getting Started
===============

Welcome to the guide for getting started with `codegreen_core`. This document provides installation instructions and the initial steps required to get the package up and running. It also outlines the package structure, which will help you choose the appropriate tools based on your needs.

Installation
-------------

Using pip : 

.. code-block:: python

  pip install codegreen_core

You can also use clone the git repository and install the package :

.. code-block:: bash

  git clone https://github.com/bionetslab/codegreen-core.git
  pip install -e  . 


Setup 
-------

After you have successfully installed the package, the next step is to create a configuration file. 
- Create a new file `.codegreencore.config` in your root directory.
- This file will contains all the configruations required to run the packages successfully.
- Here is a template for the config file :

After successfully installing the package, the next step is to create a configuration file:

- Create a new file named `.codegreencore.config`` in your root directory.
- This file will contain all the configurations required to run the package successfully.
- Below is a template for the configuration file:"

.. code-block:: bash

  [codegreen]
    ENTSOE_token = <token>
    enable_energy_caching = false
    energy_redis_path = <redis_path>


Description of the fields in configuration file:

- `ENTSOE_token``: The token required to fetch data from the ENTSO-E portal. Please follow the steps at https://transparency.entsoe.eu to create a free account and obtain an API token.
- `enable_energy_caching``: (boolean) Indicates whether energy data used for optimal time predictions should be cached.
- `energy_redis_path``: The path to the Redis server where energy data will be stored. This field is required if caching is enabled using the above option.


Package Organization
---------------------

.. image:: _static/modules.png
   :alt: modules
   :width: 400px  
   :align: center 


The package is divided into two main modules: `data`` and `tools`. (There is also an additional module, `utilities`, which provides helper methods that support other modules.)

The `data`` module contains methods for fetching energy production data. This package relies on external data sources to retrieve this information, which is then processed to make it usable by other components of the package. For more details and a complete API , see the data module documentation.

The `tools`` module provides a variety of tools, including:

- Carbon intensity calculator
- Carbon emission calculator
- Optimal time-shifting predictor
- Optimal location-shifting predictor

For more information, refer to the `tools` module documentation.


Example : Calculating optimal time for a computational task 
-------------------------------------------------------------
Assuming all the above steps are done, you can now calculate the optimal starting time for a computations. 

.. code-block:: python
  
  from datetime import datetime,timedelta 
  from codegreen_core.tools.loadshift_time import predict_now

  country_code = "DK"
  est_runtime_hour = 10
  est_runtime_min = 0
  now = datetime.now()
  hard_finish_date = now + timedelta(days=1)
  criteria = "percent_renewable"
  per_renewable = 50 

  time = predict_now(country_code,
                    est_runtime_hour,
                    est_runtime_min,
                    hard_finish_date,
                    criteria,
                    per_renewable)
  # (1728640800.0, <Message.OPTIMAL_TIME: 'OPTIMAL_TIME'>, 76.9090909090909)

  
