#!/usr/bin/python

"""
Check HTTP JSON Nagios Plugin

Generic Nagios plugin which checks json values from a given endpoint against argument specified rules
and determines the status and performance data for that service.
"""

import httplib, urllib, urllib2, base64
import json
import sys
import argparse
from pprint import pprint
from urllib2 import HTTPError
from urllib2 import URLError


class NagiosHelper:
	"""Help with Nagios specific status string formatting."""
	code = 0
	message_prefixes = {0: 'OK', 1: 'WARNING', 2: 'CRITICAL', 3: 'UNKNOWN'}
	message_text = ''
	performance_data = ''

	def getMessage(self):
		"""Build a status-prefixed message with optional performance data generated externally"""
		text = "%s" % self.message_prefixes[self.code]
		if self.message_text:
			text += ": %s" % self.message_text
		if self.performance_data:
			text += "|%s" % self.performance_data
		return text

	def setCodeAndMessage(self, code, text):
		self.code = code
		self.message_text = text

	def ok(self, text): self.setCodeAndMessage(0, text)
	def warning(self, text): self.setCodeAndMessage(1, text)
	def critical(self, text): self.setCodeAndMessage(2, text)
	def unknown(self, text): self.setCodeAndMessage(3, text)

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
	def gte(self, key, value): return self.exists(key) and float(self.get(key)) >= float(value)
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

class JsonRuleProcessor:
	"""Perform checks and gather values from a JSON dict given rules and metrics definitions"""
	def __init__(self, json_data, rules_args):
		self.data = json_data
		self.rules = rules_args
		separator = '.'
		if self.rules.separator: separator = self.rules.separator
		self.helper = JsonHelper(self.data, separator)

		debugPrint(rules_args.debug, "separator:%s" % separator)

	def isAlive(self):
		"""Return a tuple with liveness and reason for not liveness given existence, equality, and comparison rules"""
		reason = ''

		if self.rules.key_list != None:
			for k in self.rules.key_list:
				if (self.helper.exists(k) == False):
					reason += " Key %s did not exist." % k

		if self.rules.key_value_list != None:
			for kv in self.rules.key_value_list:
				k, v = kv.split(',')
				if (self.helper.equals(k, v) == False):
					reason += " Value %s for key %s did not match." % (v, k)

		if self.rules.key_lte_list != None:
			for kv in self.rules.key_lte_list:
				k, v = kv.split(',')
				if (self.helper.lte(k, v) == False):
					reason += " Value %s was not less than or equal to value for key %s." % (v, k)

		if self.rules.key_gte_list != None:
			for kv in self.rules.key_gte_list:
				k, v = kv.split(',')
				if (self.helper.gte(k, v) == False):
					reason += " Value %s was not greater than or equal to value for key %s." % (v, k)

		is_alive = (reason == '')

		return (is_alive, reason)

	def getMetrics(self):
		"""Return a Nagios specific performance metrics string given keys and parameter definitions"""
		metrics = ''

		if self.rules.metric_list != None:
			for metric in self.rules.metric_list:
				key = metric
				minimum = maximum = warn_range = crit_range = 0
				uom = ''

				if ',' in metric:
					vals = metric.split(',')

					if len(vals) == 2:
						key,uom = vals
					if len(vals) == 4:
						key,uom,minimum,maximum = vals
					if len(vals) == 6:
						key,uom,minimum,maximum,warn_range,crit_range = vals

				if self.helper.exists(key):
					metrics += "'%s'=%s" % (key, self.helper.get(key))
					if uom: metrics += uom
					metrics += ";%s" % minimum
					metrics += ";%s" % maximum
					if warn_range: metrics += ";%s" % warn_range
					if crit_range: metrics += ";%s" % crit_range

				metrics += ' '


		return "%s" % metrics

def parseArgs():
	parser = argparse.ArgumentParser(description=
			'Nagios plugin which checks json values from a given endpoint against argument specified rules\
			and determines the status and performance data for that service')

	parser.add_argument('-H', '--host', dest='host', default='localhost', help='Host.')
	parser.add_argument('-P', '--port', dest='port', help='TCP port')
	parser.add_argument('-B', '--basic-auth', dest='auth', help='Basic auth string "username:password"')
	parser.add_argument('-p', '--path', dest='path', help='Path.')
	parser.add_argument('-D', '--data', dest='data', help='The http payload to send as a POST')
	parser.add_argument('-e', '--key_exists', dest='key_list', nargs='*',
		help='Checks existence of these keys to determine status.')
	parser.add_argument('-q', '--key_equals', dest='key_value_list', nargs='*',
		help='Checks equality of these keys and values (key,value key2,value2) to determine status.\
		Multiple key values can be delimited with colon (key,value1:value2)')
	parser.add_argument('-l', '--key_lte', dest='key_lte_list', nargs='*',
		help='Checks that these keys and values (key,value key2,value2) are less than or equal to\
		the returned json value to determine status.')
	parser.add_argument('-g', '--key_gte', dest='key_gte_list', nargs='*',
		help='Checks that these keys and values (key,value key2,value2) are greater than or equal to\
		the returned json value to determine status.')
	parser.add_argument('-m', '--key_metric', dest='metric_list', nargs='*',
		help='Gathers the values of these keys (key,UnitOfMeasure,Min,Max,WarnRange,CriticalRange) for Nagios performance data.\
		More information about Range format and units of measure for nagios can be found at https://nagios-plugins.org/doc/guidelines.html\
		Additional formats for this parameter are: (key), (key,UnitOfMeasure), (key,UnitOfMeasure,Min,Max).')
	parser.add_argument('-s', '--ssl', action='store_true', help='HTTPS mode.')
	parser.add_argument('-t', '--timeout', type=int, help='Connection timeout (seconds)')
	parser.add_argument('-f', '--field_separator', dest='separator', help='Json Field separator, defaults to "." ; Select element in an array with "(" ")"')
	parser.add_argument('-d', '--debug', action='store_true', help='Debug mode.')

	if len(sys.argv) == 1:
		parser.print_help()
		exit(0)
	else:
		return parser.parse_args()

def debugPrint(debug_flag, message, pretty_flag=False):
	if debug_flag:
		if pretty_flag:
			pprint(message)
		else:
			print message

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
		if args.timeout and args.data:
			response = urllib2.urlopen(req, timeout=args.timeout, data=args.data)
		elif args.timeout:
			response = urllib2.urlopen(req, timeout=args.timeout)
		elif args.data:
			response = urllib2.urlopen(req, data=args.data)
		else:
			response = urllib2.urlopen(req)
	except HTTPError as e:
		nagios.unknown("HTTPError[%s], url:%s" % (str(e.code), url))
	except URLError as e:
		nagios.critical("URLError[%s], url:%s" % (str(e.reason), url))
	else:
		jsondata = response.read()
		data = json.loads(jsondata)

		debugPrint(args.debug, 'json:')
		debugPrint(args.debug, data, True)

		# Apply rules to returned JSON data
		processor = JsonRuleProcessor(data, args)
		is_alive, reason = processor.isAlive()

		# Gather metrics for display
		nagios.performance_data = processor.getMetrics()

		if is_alive:
			nagios.ok("Status OK.")
		else:
			nagios.warning("Status check failed, reason:%s" % reason)

	# Print Nagios specific string and exit appropriately
	print nagios.getMessage()
	exit(nagios.code)
