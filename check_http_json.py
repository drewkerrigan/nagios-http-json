#!/usr/bin/python

"""
Check HTTP JSON Nagios Plugin

Generic Nagios plugin which checks json values from a given endpoint against argument specified rules
and determines the status and performance data for that service.
"""

import httplib, urllib, urllib2, base64
import json
import argparse
import sys
from pprint import pprint
from urllib2 import HTTPError
from urllib2 import URLError

# TEST = False


OK_CODE = 0
WARNING_CODE = 1
CRITICAL_CODE = 2
UNKNOWN_CODE = 3

class NagiosHelper:
	"""Help with Nagios specific status string formatting."""
	message_prefixes = {OK_CODE: 'OK', WARNING_CODE: 'WARNING', CRITICAL_CODE: 'CRITICAL', UNKNOWN_CODE: 'UNKNOWN'}
	performance_data = ''
	warning_message = ''
	critical_message = ''
	unknown_message = ''

	def getMessage(self):
		"""Build a status-prefixed message with optional performance data generated externally"""
		text = "%s: Status %s." % (self.message_prefixes[self.getCode()], self.message_prefixes[self.getCode()])
		text += self.warning_message
		text += self.critical_message
		text += self.unknown_message
		if self.performance_data:
			text += "|%s" % self.performance_data
		return text

	def getCode(self):
		code = OK_CODE
		if (self.warning_message != ''):
			code = WARNING_CODE
		if (self.critical_message != ''):
			code = CRITICAL_CODE
		if (self.unknown_message != ''):
			code = UNKNOWN_CODE
		return code

	def append_warning(self, warning_message):
		self.warning_message += warning_message
	def append_critical(self, critical_message):
		self.critical_message += critical_message
	def append_unknown(self, unknown_message):
		self.critical_message += unknown_message
	def append_metrics(self, (performance_data, warning_message, critical_message)):
		self.performance_data += performance_data
		self.append_warning(warning_message)
		self.append_critical(critical_message)

class JsonHelper:
	"""Perform simple comparison operations against values in a given JSON dict"""
	def __init__(self, json_data, separator):
		self.data = json_data
		self.separator = separator
		self.arrayOpener = '('
		self.arrayCloser = ')'

	def getSubElement(self, key, data):
		separatorIndex = key.find(self.separator)
		partialKey = key[:separatorIndex]
		remainingKey = key[separatorIndex + 1:]
		if partialKey in data:
			return self.get(remainingKey, data[partialKey])
		else:
			return (None, 'not_found')

	def getSubArrayElement(self, key, data):
		subElemKey = key[:key.find(self.arrayOpener)]
		index = int(key[key.find(self.arrayOpener) + 1:key.find(self.arrayCloser)])
		remainingKey = key[key.find(self.arrayCloser + self.separator) + 2:]
		if key.find(self.arrayCloser + self.separator) == -1:
			remainingKey = key[key.find(self.arrayCloser) + 1:]
		if subElemKey in data:
			if index < len(data[subElemKey]):
				return self.get(remainingKey, data[subElemKey][index])
			else:
				return (None, 'not_found')
		else:
			if not subElemKey:
				return self.get(remainingKey, data[index])
			else:
				return (None, 'not_found')

	def equals(self, key, value): return self.exists(key) and str(self.get(key)) in value.split(':')
	def lte(self, key, value): return self.exists(key) and float(self.get(key)) <= float(value)
	def lt(self, key, value): return self.exists(key) and float(self.get(key)) < float(value)
	def gte(self, key, value): return self.exists(key) and float(self.get(key)) >= float(value)
	def gt(self, key, value): return self.exists(key) and float(self.get(key)) > float(value)
	def exists(self, key): return (self.get(key) != (None, 'not_found'))
	def get(self, key, temp_data=''):
		"""Can navigate nested json keys with a dot format (Element.Key.NestedKey). Returns (None, 'not_found') if not found"""
		if temp_data:
			data = temp_data
		else:
			data = self.data
		if len(key) <= 0:
			return data
		if key.find(self.separator) != -1 and key.find(self.arrayOpener) != -1 :
			if key.find(self.separator) < key.find(self.arrayOpener) :
				return self.getSubElement(key, data)
			else:
				return self.getSubArrayElement(key, data)
		else:
			if key.find(self.separator) != -1 :
				return self.getSubElement(key, data)
			else:
				if key.find(self.arrayOpener) != -1 :
					return self.getSubArrayElement(key, data)
				else:
					if key in data:
						return data[key]
					else:
						return (None, 'not_found')

