#!/usr/bin/env python3

import urllib.request, urllib.error, urllib.parse
import base64
import json
import argparse
import sys
import ssl
import traceback
from urllib.error import HTTPError
from urllib.error import URLError
from datetime import datetime, timedelta, timezone

plugin_description = \
"""
Check HTTP JSON Nagios Plugin

Generic Nagios plugin which checks json values from a given endpoint against
argument specified rules and determines the status and performance data for
that service.
"""

OK_CODE = 0
WARNING_CODE = 1
CRITICAL_CODE = 2
UNKNOWN_CODE = 3

__version__ = '2.3.0'
__version_date__ = '2025-04-11'

class NagiosHelper:
    """
    Help with Nagios specific status string formatting.
    """

    message_prefixes = {OK_CODE: 'OK',
                        WARNING_CODE: 'WARNING',
                        CRITICAL_CODE: 'CRITICAL',
                        UNKNOWN_CODE: 'UNKNOWN'}
    performance_data = ''
    warning_message = ''
    critical_message = ''
    unknown_message = ''

    def getMessage(self, message=''):
        """
        Build a status-prefixed message with optional performance data
        generated externally
        """

        message += self.warning_message
        message += self.critical_message
        message += self.unknown_message
        code = self.message_prefixes[self.getCode()]
        output = "{code}: Status {code}. {message}".format(code=code, message=message.strip())
        if self.performance_data:
            output = "{code}: {perf_data} Status {code}. {message}|{perf_data}".format(
                code=code,
                message=message.strip(),
                perf_data=self.performance_data)
        return output.strip()

    def getCode(self):
        code = OK_CODE
        if (self.warning_message != ''):
            code = WARNING_CODE
        if (self.critical_message != ''):
            code = CRITICAL_CODE
        if (self.unknown_message != ''):
            code = UNKNOWN_CODE
        return code

    def append_message(self, code, msg):
        if code > 2 or code < 0:
            self.unknown_message += msg
        if code == 1:
            self.warning_message += msg
        if code == 2:
            self.critical_message += msg

    def append_metrics(self, metrics):
        (performance_data, warning_message, critical_message) = metrics
        self.performance_data += performance_data
        self.append_message(WARNING_CODE, warning_message)
        self.append_message(CRITICAL_CODE, critical_message)


class JsonHelper:
    """
    Perform simple comparison operations against values in a given
    JSON dict
    """

    def __init__(self, json_data, separator, value_separator):
        self.data = json_data
        self.separator = separator
        self.value_separator = value_separator
        self.arrayOpener = '('
        self.arrayCloser = ')'

    def getSubElement(self, key, data):
        separatorIndex = key.find(self.separator)
        partialKey = key[:separatorIndex]
        remainingKey = key[separatorIndex + 1:]
        if partialKey in data:
            return self.get(remainingKey, data[partialKey])
        return (None, 'not_found')

    def getSubArrayElement(self, key, data):
        subElemKey = key[:key.find(self.arrayOpener)]
        index = int(key[key.find(self.arrayOpener) +
                        1:key.find(self.arrayCloser)])
        remainingKey = key[key.find(self.arrayCloser + self.separator) + 2:]

        if key.find(self.arrayCloser + self.separator) == -1:
            remainingKey = key[key.find(self.arrayCloser) + 1:]
        if subElemKey in data:
            if index < len(data[subElemKey]):
                return self.get(remainingKey, data[subElemKey][index])
            else:
                return (None, 'not_found')
        if index >= len(data):
            return (None, 'not_found')
        else:
            if not subElemKey:
                return self.get(remainingKey, data[index])
            else:
                return (None, 'not_found')

    def equals(self, key, value):
        return self.exists(key) and \
            str(self.get(key)) in value.split(self.value_separator)

    def lte(self, key, value):
        return self.exists(key) and float(self.get(key)) <= float(value)

    def lt(self, key, value):
        return self.exists(key) and float(self.get(key)) < float(value)

    def gte(self, key, value):
        return self.exists(key) and float(self.get(key)) >= float(value)

    def gt(self, key, value):
        return self.exists(key) and float(self.get(key)) > float(value)

    def exists(self, key):
        return (self.get(key) != (None, 'not_found'))

    def get(self, key, temp_data=''):
        """
        Can navigate nested json keys with a dot format
        (Element.Key.NestedKey). Returns (None, 'not_found') if not found
        """

        if temp_data != '':
            data = temp_data
        else:
            data = self.data
        if len(key) <= 0:
            return data
        if key.find(self.separator) != -1 and \
           key.find(self.arrayOpener) != -1:
            if key.find(self.separator) < key.find(self.arrayOpener):
                return self.getSubElement(key, data)
            else:
                return self.getSubArrayElement(key, data)
        else:
            if key.find(self.separator) != -1:
                return self.getSubElement(key, data)
            else:
                if key.find(self.arrayOpener) != -1:
                    return self.getSubArrayElement(key, data)
                else:
                    if isinstance(data, dict) and key in data:
                        return data[key]
                    else:
                        return (None, 'not_found')

    def expandKey(self, key, keys):
        if '(*)' not in key:
            keys.append(key)
            return keys
        subElemKey = ''
        if key.find('(*)') > 0:
            subElemKey = key[:key.find('(*)')-1]
        remainingKey = key[key.find('(*)')+3:]
        elemData = self.get(subElemKey)
        if elemData == (None, 'not_found'):
            keys.append(key)
            return keys
        if subElemKey != '':
            subElemKey = subElemKey + '.'
        for i in range(len(elemData)):
            newKey = subElemKey + '(' + str(i) + ')' + remainingKey
            newKeys = self.expandKey(newKey, [])
            for j in newKeys:
                keys.append(j)

        return keys


