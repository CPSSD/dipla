import json


class ConfigHandler:
    """
    This class handles all the config parameters for the Dipla client.
    Paramters can be accessed using the `my_config.params` dict.

    Values can be added manually (add_param) or by a file (parse_from_file)

    The parameters are pre-populated using the config_defaults unless otherwise
    specified when initalising the class.
    """

    config_defaults = {
        'server_ip': 'localhost',
        'server_port': 8765,
        'log_file': 'DIPLA_CLIENT.log',
        'password': None
    }

    """
    To add a configurable parameter to the config add its name and type here.
    """
    config_types = {
        'server_ip': str,
        'server_port': int,
        'log_file': str,
        'password': str,
    }

    def __init__(self, fill_defaults=True):
        self.params = dict(self.config_defaults) if fill_defaults else {}

    def parse_from_file(self, filename):
        with open(filename, 'r') as conf_file:
            conf_dict = json.load(conf_file)

        for param in conf_dict:
            self.add_param(param, conf_dict[param])

    def add_param(self, param_name, param_value):
        self.__check_param(param_name, param_value)
        self.params[param_name] = param_value

    def __check_param(self, param_name, param_value):
        if param_name not in self.config_types:
            raise InvalidConfigException(
                "Unknown parameter '{}'".format(param_name))
        if not isinstance(param_value, self.config_types[param_name]):
            raise InvalidConfigException(
                "Parameter '{}' isn't of type '{}'".format(
                    param_name, self.config_types[param_name]))


class InvalidConfigException(Exception):
    pass