def _getKeyAlias(original_key):
	key = original_key
	alias = original_key
	if '>' in original_key:
		keys = original_key.split('>')
		if len(keys) == 2:
			key, alias = keys
	return key, alias

class JsonRuleProcessor:
	"""Perform checks and gather values from a JSON dict given rules and metrics definitions"""
	def __init__(self, json_data, rules_args):
		self.data = json_data
		self.rules = rules_args
		separator = '.'
		if self.rules.separator: separator = self.rules.separator
		self.helper = JsonHelper(self.data, separator)
		debugPrint(rules_args.debug, "rules:%s" % rules_args)
		debugPrint(rules_args.debug, "separator:%s" % separator)

	def checkExists(self, exists_list):
		failure = ''
		for k in exists_list:
			key, alias = _getKeyAlias(k)
			if (self.helper.exists(key) == False):
				failure += " Key %s did not exist." % alias
		return failure

	def checkEquality(self, equality_list):
		failure = ''
		for kv in equality_list:
			k, v = kv.split(',')
			key, alias = _getKeyAlias(k)
			if (self.helper.equals(key, v) == False):
				failure += " Value for key %s did not match %s." % (alias, v)
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
				failure += " Value for key %s was less than or equal to %s." % (alias, end)
			elif (not invert and self.helper.gt(key, end)):
				failure += " Value for key %s was greater than %s." % (alias, end)
		elif(end == 'infinity'):
			if (invert and self.helper.gte(key, start)):
				failure += " Value for key %s was greater than or equal to %s." % (alias, start)
			elif (not invert and self.helper.lt(key, start)):
				failure += " Value for key %s was less than %s." % (alias, start)
		else:
			if (invert and self.helper.gte(key, start) and self.helper.lte(key, end)):
				failure += " Value for key %s was inside the range %s:%s." % (alias, start, end)
			elif (not invert and (self.helper.lt(key, start) or self.helper.gt(key, end))):
				failure += " Value for key %s was outside the range %s:%s." % (alias, start, end)
		return failure

	def checkThresholds(self, threshold_list):
		failure = ''
		for threshold in threshold_list:
			k, r = threshold.split(',')
			key, alias = _getKeyAlias(k)
			failure += self.checkThreshold(key, alias, r)
		return failure

	def checkWarning(self):
		failure = ''
		if self.rules.key_threshold_warning != None:
			failure += self.checkThresholds(self.rules.key_threshold_warning)
		if self.rules.key_value_list != None:
			failure += self.checkEquality(self.rules.key_value_list)
		if self.rules.key_list != None:
			failure += self.checkExists(self.rules.key_list)
		return failure

	def checkCritical(self):
		failure = ''
		if self.rules.key_threshold_critical != None:
			failure += self.checkThresholds(self.rules.key_threshold_critical)
		if self.rules.key_value_list_critical != None:
			failure += self.checkEquality(self.rules.key_value_list_critical)
		if self.rules.key_list_critical != None:
			failure += self.checkExists(self.rules.key_list_critical)
		return failure

	def checkMetrics(self):
		"""Return a Nagios specific performance metrics string given keys and parameter definitions"""
		metrics = ''
		warning = ''
		critical = ''
		if self.rules.metric_list != None:
			for metric in self.rules.metric_list:
				key = metric
				minimum = maximum = warn_range = crit_range = None
				uom = ''
				if ',' in metric:
					vals = metric.split(',')
					if len(vals) == 2:
						key,uom = vals
					if len(vals) == 4:
						key,uom,warn_range,crit_range = vals
					if len(vals) == 6:
						key,uom,warn_range,crit_range,minimum,maximum = vals
				key, alias = _getKeyAlias(key)
				if self.helper.exists(key):
					metrics += "'%s'=%s" % (alias, self.helper.get(key))
					if uom: metrics += uom
					if warn_range != None:
						warning += self.checkThreshold(key, alias, warn_range)
						metrics += ";%s" % warn_range
					if crit_range != None:
						critical += self.checkThreshold(key, alias, crit_range)
						metrics += ";%s" % crit_range
					if minimum != None:
						critical += self.checkThreshold(key, alias, minimum + ':')
						metrics += ";%s" % minimum
					if maximum != None:
						critical += self.checkThreshold(key, alias, '~:' + maximum)
						metrics += ";%s" % maximum
				metrics += ' '
		return ("%s" % metrics, warning, critical)

