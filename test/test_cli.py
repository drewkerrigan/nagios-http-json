#!/usr/bin/env python3


import unittest
import unittest.mock as mock
import sys
import os

sys.path.append('..')

from check_http_json import debugPrint
from check_http_json import verbosePrint


class CLITest(unittest.TestCase):
    """
    Tests for CLI
    """

    def setUp(self):
        """
        Defining the exitcodes
        """

        self.exit_0 = 0 << 8
        self.exit_1 = 1 << 8
        self.exit_2 = 2 << 8
        self.exit_3 = 3 << 8

    def test_debugprint(self):
        with mock.patch('builtins.print') as mock_print:
            debugPrint(True, 'debug')
            mock_print.assert_called_once_with('debug')

    def test_verbose(self):
        with mock.patch('builtins.print') as mock_print:
            verbosePrint(0, 3, 'verbose')
            mock_print.assert_not_called()

            verbosePrint(3, 3, 'verbose')
            mock_print.assert_called_once_with('verbose')

    def test_cli_without_params(self):

        command = '/usr/bin/env python3 check_http_json.py > /dev/null 2>&1'
        status = os.system(command)

        self.assertEqual(status, self.exit_2)
