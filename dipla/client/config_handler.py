import json


class ConfigHandler:

    config_defaults = {
        'server_ip': 'localhost',
        'server_port': 8765,
    }
    config_types = {
        'server_ip': str,
        'server_port': int,
    }

    def __init__(self, fill_defaults=True):
        self.params = dict(self.config_defaults) if fill_defaults else {}

    def parse_from_file(self, filename):
        with open(filename, 'r') as conf_file:
            conf_dict = json.load(conf_file)
        if not isinstance(conf_dict, dict):
            raise InvalidConfig("Config must be in the form of a dict")

        for param in conf_dict:
            self.add_param(param, conf_dict[param])

    def add_param(self, param_name, param_value):
        self.__check_param(param_name, param_value)
        self.params[param_name] = param_value

    def __check_param(self, param_name, param_value):
        if param_name not in self.config_types:
            raise InvalidConfig("Unknown parameter '{}'".format(param_name))
        if not isinstance(param_value, self.config_types[param_name]):
            raise InvalidConfig("Parameter '{}' isn't of type '{}'".format(
                param_name, self.config_types[param_name]))

class InvalidConfig(Exception):
    pass
