import os
from unittest import TestCase
from dipla.client.config_handler import ConfigHandler, InvalidConfigException


class ConfigHandlerTest(TestCase):

    def test_correct_config_handler_defaults(self):
        # Test that everything in the defaults follows the type rules
        for param_name in ConfigHandler.config_defaults:
            self.assertIn(param_name, ConfigHandler.config_types)
            self.assertIsInstance(
                ConfigHandler.config_defaults[param_name],
                ConfigHandler.config_types[param_name])

    def test_defaults_not_applied(self):
        c = ConfigHandler(fill_defaults=False)
        self.assertEqual(c.params, {})

    def test_param_can_be_added(self):
        c = ConfigHandler(fill_defaults=False)
        param_name, param_value = self.get_valid_param()
        c.add_param(param_name, param_value)
        self.assertIn(param_name, c.params)
        self.assertEqual(param_value, c.params[param_name])

    def test_unknown_param_cant_be_added(self):
        c = ConfigHandler()
        param_name, param_value = 'invalid_test_param', 42
        with self.assertRaises(InvalidConfigException):
            c.add_param(param_name, param_value)

    def test_param_of_wrong_type_cant_be_added(self):
        c = ConfigHandler()
        param_name, param_value = self.get_valid_param()
        if isinstance(param_value, str):
            param_value = 42
        else:
            param_value = 'wrong type'
        with self.assertRaises(InvalidConfigException):
            c.add_param(param_name, param_value)

    def get_valid_param(self):
        return list(ConfigHandler.config_defaults.items())[0]
