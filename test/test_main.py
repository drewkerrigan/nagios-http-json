#!/usr/bin/env python3


import unittest
import unittest.mock as mock
import sys
import os

sys.path.append('..')

from check_http_json import main


class MockResponse():
    def __init__(self, status_code=200, content='{"foo": "bar"}'):
        self.status_code = status_code
        self.content = content

    def read(self):
        return self.content


class MainTest(unittest.TestCase):
    """
    Tests for Main
    """

    @mock.patch('builtins.print')
    def test_main_version(self, mock_print):
        args = ['--version']

        with self.assertRaises(SystemExit) as test:
            main(args)

        mock_print.assert_called_once()
        self.assertEqual(test.exception.code, 0)

    @mock.patch('builtins.print')
    @mock.patch('urllib.request.urlopen')
    def test_main_with_ssl(self, mock_request, mock_print):
        args = '-H localhost --ssl'.split(' ')

        mock_request.return_value = MockResponse()

        with self.assertRaises(SystemExit) as test:
            main(args)

        self.assertEqual(test.exception.code, 0)


    @mock.patch('builtins.print')
    @mock.patch('urllib.request.urlopen')
    def test_main_with_parse_error(self, mock_request, mock_print):
        args = '-H localhost'.split(' ')

        mock_request.return_value = MockResponse(content='not JSON')

        with self.assertRaises(SystemExit) as test:
            main(args)

        self.assertTrue('Parser error' in str(mock_print.call_args))
        self.assertEqual(test.exception.code, 3)

    @mock.patch('builtins.print')
    def test_main_with_url_error(self, mock_print):
        args = '-H localhost'.split(' ')

        with self.assertRaises(SystemExit) as test:
            main(args)

        self.assertTrue('URLError' in str(mock_print.call_args))
        self.assertEqual(test.exception.code, 3)

    @mock.patch('builtins.print')
    @mock.patch('urllib.request.urlopen')
    def test_main_with_http_error_no_json(self, mock_request, mock_print):
        args = '-H localhost'.split(' ')

        mock_request.return_value = MockResponse(content='not JSON', status_code=503)

        with self.assertRaises(SystemExit) as test:
            main(args)

        self.assertTrue('Parser error' in str(mock_print.call_args))
        self.assertEqual(test.exception.code, 3)

    @mock.patch('builtins.print')
    @mock.patch('urllib.request.urlopen')
    def test_main_with_http_error_valid_json(self, mock_request, mock_print):
        args = '-H localhost'.split(' ')

        mock_request.return_value = MockResponse(status_code=503)

        with self.assertRaises(SystemExit) as test:
            main(args)

        self.assertEqual(test.exception.code, 0)
