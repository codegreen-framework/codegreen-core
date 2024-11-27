import os
import configparser
import redis


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


class Config:
    config_data = None
    section_name = "codegreen"
    all_keys = [
        {
            "name":"ENTSOE_token",
            "default": "None",
            "use":"To fetch data from ENTSOE portal",
            "boolean":False,
        },
        {
            "name":"default_energy_mode",
            "default":"public_data",
            "use":"Determines which type of data to use.",
            "boolean":False,
        },
        {
            "name":"enable_energy_caching",
            "default":"False",
            "use":"To indicate if data used by tools must be cached",
            "boolean":True,
        },
        {
            "name":"energy_redis_path",
            "default":"None",
            "boolean":False,
            "use":"Path to redis server to cache data.required if enable_energy_caching is enabled "
        },
        {
            "name":"enable_time_prediction_logging",
            "default":"False",
            "boolean":True,
            "use":"To indicate if logs must me saved in a log file  "
        },
         {
            "name":"log_folder_path",
            "default":" ",
            "boolean":False,
            "use":"Path of the folder where logs will be stored"
        }
    
    ]

    @classmethod
    def load_config(self, file_path=None):
        """to load configurations from the user config file"""
        config_file_name = ".codegreencore.config"
        config_locations = [
            os.path.join(os.path.expanduser("~"), config_file_name),
            os.path.join(os.getcwd(), config_file_name),
        ]
        for loc in config_locations:
            if os.path.isfile(loc):
                file_path = loc
                break

        if file_path is None:
            raise ConfigError("Could not find the '.codegreencore.config' file. Please ensure that this file is created in the root folder of your project.")

        self.config_data = configparser.ConfigParser()
        self.config_data.read(file_path)

        if self.section_name not in self.config_data:
            self.config_data[self.section_name] = {}
            raise ConfigError("Invalid config file. The config file must have a section called codegreen")
        
        for ky in self.all_keys:
            try :
                value = self.config_data.get(self.section_name, ky["name"])
                # print(value)
            except configparser.NoOptionError:
                self.config_data.set(self.section_name, ky["name"],ky["default"])
            
        if self.get("enable_energy_caching") == True:
            if self.get("energy_redis_path") is None:
                raise ConfigError(
                    "Invalid configuration. If 'enable_energy_caching' is set, 'energy_redis_path' is also required  "
                )
            else:
                r = redis.from_url(self.get("energy_redis_path"))
                r.ping()
                # print("Connection to redis works")

    @classmethod
    def get(self, key):
        if not self.config_data.sections():
            raise ConfigError(
                "Configuration not loaded. Please call 'load_config' first."
            )
        try:
            value = self.config_data.get(self.section_name, key)
            config = next((d for d in self.all_keys if d.get("name") == key), None)
            if config["boolean"]:
                return  value.lower() == "true"
            return value
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            print("Config not found")
            print(key)
            raise e
