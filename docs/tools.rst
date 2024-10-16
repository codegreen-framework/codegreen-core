``tools`` Module
=================

This subpackage  provides tools and methods for tasks like calculating the carbon intensity of energy production and calculating the emissions produced due to a computation. 

Each tool is implemented in a separate module and must be imported individually (See below). 

..
  Methods vary depending on the type of input (e.g, country name vs energy data) and the output (e.g single value vs time series DataFrame). Most tools  depend on the data from the `data` sub package.
  As a convention, methods that primarily accept DataFrame as an input (along with other parameters) and return  a DataFrame are prefixed with `_df`. 


.. automodule:: codegreen_core.tools
   :members:

Carbon Intensity of Energy
---------------------------

Carbon intensity refers to the amount of greenhouse gases emitted per unit of electricity generated. 
It is typically measured in grams of CO₂ equivalents per kilowatt-hour (gCO2e/kWh). 

Different types of energy production, such as fossil fuels, renewable, and nuclear power, have varying carbon intensity values.
Carbon intensity of an energy mix is the weighted sum of the base carbon intensity values of each energy source based on proportion of each source. 
The carbon intensity of the energy powering a system significantly impacts the overall carbon emissions of computational tasks.

..
   Note : 1 kg = 1000 grams and 1MWh = 1000 kWh. This means, 1 kg/MWh = 1 kg/(kWh * 1000 )  = 1000 g/ (kWH * 1000) ....(both 1000 cancel each other out) => 1kg/MWh = 1g/kWh         

The table below shows the base carbon intensity values of various electricity production sources. These values are adapted from [5]

 ============= ============================================================= ======  
  Type          Average of                                                    mean     
 ============= ============================================================= ====== 
  coal          Coal—PC                                                       820       
  natural gas   Gas—Combined Cycle                                            490    
  biogas        Biomass—co-firing,Biomass—dedicated                            485      
  geothermal    Geothermal                                                    38    
  hydropower    Hydropower                                                    24     
  nuclear       Nuclear                                                       12    
  solar         Concentrated Solar Power, Solar PV—rooftop,Solar PV—utility   38.6   
  wind          Wind onshore, Wind offshore                                   11.5   
 ============= ============================================================= ======

One challenge with the carbon intensity calculation is that the values can vary depending on the methodology used to make the calculation. Thus, we provide CI values calculated using multiple approaches (essentially different base values). These values are included in the DataFrame as different columns. You can also use your own base values. By default, the IPCC values are used.

When energy generation data is not available for a country, the average values of Carbon Intensity is used. The source of this data is Carbon Footprint Ltd [8]

.. automodule:: codegreen_core.tools.carbon_intensity
   :members:

Carbon emission of a job
-------------------------

**The Methodology for calculating carbon emissions** (Based on [7])

Carbon emission of a job depends on 2 factors : Energy consumed by the hardware to run the computation and the emissions generated to produce this energy. The unit used is CO2e or Carbon dioxide equivalent.

- Carbon Emissions : :math:`\text{CE} = E \times \text{CI}` (in :math:`CO_{2}e` )
- Energy consumption : :math:`E = t \times \left( n_{c} \times P_{c} \times u_{c} + n_{m} \times P_{m} \right) \times PUE \times 0.001` (in kWh)

   - :math:`t` : running time in hours 
   - :math:`n_c` : the number of core 
   - :math:`n_m` : the size of memory available (in Gigabytes)
   - :math:`u_c` : the core usage factor (between 0 and 1)
   - :math:`P_c` : power draw of a computing core (Watt)
   - :math:`P_m` : power draw of memory (Watt)
   - :math:`PUE` :  efficiency coefficient of the data center
   
- Emissions related to the production of the energy : represented by the Carbon Intensity of the energy mix during that period. Already implemented above


.. automodule:: codegreen_core.tools.carbon_emission
   :members:


Optimal time shifting 
---------------------

.. automodule:: codegreen_core.tools.loadshift_time
   :members:


Optimal Location shifting 
-------------------------

.. automodule:: codegreen_core.tools.loadshift_location
   :members:
