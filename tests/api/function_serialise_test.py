from unittest import TestCase
from base64 import b64decode
from dill import loads
from types import CodeType
from dipla.api_support.function_serialise import serialise_code_object
from dipla.api_support.function_serialise import get_encoded_script
from dipla.api_support import script_templates


class SerialiseCodeObjectTest(TestCase):

    def test_code_object_can_be_pickled(self):
        example_func = self._get_example_function()
        pickled_co = serialise_code_object(example_func.__code__)

    def test_pickled_code_object_is_valid(self):
        example_func = self._get_example_function()
        pickled_co = serialise_code_object(example_func.__code__)
        decoded_co = loads(pickled_co)

        co = CodeType(*decoded_co)
        self.assertEqual(co, example_func.__code__)

    def _get_example_function(self):
        def example_func(x, y):
            return x + y
        return example_func


class ScriptEncoderTest(TestCase):

    def test_function_can_be_encoded(self):
        example_func = self._get_example_function()
        b64_script = get_encoded_script(
            example_func,
            script_templates.argv_input_script)

    def test_encoded_script_valid_base64(self):
        example_func = self._get_example_function()
        b64_script = get_encoded_script(
            example_func,
            script_templates.argv_input_script)
        decoded_script = b64decode(b64_script)
        self.assertEqual(type(decoded_script), bytes)

    def _get_example_function(self):
        def example_func(x, y):
            return x + y
        return example_func
