``data`` Module
===============

This module provides methods to fetch energy production data for a specific country over a defined time period. 
One of the main challenges is the variability in the availability of data for different countries, which can impact the granularity and completeness of the data. 

.. automodule:: codegreen_core.data
   :members:


List of countries
-----------------

The list of countries for which data is available : 

.. country_table::

Fetching data from ENTSOE
-------------------------

ENTSO-E (https://www.entsoe.eu), the European Network of Transmission System Operators for Electricity, is an association that facilitates the cooperation of European transmission system operators (TSOs). Through its Transparency Portal, ENTSO-E provides real-time energy data for various countries across Europe, ensuring open access to this information. We utilize this data for countries within the European Union (EU).


.. automodule:: codegreen_core.data.entsoe
   :members:
   :show-inheritance:

