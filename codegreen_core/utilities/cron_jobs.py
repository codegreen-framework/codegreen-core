"""
to set up cron jobs
1. to update cache of energy generation data 
2. to update the offline files 
3. to run re-training of energy models 

1,2 can be done together and must be done more frequently 
3 has to be done once every 3 month or so. 
"""

import sys
import getpass
import importlib.util
import os
from crontab import CronTab
from .config import Config
from .log import log_stuff

PACKAGE_NAME = "codegreen_core"  # Replace with your package's name
USER = getpass.getuser()  # Get current user

def get_package_path():
    """Returns the installed path of the package."""
    spec = importlib.util.find_spec(PACKAGE_NAME)
    if not spec or not spec.origin:
        raise RuntimeError(f"Package '{PACKAGE_NAME}' not found.")
    return os.path.dirname(spec.origin)

def get_script_path(script_name):
    """Returns the full path of the script inside the package."""
    return os.path.join(get_package_path(), script_name)

def get_cron():
    """Returns a cron object for the current user."""
    return CronTab(user=USER)

def job_exists(command):
    """Check if a cron job with the given command already exists."""
    cron = get_cron()
    return any(job.command == command for job in cron)

def add_cron_jobs():
    """Adds cron jobs for s1.py and s2.py if they don't already exist."""
    cron = get_cron()

    # Get full script paths
    command_s1 = f"python3 {get_script_path('utilities/update_offline_files.py')}"
    command_s2 = f"python3 {get_script_path('utilities/update_cache.py')}"

    # Check if jobs already exist
    if job_exists(command_s1) or job_exists(command_s2):
        print("Cron jobs already exist.")
        return

    # Add new cron jobs
    job1 = cron.new(command=command_s1, comment="codegreen_core_job1")
    job2 = cron.new(command=command_s2, comment="codegreen_core_job2")

    # Set schedule (example: every minute)
    job1_hour =  int(Config.get("cron_refresh_offline_files_hour")) # cache
    job2_hour =  int(Config.get("cron_refresh_cache_hour"))  # offline file

    if job1_hour < 0 or job1_hour > 24:
        raise RuntimeError("Invalid cron_refresh_offline_files_hour must be between 1 and 24")
        
    if job2_hour < 0 or job2_hour > 24:
        raise RuntimeError("Invalid cron_refresh_cache_hour must be between 1 and 24")
        
    job1.hour.every(job1_hour)
    job2.hour.every(job2_hour)

    # Write the jobs to cron
    cron.write()
    log_stuff("Cron jobs set ")
    print("Cron jobs added successfully.")

def remove_cron_jobs():
    """Removes the cron jobs for s1.py and s2.py."""
    cron = get_cron()
    cron.remove_all(comment="codegreen_core_job1")
    cron.remove_all(comment="codegreen_core_job2")
    cron.write()
    print("Cron jobs removed successfully.")
    log_stuff("Cron jobs removed ")

def list_cron_jobs():
    """Lists all cron jobs related to the package."""
    cron = get_cron()
    found = False
    for job in cron:
        if "codegreen_core_job1" in job.comment or "codegreen_core_job2" in job.comment:
            print(f"{job}")
            found = True
    if not found:
        print("No cron jobs found for this package.")

# def main(action):
#     """Main function to start, stop, or list cron jobs."""
#     if action == "start":
#         add_cron_jobs()
#     elif action == "stop":
#         remove_cron_jobs()
#     elif action == "list":
#         list_cron_jobs()
#     else:
#         print("Invalid command. Use 'start', 'stop', or 'list'.")


# if __name__ == "__main__":
#     if len(sys.argv) != 2:
#         print("Usage: python manage_cron.py <start|stop|list>")
#         sys.exit(1)

#     main(sys.argv[1])