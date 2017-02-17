import unittest
import json

from dipla.shared.error_codes import ErrorCodes


class ErrorCodesTest(unittest.TestCase):

    def test_error_code_can_be_JSON_encoded(self):
        data = {
            "example": "test",
            "code": ErrorCodes.user_id_already_taken
        }
        # No assertions needed, if this doesn't cause an error then the
        # test passes
        json.dumps(data)