def _getKeyAlias(original_key):
    key = original_key
    alias = original_key
    if '>' in original_key:
        keys = original_key.split('>')
        if len(keys) == 2:
            key, alias = keys
    return key, alias


class JsonRuleProcessor:
    """
    Perform checks and gather values from a JSON dict given rules
    and metrics definitions
    """

    def __init__(self, json_data, rules_args):
        self.data = json_data
        self.rules = rules_args
        separator = '.'
        value_separator = ':'
        if self.rules.separator:
            separator = self.rules.separator
        if self.rules.value_separator:
            value_separator = self.rules.value_separator
        self.helper = JsonHelper(self.data, separator, value_separator)
        debugPrint(rules_args.debug, "rules: %s" % rules_args)
        debugPrint(rules_args.debug, "separator: %s" % separator)
        debugPrint(rules_args.debug, "value_separator: %s" % value_separator)
        self.metric_list = self.expandKeys(self.rules.metric_list)
        self.key_threshold_warning = self.expandKeys(
            self.rules.key_threshold_warning)
        self.key_threshold_critical = self.expandKeys(
            self.rules.key_threshold_critical)
        self.key_value_list = self.expandKeys(self.rules.key_value_list)
        self.key_value_list_not = self.expandKeys(
            self.rules.key_value_list_not)
        self.key_time_list = self.expandKeys(self.rules.key_time_list)
        self.key_list = self.expandKeys(self.rules.key_list)
        self.key_value_list_critical = self.expandKeys(
            self.rules.key_value_list_critical)
        self.key_value_list_not_critical = self.expandKeys(
            self.rules.key_value_list_not_critical)
        self.key_time_list_critical = self.expandKeys(self.rules.key_time_list_critical)
        self.key_list_critical = self.expandKeys(self.rules.key_list_critical)
        self.key_value_list_unknown = self.expandKeys(
            self.rules.key_value_list_unknown)

    def expandKeys(self, src):
        if src is None:
            return []
        dest = []
        for key in src:
            newKeys = self.helper.expandKey(key, [])
            for k in newKeys:
                dest.append(k)
        return dest

    def checkExists(self, exists_list):
        failure = ''
        for k in exists_list:
            key, alias = _getKeyAlias(k)
            if (self.helper.exists(key) is False):
                failure += " Key %s did not exist." % alias
        return failure

    def checkEquality(self, equality_list):
        failure = ''
        for kv in equality_list:
            k, v = kv.split(',')
            key, alias = _getKeyAlias(k)
            if not self.helper.equals(key, v):
                failure += " Key %s mismatch. %s != %s" % (alias, v,
                                                           self.helper.get(key))
        return failure

    def checkNonEquality(self, equality_list):
        failure = ''
        for kv in equality_list:
            k, v = kv.split(',')
            key, alias = _getKeyAlias(k)
            if self.helper.equals(key, v):
                failure += " Key %s match found. %s == %s" % (alias, v,
                                                              self.helper.get(key))
        return failure

    def checkThreshold(self, key, alias, r):
        failure = ''
        invert = False
        start = 0
        end = 'infinity'
        if r.startswith('@'):
            invert = True
            r = r[1:]
        vals = r.split(':')
        if len(vals) == 1:
            end = vals[0]
        if len(vals) == 2:
            start = vals[0]
            if vals[1] != '':
                end = vals[1]
        if(start == '~'):
            if (invert and self.helper.lte(key, end)):
                failure += " Value (%s) for key %s was less than or equal to %s." % \
                           (self.helper.get(key), alias, end)
            elif (not invert and self.helper.gt(key, end)):
                failure += " Value (%s) for key %s was greater than %s." % \
                           (self.helper.get(key), alias, end)
        elif(end == 'infinity'):
            if (invert and self.helper.gte(key, start)):
                failure += " Value (%s) for key %s was greater than or equal to %s." % \
                           (self.helper.get(key), alias, start)
            elif (not invert and self.helper.lt(key, start)):
                failure += " Value (%s) for key %s was less than %s." % \
                           (self.helper.get(key), alias, start)
        else:
            if (invert and self.helper.gte(key, start) and
                    self.helper.lte(key, end)):
                failure += " Value (%s) for key %s was inside the range %s:%s." % \
                           (self.helper.get(key), alias, start, end)
            elif (not invert and (self.helper.lt(key, start) or
                                  self.helper.gt(key, end))):
                failure += " Value (%s) for key %s was outside the range %s:%s." % \
                           (self.helper.get(key), alias, start, end)

        return failure

    def checkThresholds(self, threshold_list):
        failure = ''
        for threshold in threshold_list:
            k, r = threshold.split(',')
            key, alias = _getKeyAlias(k)
            failure += self.checkThreshold(key, alias, r)
        return failure

    def checkTimestamp(self, key, alias, r):
        failure = ''
        invert = False
        negative = False
        if r.startswith('@'):
            invert = True
            r = r[1:]
        if r.startswith('-'):
            negative = True
            r = r[1:]
        duration = int(r[:-1])
        unit = r[-1]

        if unit == 's':
            tiemduration = timedelta(seconds=duration)
        elif unit == 'm':
            tiemduration = timedelta(minutes=duration)
        elif unit == 'h':
            tiemduration = timedelta(hours=duration)
        elif unit == 'd':
            tiemduration = timedelta(days=duration)
        else:
            return " Value (%s) is not a vaild timeduration." % (r)

        if not self.helper.exists(key):
            return " Key (%s) for key %s not Exists." % \
                           (key, alias)

        try:
            timestamp = datetime.fromisoformat(self.helper.get(key))
        except ValueError as ve:
            return " Value (%s) for key %s is not a Date in ISO format. %s" % \
                           (self.helper.get(key), alias, ve)

        now = datetime.now(timezone.utc)

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        age = now - timestamp

        if not negative:
            if age > tiemduration and not invert:
                failure += " Value (%s) for key %s is older than now-%s%s." % \
                           (self.helper.get(key), alias, duration, unit)
            if not age > tiemduration and invert:
                failure += " Value (%s) for key %s is newer than now-%s%s." % \
                           (self.helper.get(key), alias, duration, unit)
        else:
            if age < -tiemduration and not invert:
                failure += " Value (%s) for key %s is newer than now+%s%s." % \
                           (self.helper.get(key), alias, duration, unit)
            if not age < -tiemduration and invert:
                failure += " Value (%s) for key %s is older than now+%s%s.." % \
                           (self.helper.get(key), alias, duration, unit)

        return failure

    def checkTimestamps(self, threshold_list):
        failure = ''
        for threshold in threshold_list:
            k, r = threshold.split(',')
            key, alias = _getKeyAlias(k)
            failure += self.checkTimestamp(key, alias, r)
        return failure

    def checkWarning(self):
        failure = ''
        if self.key_threshold_warning is not None:
            failure += self.checkThresholds(self.key_threshold_warning)
        if self.key_value_list is not None:
            failure += self.checkEquality(self.key_value_list)
        if self.key_value_list_not is not None:
            failure += self.checkNonEquality(self.key_value_list_not)
        if self.key_time_list is not None:
            failure += self.checkTimestamps(self.key_time_list)
        if self.key_list is not None:
            failure += self.checkExists(self.key_list)
        return failure

    def checkCritical(self):
        failure = ''
        if not self.data:
            failure = " Empty JSON data."
        if self.key_threshold_critical is not None:
            failure += self.checkThresholds(self.key_threshold_critical)
        if self.key_value_list_critical is not None:
            failure += self.checkEquality(self.key_value_list_critical)
        if self.key_value_list_not_critical is not None:
            failure += self.checkNonEquality(self.key_value_list_not_critical)
        if self.key_time_list_critical is not None:
            failure += self.checkTimestamps(self.key_time_list_critical)
        if self.key_list_critical is not None:
            failure += self.checkExists(self.key_list_critical)
        return failure

    def checkUnknown(self):
        unknown = ''
        if self.key_value_list_unknown is not None:
            unknown += self.checkEquality(self.key_value_list_unknown)
        return unknown

    def checkMetrics(self):
        """
        Return a Nagios specific performance metrics string given keys
        and parameter definitions
        """

        metrics = ''
        warning = ''
        critical = ''
        if self.metric_list is not None:
            for metric in self.metric_list:
                key = metric
                minimum = maximum = warn_range = crit_range = None
                uom = ''
                if ',' in metric:
                    vals = metric.split(',')
                    if len(vals) == 2:
                        key, uom = vals
                    if len(vals) == 4:
                        key, uom, warn_range, crit_range = vals
                    if len(vals) == 6:
                        key, uom, warn_range, crit_range, \
                            minimum, maximum = vals
                key, alias = _getKeyAlias(key)
                if self.helper.exists(key):
                    metrics += "'%s'=%s" % (alias, self.helper.get(key))
                    if uom:
                        metrics += uom
                    if warn_range is not None:
                        warning += self.checkThreshold(key, alias, warn_range)
                        metrics += ";%s" % warn_range
                    if crit_range is not None:
                        critical += self.checkThreshold(key, alias, crit_range)
                        metrics += ";%s" % crit_range
                    if minimum is not None:
                        critical += self.checkThreshold(key, alias, minimum +
                                                        ':')
                        metrics += ";%s" % minimum
                    if maximum is not None:
                        critical += self.checkThreshold(key, alias, '~:' +
                                                        maximum)
                        metrics += ";%s" % maximum
                metrics += ' '
        return ("%s" % metrics, warning, critical)


