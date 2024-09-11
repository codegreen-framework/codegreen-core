from .carbon_emission import calculate_carbon_emission_job

def get_saving_same_device(country_code,start_time_request,start_time_predicted,runtime,cpu_cores,cpu_memory):
  
  ce_job1,ci1 = calculate_carbon_emission_job(country_code,start_time_request,runtime,cpu_cores,cpu_memory) 
  ce_job2,ci2 = calculate_carbon_emission_job(country_code,start_time_predicted,runtime,cpu_cores,cpu_memory)
  return ce_job1-ce_job2 # ideally this should be positive todo what if this is negative?, make a note in the comments 