def parseArgs():
	parser = argparse.ArgumentParser(description=
			'Nagios plugin which checks json values from a given endpoint against argument specified rules\
			and determines the status and performance data for that service')

    # parser.add_argument('-v', '--verbose', action='store_true', help='Verbose Output')
	parser.add_argument('-d', '--debug', action='store_true', help='Debug mode.')
	parser.add_argument('-s', '--ssl', action='store_true', help='HTTPS mode.')
	parser.add_argument('-H', '--host', dest='host', required=True, help='Host.')
	parser.add_argument('-P', '--port', dest='port', help='TCP port')
	parser.add_argument('-p', '--path', dest='path', help='Path.')
	parser.add_argument('-t', '--timeout', type=int, help='Connection timeout (seconds)')
	parser.add_argument('-B', '--basic-auth', dest='auth', help='Basic auth string "username:password"')
	parser.add_argument('-D', '--data', dest='data', help='The http payload to send as a POST')
	parser.add_argument('-A', '--headers', dest='headers', help='The http headers in JSON format.')
	parser.add_argument('-f', '--field_separator', dest='separator',
		help='Json Field separator, defaults to "." ; Select element in an array with "(" ")"')
	parser.add_argument('-w', '--warning', dest='key_threshold_warning', nargs='*',
		help='Warning threshold for these values (key1[>alias],WarnRange key2[>alias],WarnRange). WarnRange is in the format [@]start:end, more information at nagios-plugins.org/doc/guidelines.html.')
	parser.add_argument('-c', '--critical', dest='key_threshold_critical', nargs='*',
		help='Critical threshold for these values (key1[>alias],CriticalRange key2[>alias],CriticalRange. CriticalRange is in the format [@]start:end, more information at nagios-plugins.org/doc/guidelines.html.')
	parser.add_argument('-e', '--key_exists', dest='key_list', nargs='*',
		help='Checks existence of these keys to determine status. Return warning if key is not present.')
	parser.add_argument('-E', '--key_exists_critical', dest='key_list_critical', nargs='*',
		help='Same as -e but return critical if key is not present.')
	parser.add_argument('-q', '--key_equals', dest='key_value_list', nargs='*',
		help='Checks equality of these keys and values (key[>alias],value key2,value2) to determine status.\
		Multiple key values can be delimited with colon (key,value1:value2). Return warning if equality check fails')
	parser.add_argument('-Q', '--key_equals_critical', dest='key_value_list_critical', nargs='*',
		help='Same as -q but return critical if equality check fails.')
	parser.add_argument('-m', '--key_metric', dest='metric_list', nargs='*',
		help='Gathers the values of these keys (key[>alias],UnitOfMeasure,WarnRange,CriticalRange,Min,Max) for Nagios performance data.\
		More information about Range format and units of measure for nagios can be found at nagios-plugins.org/doc/guidelines.html\
		Additional formats for this parameter are: (key[>alias]), (key[>alias],UnitOfMeasure), (key[>alias],UnitOfMeasure,WarnRange,CriticalRange).')

	return parser.parse_args()

def debugPrint(debug_flag, message, pretty_flag=False):
	if debug_flag:
		if pretty_flag:
			pprint(message)
		else:
			print message

