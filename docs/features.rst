Features of `codegreen-core`
=============================

**Gather energy production data**

Energy is produced from multiple sources, some of these sources are non-renewable, such as fossil fuels and coal, and others are renewable, like wind and solar. The combination of energy produced from different sources (or the energy mix) varies from country to country and season to season. The amount of carbon emissions generated from energy production depends on this energy mix. When more energy is derived from renewable sources, carbon emissions are lower, making the energy more 'green.' (and vice versa). This relationship is measured by carbon intensity, which quantifies the amount of carbon dioxide emitted per unit of energy produced.

The codegreen-core package offers tools to collect time series data of the energy mix for various countries, which can also be used to calculate the carbon intensity of energy.

.. image:: _static/DE_1.png
   :alt: Germany example 1
   :width: 600px  
   :align: center  

The figure above shows the percentage of energy generated from renewable (green) and non renewable (red) sources in Germany on 1st and 2nd June 2024.

This data helps analyze the energy production in a country over a period of time to  identify patterns and compare energy data for  multiple countries. 

.. image:: _static/multiple_2.png
   :alt: Multiple example 1
   :width: 800px  
   :align: center 

The figure above shows the percentage of energy generated from renewable sources in four countries (Germany, France, Italy, and Spain) from June 1 to June 24, 2024.

An interesting observation is that the amount of green energy changes almost every hour. This presents two approaches to reducing carbon emissions:

- **Time Shifting**: Adjusting the timing of computations to align with periods of greater availability of green energy.
- **Location Shifting**: Moving computational tasks to locations that utilize more green energy.


**Calculating carbon emission of a computational task**

Given the time taken by a computational task, the location where it was performed, and the hardware specifications (number of cores/GPUs used and size of memory), the codegreen-core package provides an estimate of the carbon emissions produced by the task


.. image:: _static/CE_DE_1.png
   :alt: CE DE example 1
   :width: 600px  
   :align: center 

The figure above shows the carbon emissions produced by a 12-hour computational task performed on 124 cores with 64 GB of memory in Germany


**Predicting the optimal time/location to start the computational task**

Given the approximate run time of the task, the hardware specifications, the location, and a specified criteria,  `codegreen-core`  predicts an optimal time based on energy production forecast data. It is designed to be fault-tolerant, and if no optimal time exists, the current time is returned. The user provides a criteria, such as the minimum percentage of renewable energy for the entire duration, which is used to predict the optimal time. 

.. image:: _static/optimal_it_1.png
   :alt: optimal eg 1
   :width: 800px  
   :align: center 

The figure above shows the carbon emissions produced by an 8-hour computational task performed on 124 cores with 64 GB of memory in Italy, along with the potential savings in carbon emissions when the computation is started at suggested times using three different criteria (values of percentage renewable energy).

..
  // Challenges and future plans 
  // One of the main challenges is the availability of time series of energy produced using renewable and non renewable sources for different coutnreis. The current energy forecasts are also limited to the next 24 hours which limits the optimal time decitions within the next 24 hours.  In future, we plan to integrate data for Non EU counties as well as train predication models that can generate time series forecasts of for longer periods of time. 