#!/usr/bin/env python3


import unittest
import unittest.mock as mock
import sys

sys.path.append('..')

from check_http_json import debugPrint


class MainTest(unittest.TestCase):
    """
    Tests for main
    """

    def test_debugprint(self):
        with mock.patch('builtins.print') as mock_print:
            debugPrint(True, 'debug')
            mock_print.assert_called_once_with('debug')

    def test_debugprint_pprint(self):
        with mock.patch('check_http_json.pprint') as mock_pprint:
            debugPrint(True, 'debug', True)
            mock_pprint.assert_called_once_with('debug')
