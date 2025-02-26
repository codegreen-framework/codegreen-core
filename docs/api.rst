codegreen_core API
===================


Package Organization
---------------------

.. image:: _static/modules.png
   :alt: modules
   :width: 400px  
   :align: center 


The package is divided into two main sub packages: `data`` and `tools`. (There is also an additional module, `utilities`, which provides helper methods that support other modules.)

The `data` sub package contains methods for fetching energy production data. This package relies on external data sources to retrieve this information, which is then processed to make it usable by other components of the package. For more details and a complete API , see the data module documentation.

The `tools` sub package provides a variety of tools, including:

- Carbon intensity calculator
- Carbon emission calculator
- Optimal time-shifting predictor
- Optimal location-shifting predictor


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
  


The core package contains 2 main module :  
- `data` : To fetch energy data for a country
- `tools` : To calculate various quantities like Optimal computation time, carbon intensity etc. 


`data` module
--------------

.. automodule:: codegreen_core.data
   :members:


`tools` module
---------------

.. automodule:: codegreen_core.tools
   :members:


.. automodule:: codegreen_core.tools.carbon_intensity
   :members:


.. automodule:: codegreen_core.tools.carbon_emission
   :members:


.. automodule:: codegreen_core.tools.loadshift_time
   :members:


.. automodule:: codegreen_core.tools.loadshift_location
   :members: