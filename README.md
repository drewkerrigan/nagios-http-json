![CI](https://github.com/drewkerrigan/nagios-http-json/workflows/CI/badge.svg)

# Nagios Json Plugin

This is a generic plugin for Nagios which checks json values from a given HTTP endpoint against argument specified rules and determines the status and performance data for that service.

## Installation

Requirements:

* Python 3.6+

### Nagios

Assuming a standard installation of Nagios, the plugin can be executed from the machine that Nagios is running on.

```bash
cp check_http_json.py /usr/local/nagios/libexec/plugins/check_http_json.py
chmod +x /usr/local/nagios/libexec/plugins/check_http_json.py
```

Add the following service definition to your server config (`localhost.cfg`):

```

define service {
        use                             local-service
        host_name                       localhost
        service_description             <command_description>
        check_command                   <command_name>
        }

```

Add the following command definition to your commands config (`commands.config`):

```

define command{
        command_name    <command_name>
        command_line    /usr/bin/python /usr/local/nagios/libexec/plugins/check_http_json.py -H <host>:<port> -p <path> [-e|-q|-w|-c <rules>] [-m <metrics>]
        }

```

### Icinga2

An example Icinga2 command definition can be found here: (`contrib/icinga2_check_command_definition.conf`)

## Usage

Executing `./check_http_json.py -h` will yield the following details:

```
usage: check_http_json.py [-h] [-d] [-s] -H HOST [-k] [-V] [--cacert CACERT]
                          [--cert CERT] [--key KEY] [-P PORT] [-p PATH]
                          [-t TIMEOUT] [-B AUTH] [-D DATA] [-A HEADERS]
                          [-f FIELD_SEPARATOR] [-F VALUE_SEPARATOR]
                          [-w [KEY_THRESHOLD_WARNING [KEY_THRESHOLD_WARNING ...]]]
                          [-c [KEY_THRESHOLD_CRITICAL [KEY_THRESHOLD_CRITICAL ...]]]
                          [-e [KEY_LIST [KEY_LIST ...]]]
                          [-E [KEY_LIST_CRITICAL [KEY_LIST_CRITICAL ...]]]
                          [-q [KEY_VALUE_LIST [KEY_VALUE_LIST ...]]]
                          [-Q [KEY_VALUE_LIST_CRITICAL [KEY_VALUE_LIST_CRITICAL ...]]]
                          [-u [KEY_VALUE_LIST_UNKNOWN [KEY_VALUE_LIST_UNKNOWN ...]]]
                          [-y [KEY_VALUE_LIST_NOT [KEY_VALUE_LIST_NOT ...]]]
                          [-Y [KEY_VALUE_LIST_NOT_CRITICAL [KEY_VALUE_LIST_NOT_CRITICAL ...]]]
                          [-m [METRIC_LIST [METRIC_LIST ...]]]

Check HTTP JSON Nagios Plugin

Generic Nagios plugin which checks json values from a given endpoint against
argument specified rules and determines the status and performance data for
that service.

Version: 2.2.0 (2024-05-14)

options:
  -h, --help            show this help message and exit
  -d, --debug           debug mode
  -v, --verbose         Verbose mode. Multiple -v options increase the verbosity
  -s, --ssl             use TLS to connect to remote host
  -H HOST, --host HOST  remote host to query
  -k, --insecure        do not check server SSL certificate
  -X {GET,POST}, --request {GET,POST}
                        Specifies a custom request method to use when communicating with the HTTP server
  -V, --version         print version of this plugin
  --cacert CACERT       SSL CA certificate
  --cert CERT           SSL client certificate
  --key KEY             SSL client key ( if not bundled into the cert )
  -P PORT, --port PORT  TCP port
  -p PATH, --path PATH  Path
  -t TIMEOUT, --timeout TIMEOUT
                        Connection timeout (seconds)
  --unreachable-state UNREACHABLE_STATE
                        Exit with specified code if URL unreachable. Examples: 1 for Warning, 2 for Critical, 3 for Unknown (default: 3)
  -B AUTH, --basic-auth AUTH
                        Basic auth string "username:password"
  -D DATA, --data DATA  The http payload to send as a POST
  -A HEADERS, --headers HEADERS
                        The http headers in JSON format.
  -f SEPARATOR, --field_separator SEPARATOR
                        JSON Field separator, defaults to "."; Select element in an array with "(" ")"
  -F VALUE_SEPARATOR, --value_separator VALUE_SEPARATOR
                        JSON Value separator, defaults to ":"
  -w [KEY_THRESHOLD_WARNING ...], --warning [KEY_THRESHOLD_WARNING ...]
                        Warning threshold for these values (key1[>alias],WarnRange key2[>alias],WarnRange). WarnRange is in the format
                        [@]start:end, more information at nagios-plugins.org/doc/guidelines.html.
  -c [KEY_THRESHOLD_CRITICAL ...], --critical [KEY_THRESHOLD_CRITICAL ...]
                        Critical threshold for these values (key1[>alias],CriticalRange key2[>alias],CriticalRange. CriticalRange is in
                        the format [@]start:end, more information at nagios-plugins.org/doc/guidelines.html.
  -e [KEY_LIST ...], --key_exists [KEY_LIST ...]
                        Checks existence of these keys to determine status. Return warning if key is not present.
  -E [KEY_LIST_CRITICAL ...], --key_exists_critical [KEY_LIST_CRITICAL ...]
                        Same as -e but return critical if key is not present.
  -q [KEY_VALUE_LIST ...], --key_equals [KEY_VALUE_LIST ...]
                        Checks equality of these keys and values (key[>alias],value key2,value2) to determine status. Multiple key values
                        can be delimited with colon (key,value1:value2). Return warning if equality check fails
  -Q [KEY_VALUE_LIST_CRITICAL ...], --key_equals_critical [KEY_VALUE_LIST_CRITICAL ...]
                        Same as -q but return critical if equality check fails.
  --key_time [KEY_TIME_LIST ...],
                        Checks a Timestamp of these keys and values
                        (key[>alias],value key2,value2) to determine status.
                        Multiple key values can be delimited with colon
                        (key,value1:value2). Return warning if the key is older
                        than the value (ex.: 30s,10m,2h,3d,...). 
                        With at it return warning if the key is jounger
                        than the value (ex.: @30s,@10m,@2h,@3d,...).
                        With Minus you can shift the time in the future.
  --key_time_critical [KEY_TIME_LIST_CRITICAL ...],
                        Same as --key_time but return critical if
                        Timestamp age fails.
  -u [KEY_VALUE_LIST_UNKNOWN ...], --key_equals_unknown [KEY_VALUE_LIST_UNKNOWN ...]
                        Same as -q but return unknown if equality check fails.
  -y [KEY_VALUE_LIST_NOT ...], --key_not_equals [KEY_VALUE_LIST_NOT ...]
                        Checks equality of these keys and values (key[>alias],value key2,value2) to determine status. Multiple key values
                        can be delimited with colon (key,value1:value2). Return warning if equality check succeeds
  -Y [KEY_VALUE_LIST_NOT_CRITICAL ...], --key_not_equals_critical [KEY_VALUE_LIST_NOT_CRITICAL ...]
                        Same as -q but return critical if equality check succeeds.
  -m [METRIC_LIST ...], --key_metric [METRIC_LIST ...]
                        Gathers the values of these keys (key[>alias], UnitOfMeasure,WarnRange,CriticalRange,Min,Max) for Nagios
                        performance data. More information about Range format and units of measure for nagios can be found at nagios-
                        plugins.org/doc/guidelines.html Additional formats for this parameter are: (key[>alias]),
                        (key[>alias],UnitOfMeasure), (key[>alias],UnitOfMeasure,WarnRange, CriticalRange).
```

The check plugin respects the environment variables `HTTP_PROXY`, `HTTPS_PROXY`.

## Examples

### Key Naming

**Data for key** `value`:

    { "value": 1000 }

**Data for key** `capacity.value`:

    {
        "capacity": {
            "value": 1000
        }
    }

**Data for key** `(0).capacity.value`:

    [
        {
            "capacity": {
                "value": 1000
            }
        }
    ]

**Data for keys of all items in a list** `(*).capacity.value`:

    [
        {
            "capacity": {
                "value": 1000
            }
        },
        {
            "capacity": {
                "value": 2200
            }
        }
    ]

**Data for separator** `-f _` **and key** `(0)_gauges_jvm.buffers.direct.capacity_value`:

    [
        {
            "gauges": {
                "jvm.buffers.direct.capacity":
                    "value": 1000
                }
            }
        }
    ]