def parseArgs(args):
    """
    CLI argument definitions and parsing
    """

    parser = argparse.ArgumentParser(
        description=plugin_description + '\n\nVersion: %s (%s)'
        %(__version__, __version_date__),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('-d', '--debug', action='store_true',
                        help='debug mode')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='Verbose mode. Multiple -v options increase the verbosity')

    parser.add_argument('-s', '--ssl', action='store_true',
                        help='use TLS to connect to remote host')
    parser.add_argument('-H', '--host', dest='host',
                        required=not ('-V' in args or '--version' in args),
                        help='remote host to query')
    parser.add_argument('-k', '--insecure', action='store_true',
                        help='do not check server SSL certificate')
    parser.add_argument('-X', '--request', dest='method', default='GET', choices=['GET', 'POST'],
                        help='Specifies a custom request method to use when communicating  with  the HTTP server')
    parser.add_argument('-V', '--version', action='store_true',
                        help='print version of this plugin')
    parser.add_argument('--cacert',
                        dest='cacert', help='SSL CA certificate')
    parser.add_argument('--cert',
                        dest='cert', help='SSL client certificate')
    parser.add_argument('--key', dest='key',
                        help='SSL client key ( if not bundled into the cert )')
    parser.add_argument('-P', '--port', dest='port', help='TCP port')
    parser.add_argument('-p', '--path', dest='path', help='Path')
    parser.add_argument('-t', '--timeout', type=int,
                        help='Connection timeout (seconds)')
    parser.add_argument('--unreachable-state', type=int, default=3,
                        help='Exit with specified code when the URL is unreachable. Examples: 1 for Warning, 2 for Critical, 3 for Unknown (default: 3)')
    parser.add_argument('--invalid-json-state', type=int, default=3,
                        help='Exit with specified code when no valid JSON is returned. Examples: 1 for Warning, 2 for Critical, 3 for Unknown (default: 3)')
    parser.add_argument('-B', '--basic-auth', dest='auth',
                        help='Basic auth string "username:password"')
    parser.add_argument('-D', '--data', dest='data',
                        help='The http payload to send as a POST')
    parser.add_argument('-A', '--headers', dest='headers',
                        help='The http headers in JSON format.')
    parser.add_argument('-f', '--field_separator', dest='separator',
                        help='''JSON Field separator, defaults to ".";
                        Select element in an array with "(" ")"''')
    parser.add_argument('-F', '--value_separator', dest='value_separator',
                        help='''JSON Value separator, defaults to ":"''')
    parser.add_argument('-w', '--warning', dest='key_threshold_warning',
                        nargs='*',
                        help='''Warning threshold for these values
                        (key1[>alias],WarnRange key2[>alias],WarnRange).
                        WarnRange is in the format [@]start:end, more
                        information at
                        nagios-plugins.org/doc/guidelines.html.''')
    parser.add_argument('-c', '--critical', dest='key_threshold_critical',
                        nargs='*',
                        help='''Critical threshold for these values
                        (key1[>alias],CriticalRange key2[>alias],CriticalRange.
                        CriticalRange is in the format [@]start:end, more
                        information at
                        nagios-plugins.org/doc/guidelines.html.''')
    parser.add_argument('-e', '--key_exists', dest='key_list', nargs='*',
                        help='''Checks existence of these keys to determine
                        status. Return warning if key is not present.''')
    parser.add_argument('-E', '--key_exists_critical', dest='key_list_critical',
                        nargs='*',
                        help='''Same as -e but return critical if key is
                        not present.''')
    parser.add_argument('-q', '--key_equals', dest='key_value_list',
                        action='extend',
                        nargs='*',
                        help='''Checks equality of these keys and values
                        (key[>alias],value key2,value2) to determine status.
                        Multiple key values can be delimited with colon
                        (key,value1:value2). Return warning if equality
                        check fails''')
    parser.add_argument('-Q', '--key_equals_critical', dest='key_value_list_critical',
                        action='extend',
                        nargs='*',
                        help='''Same as -q but return critical if
                        equality check fails.''')
    parser.add_argument('--key_time', dest='key_time_list', nargs='*',
                        help='''Checks a Timestamp of these keys and values
                        (key[>alias],value key2,value2) to determine status.
                        Multiple key values can be delimited with colon
                        (key,value1:value2). Return warning if the key is older
                        than the value (ex.: 30s,10m,2h,3d,...).
                        With at it return warning if the key is jounger
                        than the value (ex.: @30s,@10m,@2h,@3d,...).
                        With Minus you can shift the time in the future.''')
    parser.add_argument('--key_time_critical',
                        dest='key_time_list_critical', nargs='*',
                        help='''Same as --key_time but return critical if
                        Timestamp age fails.''')
    parser.add_argument('-u', '--key_equals_unknown',
                        dest='key_value_list_unknown', nargs='*',
                        help='''Same as -q but return unknown if
                        equality check fails.''')
    parser.add_argument('-y', '--key_not_equals',
                        dest='key_value_list_not', nargs='*',
                        help='''Checks equality of these keys and values
                        (key[>alias],value key2,value2) to determine status.
                        Multiple key values can be delimited with colon
                        (key,value1:value2). Return warning if equality
                        check succeeds''')
    parser.add_argument('-Y', '--key_not_equals_critical',
                        dest='key_value_list_not_critical', nargs='*',
                        help='''Same as -q but return critical if equality
                        check succeeds.''')
    parser.add_argument('-m', '--key_metric', dest='metric_list',
                        action='extend',
                        nargs='*',
                        help='''Gathers the values of these keys (key[>alias],
                        UnitOfMeasure,WarnRange,CriticalRange,Min,Max) for
                        Nagios performance data. More information about Range
                        format and units of measure for nagios can be found at
                        nagios-plugins.org/doc/guidelines.html
                        Additional formats for this parameter are:
                        (key[>alias]), (key[>alias],UnitOfMeasure),
                        (key[>alias],UnitOfMeasure,WarnRange,
                        CriticalRange).''')

    return parser.parse_args(args)


