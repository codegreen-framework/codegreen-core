import os
import configparser
import redis


class ConfigError(Exception):
    """Custom exception for configuration errors."""

    pass


class Config:
    config_data = None
    section_name = "codegreen"
    boolean_keys = {"enable_energy_caching", "enable_time_prediction_logging"}
    defaults = {
        "default_energy_mode": "public_data",
        "enable_energy_caching": False,
        "enable_time_prediction_logging": False,
        "energy_redis_path": None,
    }

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
            raise ConfigError("404 config")

        self.config_data = configparser.ConfigParser()
        self.config_data.read(file_path)

        if self.section_name not in self.config_data:
            self.config_data[self.section_name] = {}
        for key, default_value in self.defaults.items():
            if not self.config_data.has_option(self.section_name, key):
                self.config_data.set(self.section_name, key, str(default_value))

        if self.get("enable_energy_caching") == True:
            if self.get("energy_redis_path") is None:
                raise ConfigError(
                    "Invalid configuration. If 'enable_energy_caching' is set, 'energy_redis_path' is also required  "
                )
            else:
                r = redis.from_url(self.get("energy_redis_path"))
                r.ping()
        # print(self.config_data["default_energy_mode"])

    @classmethod
    def get(self, key):
        if not self.config_data.sections():
            raise ConfigError(
                "Configuration not loaded. Please call 'load_config' first."
            )
        try:
            value = self.config_data.get(self.section_name, key)
            if value is None:
                # if key not in self.defaults:
                #    raise KeyError(f"No default value provided for key: {key}")
                value = self.defaults.get(key, None)
            else:
                if key in self.boolean_keys:
                    value = value.lower() == "true"
            return value
        except (configparser.NoSectionError, configparser.NoOptionError):
            return self.defaults.get(key)  # Return default if key is missing