**Data for keys** `ring_members(0)`, `ring_members(1)`, `ring_members(2)`:

    {
        "ring_members": [
            "riak1@127.0.0.1",
            "riak2@127.0.0.1",
            "riak3@127.0.0.1"
        ]
    }


**Data for multiple keys for an object** `-q capacity1.value,True capacity2.value,True capacity3.value,True`

    {
      "capacity1": {
        "value": true
      },
      "capacity2": {
        "value": true
      },
      "capacity3": {
        "value": true
      }
    }


### Thresholds and Ranges

**Data**:

    { "metric": 1000 }

#### Relevant Commands

* **Warning:** `./check_http_json.py -H <host>:<port> -p <path> -w "metric,RANGE"`
* **Critical:** `./check_http_json.py -H <host>:<port> -p <path> -c "metric,RANGE"`
* **Metrics with Warning:** `./check_http_json.py -H <host>:<port> -p <path> -w "metric,RANGE"`
* **Metrics with Critical:**

        ./check_http_json.py -H <host>:<port> -p <path> -w "metric,,,RANGE"
        ./check_http_json.py -H <host>:<port> -p <path> -w "metric,,,,MIN,MAX"

#### Range Definitions

* **Format:** [@]START:END
* **Generates a Warning or Critical if...**
    * **Value is less than 0 or greater than 1000:** `1000` or `0:1000`
    * **Value is greater than or equal to 1000, or less than or equal to 0:** `@1000` or `@0:1000`
    * **Value is less than 1000:** `1000:`
    * **Value is greater than 1000:** `~:1000`
    * **Value is greater than or equal to 1000:** `@1000:`