def debugPrint(debug_flag, message):
    """
    Print debug messages if -d is set.
    """
    if not debug_flag:
        return

    print(message)

def verbosePrint(verbose_flag, when, message):
    """
    Print verbose messages if -v is set.
    Since -v can be used multiple times, the when parameter sets the required amount before printing
    """
    if not verbose_flag:
        return
    if verbose_flag >= when:
        print(message)

def prepare_context(args):
    """
    Prepare TLS Context
    """
    nagios = NagiosHelper()

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.options |= ssl.OP_NO_SSLv2
    context.options |= ssl.OP_NO_SSLv3

    if args.insecure:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    else:
        context.verify_mode = ssl.CERT_OPTIONAL
        context.load_default_certs()
        if args.cacert:
            try:
                context.load_verify_locations(args.cacert)
            except ssl.SSLError:
                nagios.append_message(UNKNOWN_CODE, 'Error loading SSL CA cert "%s"!' % args.cacert)
        if args.cert:
            try:
                context.load_cert_chain(args.cert, keyfile=args.key)
            except ssl.SSLError:
                if args.key:
                    nagios.append_message(UNKNOWN_CODE, 'Error loading SSL cert. Make sure key "%s" belongs to cert "%s"!' % (args.key, args.cert))
                else:
                    nagios.append_message(UNKNOWN_CODE, 'Error loading SSL cert. Make sure "%s" contains the key as well!' % (args.cert))

    if nagios.getCode() != OK_CODE:
        print(nagios.getMessage())
        sys.exit(nagios.getCode())

    return context


