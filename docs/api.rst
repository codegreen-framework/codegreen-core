codegreen_core API
===================

The core package contains 2 main module :  

- `data` : To fetch energy data for a country.
- `tools` : To calculate various quantities like Optimal computation time, carbon intensity etc. 


`data` module
--------------

.. automodule:: codegreen_core.data
   :members:


`tools` module
---------------

  Methods vary depending on the type of input (e.g, country name vs energy data) and the output (e.g single value vs time series DataFrame). Most tools  depend on the data from the `data` sub package.
  As a convention, methods that primarily accept DataFrame as an input (along with other parameters) and return  a DataFrame are prefixed with `_df`. 

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