More info about Nagios Range format and Units of Measure can be found at [https://nagios-plugins.org/doc/guidelines.html](https://nagios-plugins.org/doc/guidelines.html).

### Timestamp

**Data**:

    { "metric": "2020-01-01 10:10:00.000000+00:00" }

#### Relevant Commands

* **Warning:** `./check_http_json.py -H <host>:<port> -p <path> --key_time "metric,TIME"`
* **Critical:** `./check_http_json.py -H <host>:<port> -p <path> --key_time_critical "metric,TIME"`

#### TIME Definitions

* **Format:** [@][-]TIME
* **Generates a Warning or Critical if...**
    * **Timestamp is more than 30 seconds in the past:** `30s`
    * **Timestamp is more than 5 minutes in the past:** `5m`
    * **Timestamp is more than 12 hours in the past:** `12h`
    * **Timestamp is more than 2 days in the past:** `2d`
    * **Timestamp is more than 30 minutes in the future:** `-30m`
    * **Timestamp is not more than 30 minutes in the future:** `@-30m`
    * **Timestamp is not more than 30 minutes in the past:** `@30m`

##### Timestamp Format

This plugin uses the Python function 'datetime.fromisoformat'.
Since Python 3.11 any valid ISO 8601 format is supported, with the following exceptions:

* Time zone offsets may have fractional seconds.
* The T separator may be replaced by any single unicode character.
* Fractional hours and minutes are not supported.
* Reduced precision dates are not currently supported (YYYY-MM, YYYY).
* Extended date representations are not currently supported (±YYYYYY-MM-DD).
* Ordinal dates are not currently supported (YYYY-OOO).

Before Python 3.11, this method only supported the format YYYY-MM-DD

More info and examples the about Timestamp Format can be found at [https://docs.python.org/3/library/datetime.html#datetime.datetime.fromisoformat](https://docs.python.org/3/library/datetime.html#datetime.datetime.fromisoformat).

#### Using Headers

* `./check_http_json.py -H <host>:<port> -p <path> -A '{"content-type": "application/json"}' -w "metric,RANGE"`

## License

    Copyright 2014-2015 Drew Kerrigan.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