if __name__ == "__main__" and len(sys.argv) >= 2 and sys.argv[1] == 'UnitTest':
	import unittest
	class RulesHelper:
		separator = '.'
		debug = False
		key_threshold_warning,key_value_list,key_list,key_threshold_critical,key_value_list_critical,key_list_critical,metric_list = None, None, None, None, None, None, None
		def dash_m(self, data):
			self.metric_list = data; return self
		def dash_e(self, data):
			self.key_list = data; return self
		def dash_E(self, data):
			self.key_list_critical = data; return self
		def dash_q(self, data):
			self.key_value_list = data; return self
		def dash_Q(self, data):
			self.key_value_list_critical = data; return self
		def dash_w(self, data):
			self.key_threshold_warning = data; return self
		def dash_c(self, data):
			self.key_threshold_critical = data; return self
	class UnitTest(unittest.TestCase):
		rules = RulesHelper()
		def check_data(self, args, jsondata, code):
			data = json.loads(jsondata)
			nagios = NagiosHelper()
			processor = JsonRuleProcessor(data, args)
			nagios.append_warning(processor.checkWarning())
			nagios.append_critical(processor.checkCritical())
			nagios.append_metrics(processor.checkMetrics())
			self.assertEqual(code, nagios.getCode())
		def test_metrics(self):
			self.check_data(RulesHelper().dash_m(['metric,,1:4,1:5']), '{"metric": 5}', WARNING_CODE)
			self.check_data(RulesHelper().dash_m(['metric,,1:5,1:4']), '{"metric": 5}', CRITICAL_CODE)
			self.check_data(RulesHelper().dash_m(['metric,,1:5,1:5,6,10']), '{"metric": 5}', CRITICAL_CODE)
			self.check_data(RulesHelper().dash_m(['metric,,1:5,1:5,1,4']), '{"metric": 5}', CRITICAL_CODE)
			self.check_data(RulesHelper().dash_m(['metric,s,@1:4,@6:10,1,10']), '{"metric": 5}', OK_CODE)
		def test_exists(self):
			self.check_data(RulesHelper().dash_e(['nothere']), '{"metric": 5}', WARNING_CODE)
			self.check_data(RulesHelper().dash_E(['nothere']), '{"metric": 5}', CRITICAL_CODE)
			self.check_data(RulesHelper().dash_e(['metric']), '{"metric": 5}', OK_CODE)
		def test_equality(self):
			self.check_data(RulesHelper().dash_q(['metric,6']), '{"metric": 5}', WARNING_CODE)
			self.check_data(RulesHelper().dash_Q(['metric,6']), '{"metric": 5}', CRITICAL_CODE)
			self.check_data(RulesHelper().dash_q(['metric,5']), '{"metric": 5}', OK_CODE)
		def test_warning_thresholds(self):
			self.check_data(RulesHelper().dash_w(['metric,5']), '{"metric": 5}', OK_CODE)
			self.check_data(RulesHelper().dash_w(['metric,5:']), '{"metric": 5}', OK_CODE)
			self.check_data(RulesHelper().dash_w(['metric,~:5']), '{"metric": 5}', OK_CODE)
			self.check_data(RulesHelper().dash_w(['metric,1:5']), '{"metric": 5}', OK_CODE)
			self.check_data(RulesHelper().dash_w(['metric,@5']), '{"metric": 6}', OK_CODE)
			self.check_data(RulesHelper().dash_w(['metric,@5:']), '{"metric": 4}', OK_CODE)
			self.check_data(RulesHelper().dash_w(['metric,@~:5']), '{"metric": 6}', OK_CODE)
			self.check_data(RulesHelper().dash_w(['metric,@1:5']), '{"metric": 6}', OK_CODE)
			self.check_data(RulesHelper().dash_w(['metric,5']), '{"metric": 6}', WARNING_CODE)
			self.check_data(RulesHelper().dash_w(['metric,5:']), '{"metric": 4}', WARNING_CODE)
			self.check_data(RulesHelper().dash_w(['metric,~:5']), '{"metric": 6}', WARNING_CODE)
			self.check_data(RulesHelper().dash_w(['metric,1:5']), '{"metric": 6}', WARNING_CODE)
			self.check_data(RulesHelper().dash_w(['metric,@5']), '{"metric": 5}', WARNING_CODE)
			self.check_data(RulesHelper().dash_w(['metric,@5:']), '{"metric": 5}', WARNING_CODE)
			self.check_data(RulesHelper().dash_w(['metric,@~:5']), '{"metric": 5}', WARNING_CODE)
			self.check_data(RulesHelper().dash_w(['metric,@1:5']), '{"metric": 5}', WARNING_CODE)
		def test_critical_thresholds(self):
			self.check_data(RulesHelper().dash_c(['metric,5']), '{"metric": 5}', OK_CODE)
			self.check_data(RulesHelper().dash_c(['metric,5:']), '{"metric": 5}', OK_CODE)
			self.check_data(RulesHelper().dash_c(['metric,~:5']), '{"metric": 5}', OK_CODE)
			self.check_data(RulesHelper().dash_c(['metric,1:5']), '{"metric": 5}', OK_CODE)
			self.check_data(RulesHelper().dash_c(['metric,@5']), '{"metric": 6}', OK_CODE)
			self.check_data(RulesHelper().dash_c(['metric,@5:']), '{"metric": 4}', OK_CODE)
			self.check_data(RulesHelper().dash_c(['metric,@~:5']), '{"metric": 6}', OK_CODE)
			self.check_data(RulesHelper().dash_c(['metric,@1:5']), '{"metric": 6}', OK_CODE)
			self.check_data(RulesHelper().dash_c(['metric,5']), '{"metric": 6}', CRITICAL_CODE)
			self.check_data(RulesHelper().dash_c(['metric,5:']), '{"metric": 4}', CRITICAL_CODE)
			self.check_data(RulesHelper().dash_c(['metric,~:5']), '{"metric": 6}', CRITICAL_CODE)
			self.check_data(RulesHelper().dash_c(['metric,1:5']), '{"metric": 6}', CRITICAL_CODE)
			self.check_data(RulesHelper().dash_c(['metric,@5']), '{"metric": 5}', CRITICAL_CODE)
			self.check_data(RulesHelper().dash_c(['metric,@5:']), '{"metric": 5}', CRITICAL_CODE)
			self.check_data(RulesHelper().dash_c(['metric,@~:5']), '{"metric": 5}', CRITICAL_CODE)
			self.check_data(RulesHelper().dash_c(['metric,@1:5']), '{"metric": 5}', CRITICAL_CODE)
		def test_separator(self):
			rules = RulesHelper()
			rules.separator = '_'
			self.check_data(
				rules.dash_q(['(0)_gauges_jvm.buffers.direct.capacity(1)_value,1234']),
				'[{ "gauges": { "jvm.buffers.direct.capacity": [{"value": 215415},{"value": 1234}]}}]',
				OK_CODE)
	unittest.main()
	exit(0)

