import os
import configparser

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
  config_data = None

  @classmethod
  def load_config(self,file_path=None):
    """ to load configurations from the user config file 
    """
    config_file_name = ".codegreencore.config"
    config_locations = [
      os.path.join(os.path.expanduser("~"),config_file_name),
      os.path.join(os.getcwd(),config_file_name)
    ]

    for loc in config_locations:
      if os.path.isfile(loc):
        file_path = loc
        break
    
    if file_path is None:
      raise ConfigError("404 config")
    
    self.config_data = configparser.ConfigParser()
    self.config_data.read(file_path)
    
  
  @classmethod    
  def get(self,key):
    if not self.config_data.sections():
      raise ConfigError("Configuration not loaded. Please call 'load_config' first.")
    try:
      section_name = "codegreen"
      return self.config_data.get(section_name,key)
    except (configparser.NoSectionError, configparser.NoOptionError):
      return None
