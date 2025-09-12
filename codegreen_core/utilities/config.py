import configparser
from pathlib import Path

VALID_ENERGY_MODES = ["public_data"]

class Config:

    @classmethod
    def validate(cls):
        if cls.ENTSOE_TOKEN is None:
            raise ValueError("Config.ENTSOE_TOKEN must be set!")

        if cls.DEFAULT_ENERGY_MODE not in VALID_ENERGY_MODES:
            raise ValueError(f"Config.DEFAULT_ENERGY_MODE: {cls.DEFAULT_ENERGY_MODE} is not valid! Must be one of: {VALID_ENERGY_MODES}")
        
        if cls.ENABLE_ENERGY_CACHING is True and cls.REDIS_PATH is None:
            raise ValueError(f"Config.ENABLE_ENERGY_CACHING is enabled but Config.REDIS_PATH is not set!")
        

    @classmethod
    def load_config(cls, config_path):

        if not Path(config_path).exists():
            raise ValueError(f"Config file {config_path} does not exist!")

        config = configparser.ConfigParser()
        config.read(config_path)

        # General parameters
        cls.ENTSOE_TOKEN = config.get("DEFAULT", "ENTSOE_TOKEN", fallback=None) or None
        cls.DEFAULT_ENERGY_MODE = config.get("DEFAULT", "DEFAULT_ENERGY_MODE", fallback="public_data")

        # Cache section
        cls.ENABLE_ENERGY_CACHING = config.getboolean("Cache", "ENABLE_ENERGY_CACHING", fallback=False) 
        cls.REDIS_PATH = config.get("Cache", "REDIS_URL", fallback=None) or None
        cls.GENERATION_CACHE_HOUR = config.getint("Cache", "GENERATION_CACHE_HOUR", fallback=72)
        cls.FORECAST_CACHE_HOUR = config.getint("Cache", "FORECAST_CACHE_HOUR", fallback=24)

        # validate the config
        cls.validate()