"""Program entry point"""
if __name__ == "__main__":
	args = parseArgs()
	nagios = NagiosHelper()
	if args.ssl:
		url = "https://%s" % args.host
	else:
		url = "http://%s" % args.host
	if args.port: url += ":%s" % args.port
	if args.path: url += "/%s" % args.path
	debugPrint(args.debug, "url:%s" % url)
	# Attempt to reach the endpoint
	try:
		req = urllib2.Request(url)
		if args.auth:
			base64str = base64.encodestring(args.auth).replace('\n', '')
			req.add_header('Authorization', 'Basic %s' % base64str)
		if args.headers:
			headers=json.loads(args.headers)
			debugPrint(args.debug, "Headers:\n %s" % headers)
			for header in headers:
				req.add_header(header, headers[header])
		if args.timeout and args.data:
			response = urllib2.urlopen(req, timeout=args.timeout, data=args.data)
		elif args.timeout:
			response = urllib2.urlopen(req, timeout=args.timeout)
		elif args.data:
			response = urllib2.urlopen(req, data=args.data)
		else:
			response = urllib2.urlopen(req)
	except HTTPError as e:
		nagios.append_unknown("HTTPError[%s], url:%s" % (str(e.code), url))
	except URLError as e:
		nagios.append_critical("URLError[%s], url:%s" % (str(e.reason), url))
	else:
		jsondata = response.read()
		data = json.loads(jsondata)
		debugPrint(args.debug, 'json:')
		debugPrint(args.debug, data, True)
		# Apply rules to returned JSON data
		processor = JsonRuleProcessor(data, args)
		nagios.append_warning(processor.checkWarning())
		nagios.append_critical(processor.checkCritical())
		nagios.append_metrics(processor.checkMetrics())
	# Print Nagios specific string and exit appropriately
	print nagios.getMessage()
	exit(nagios.getCode())
