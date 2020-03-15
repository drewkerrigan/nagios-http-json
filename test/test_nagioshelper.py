#!/usr/bin/env python3


import json
import unittest
from unittest.mock import patch
import sys

sys.path.append('..')

from check_http_json import *


class NagiosHelperTest(unittest.TestCase):
    """
    Tests for the NagiosHelper
    """

    def test_getcode_default(self):

        helper = NagiosHelper()
        self.assertEqual(0, helper.getCode())

    def test_getcode_warning(self):

        helper = NagiosHelper()
        helper.warning_message = 'foobar'
        self.assertEqual(1, helper.getCode())

    def test_getcode_critical(self):

        helper = NagiosHelper()
        helper.critical_message = 'foobar'
        self.assertEqual(2, helper.getCode())

    def test_getcode_unknown(self):

        helper = NagiosHelper()
        helper.unknown_message = 'foobar'
        self.assertEqual(3, helper.getCode())

    def test_getmessage_default(self):

        helper = NagiosHelper()
        self.assertEqual('OK: Status OK.', helper.getMessage())

    def test_getmessage_perfomance_data(self):

        helper = NagiosHelper()
        helper.performance_data = 'foobar'
        self.assertEqual('OK: Status OK.|foobar', helper.getMessage())