def make_request(args, url, context):
    """
    Performs the actual request to the given URL
    """
    req = urllib.request.Request(url, method=args.method)
    req.add_header("User-Agent", "check_http_json")
    if args.auth:
        authbytes = str(args.auth).encode()
        base64str = base64.encodebytes(authbytes).decode().replace('\n', '')
        req.add_header('Authorization', 'Basic %s' % base64str)
    if args.headers:
        headers = json.loads(args.headers)
        debugPrint(args.debug, "Headers:\n %s" % headers)
        for header in headers:
            req.add_header(header, headers[header])
    if args.timeout and args.data:
        databytes = str(args.data).encode()
        response = urllib.request.urlopen(req, timeout=args.timeout,
                                          data=databytes, context=context)
    elif args.timeout:
        response = urllib.request.urlopen(req, timeout=args.timeout,
                                          context=context)
    elif args.data:
        databytes = str(args.data).encode()
        response = urllib.request.urlopen(req, data=databytes, context=context)
    else:
        # pylint: disable=consider-using-with
        response = urllib.request.urlopen(req, context=context)

    return response.read()


def main(cliargs):
    """
    Main entrypoint for CLI
    """

    args = parseArgs(cliargs)
    nagios = NagiosHelper()
    context = None

    if args.version:
        print('Version: %s - Date: %s' % (__version__, __version_date__))
        sys.exit(0)

    if args.ssl:
        url = "https://%s" % args.host
        context = prepare_context(args)
    else:
        url = "http://%s" % args.host
    if args.port:
        url += ":%s" % args.port
    if args.path:
        url += "/%s" % args.path

    debugPrint(args.debug, "url: %s" % url)
    json_data = ''

    try:
        # Requesting the data from the URL
        json_data = make_request(args, url, context)
    except HTTPError as e:
        # Try to recover from HTTP Error, if there is JSON in the response
        if "json" in e.info().get_content_subtype():
            json_data = e.read()
        else:
            exit_code = args.invalid_json_state
            nagios.append_message(exit_code, " Could not find JSON in HTTP body. HTTPError[%s], url:%s" % (str(e.code), url))
    except URLError as e:
        # Some users might prefer another exit code if the URL wasn't reached
        exit_code = args.unreachable_state
        nagios.append_message(exit_code, " URLError[%s], url:%s" % (str(e.reason), url))
        # Since we don't got any data, we can simply exit
        print(nagios.getMessage())
        sys.exit(nagios.getCode())

    try:
        # Loading the JSON data from the request
        data = json.loads(json_data)
    except ValueError as e:
        exit_code = args.invalid_json_state
        debugPrint(args.debug, traceback.format_exc())
        nagios.append_message(exit_code, " JSON Parser error: %s" % str(e))
        print(nagios.getMessage())
        sys.exit(nagios.getCode())
    else:
        verbosePrint(args.verbose, 1, json.dumps(data, indent=2))

    try:
        # Applying rules to returned JSON data
        processor = JsonRuleProcessor(data, args)
        nagios.append_message(WARNING_CODE, processor.checkWarning())
        nagios.append_message(CRITICAL_CODE, processor.checkCritical())
        nagios.append_metrics(processor.checkMetrics())
        nagios.append_message(UNKNOWN_CODE, processor.checkUnknown())
    except Exception as e: # pylint: disable=broad-exception-caught
        debugPrint(args.debug, traceback.format_exc())
        nagios.append_message(UNKNOWN_CODE, " Rule Parser error: %s" % str(e))

    # Print Nagios specific string and exit appropriately
    print(nagios.getMessage())
    sys.exit(nagios.getCode())

if __name__ == "__main__":
    # Program entry point
    main(sys.argv[1:])

#EOF
