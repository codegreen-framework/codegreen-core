import os
import configparser
import redis

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    config_data = None
    config_file_path = None
    section_name = "codegreen"
    all_keys = [
        {"name": "ENTSOE_token", "default": "None", "use": "To fetch data from ENTSOE portal", "boolean": False},
        {"name": "default_energy_mode", "default": "public_data", "use": "Determines which type of data to use.", "boolean": False},
        {"name": "enable_energy_caching", "default": "False", "use": "To indicate if data used by tools must be cached", "boolean": True},
        {"name": "energy_redis_path", "default": "None", "boolean": False, "use": "Path to redis server to cache data."},
        {"name": "enable_time_prediction_logging", "default": "False", "boolean": True, "use": "To indicate if logs must be saved."},
        {"name": "log_folder_path", "default": "", "boolean": False, "use": "Path of the folder where logs will be stored"},
        {"name": "offline_data_dir_path", "default": "", "boolean": False, "use": "Path where bulk energy data will be stored"},
        {"name": "enable_offline_energy_generation", "default": "False", "boolean": True, "use": "Enable storing energy data locally"},
        {"name": "offline_data_start_date", "default": "", "boolean": False, "use": "Start date for offline energy data"},
        {"name": "generation_cache_hour", "default": "72", "boolean": False, "use": "Number of hours data will be cached"},
        {"name": "cron_refresh_offline_files_hour", "default": "6", "boolean": False, "use": "CRON schedule for updating offline files"},
        {"name": "cron_refresh_cache_hour", "default": "6", "boolean": False, "use": "CRON job to update energy cache"},
        {"name": "enable_logging", "default": "False", "boolean": True, "use": "Enable logging for the package"}
    ]

    @classmethod
    def load_config(cls, file_path=None):
        """Load configurations from a config file or environment variables."""
        config_file_name = ".codegreencore.config"
        config_locations = [
            os.path.join(os.path.expanduser("~"), config_file_name),
            os.path.join(os.getcwd(), config_file_name),
        ]
        for loc in config_locations:
            if os.path.isfile(loc):
                file_path = loc
                break
        cls.config_data = configparser.ConfigParser()
        if file_path:
            cls.config_data.read(file_path)
            cls.config_file_path = file_path

            if cls.section_name not in cls.config_data:
                raise ConfigError(f"Invalid config file. Missing required section: {cls.section_name}")
        else:
            cls.config_data[cls.section_name] = {}
        
        for ky in cls.all_keys:
            if cls.config_data.has_option(cls.section_name, ky["name"]):
                value = cls.config_data.get(cls.section_name, ky["name"])
            else:
                env_key = f"cgc_{ky['name']}"
                value = os.getenv(env_key, ky["default"])
                cls.config_data.set(cls.section_name, ky["name"], value)
        
        if cls.get("enable_energy_caching"):
            if not cls.get("energy_redis_path"):
                raise ConfigError("'energy_redis_path' is required when 'enable_energy_caching' is enabled.")
            redis.from_url(cls.get("energy_redis_path")).ping()

        if cls.get("enable_logging"):
            if not cls.get("log_folder_path"):
                raise ConfigError("'log_folder_path' is required when 'enable_logging' is enabled.")
            os.makedirs(cls.get("log_folder_path"), exist_ok=True)

    @classmethod
    def get(cls, key):
        if not cls.config_data.sections():
            raise ConfigError("Configuration not loaded. Call 'load_config' first.")
        
        value = cls.config_data.get(cls.section_name, key, fallback=None)
        config = next((d for d in cls.all_keys if d["name"] == key), None)
        if config and config["boolean"]:
            return value.lower() == "true"
        return value
    
    @classmethod
    def get_config_file_path(cls):
        """Returns the path of the config file."""
        return cls.config_file_path
