#!/usr/bin/env python3


import unittest
import sys

sys.path.append('..')

from check_http_json import *


class ArgsTest(unittest.TestCase):
    """
    Tests for argsparse
    """

    def test_parser_defaults(self):
        parser = parseArgs(['-H', 'foobar'])
        self.assertFalse(parser.debug)
        self.assertFalse(parser.ssl)
        self.assertFalse(parser.insecure)

    def test_parser_with_debug(self):
        parser = parseArgs(['-H', 'foobar', '-d'])
        self.assertTrue(parser.debug)

    def test_parser_with_port(self):
        parser = parseArgs(['-H', 'foobar', '-P', '8888'])
        self.assertEqual(parser.port, '8888')
