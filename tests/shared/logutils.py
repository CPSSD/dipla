import unittest
from unittest.mock import patch

from dipla.shared.logutils import LogUtils


class LogUtilsTest(unittest.TestCase):

    @patch('dipla.shared.logutils.LogUtils.logger')
    def test_log_debug_logs_to_debug(self, mock_logger):
        LogUtils.log_debug('Test message')
        mock_logger.debug.assert_called_with('Test message')

    @patch('dipla.shared.logutils.LogUtils.logger')
    def test_log_warning_logs_to_warning(self, mock_logger):
        LogUtils.log_warning('Test message')
        mock_logger.warning.assert_called_with('Test message')

    @patch('dipla.shared.logutils.LogUtils.logger')
    def test_log_error_logs_error(self, mock_logger):
        LogUtils.log_error('Test Message', ValueError('Test Error'))
        mock_logger.error.assert_called_with('Test Message: Test Error')
