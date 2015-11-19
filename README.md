# Nagios Json Plugin

This is a generic plugin for Nagios which checks json values from a given HTTP endpoint against argument specified rules and determines the status and performance data for that service.

### Installation

#### Requirements

* Nagios
* Python

### Nagios Configuration

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

More info about options in Usage.

### CLI Usage

Executing `./check_http_json.py -h` will yield the following details:

```
usage: check_http_json.py [-h] [-d] [-s] -H HOST [-P PORT] [-p PATH]
                          [-t TIMEOUT] [-B AUTH] [-D DATA] [-f SEPARATOR]
                          [-w [KEY_THRESHOLD_WARNING [KEY_THRESHOLD_WARNING ...]]]
                          [-c [KEY_THRESHOLD_CRITICAL [KEY_THRESHOLD_CRITICAL ...]]]
                          [-e [KEY_LIST [KEY_LIST ...]]]
                          [-E [KEY_LIST_CRITICAL [KEY_LIST_CRITICAL ...]]]
                          [-q [KEY_VALUE_LIST [KEY_VALUE_LIST ...]]]
                          [-Q [KEY_VALUE_LIST_CRITICAL [KEY_VALUE_LIST_CRITICAL ...]]]
                          [-m [METRIC_LIST [METRIC_LIST ...]]]

Nagios plugin which checks json values from a given endpoint against argument
specified rules and determines the status and performance data for that
service

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Debug mode.
  -s, --ssl             HTTPS mode.
  -H HOST, --host HOST  Host.
  -P PORT, --port PORT  TCP port
  -p PATH, --path PATH  Path.
  -t TIMEOUT, --timeout TIMEOUT
                        Connection timeout (seconds)
  -B AUTH, --basic-auth AUTH
                        Basic auth string "username:password"
  -D DATA, --data DATA  The http payload to send as a POST
  -f SEPARATOR, --field_separator SEPARATOR
                        Json Field separator, defaults to "." ; Select element
                        in an array with "(" ")"
  -w [KEY_THRESHOLD_WARNING [KEY_THRESHOLD_WARNING ...]], --warning [KEY_THRESHOLD_WARNING [KEY_THRESHOLD_WARNING ...]]
                        Warning threshold for these values
                        (key1[>alias],WarnRange key2[>alias],WarnRange).
                        WarnRange is in the format [@]start:end, more
                        information at nagios-plugins.org/doc/guidelines.html.
  -c [KEY_THRESHOLD_CRITICAL [KEY_THRESHOLD_CRITICAL ...]], --critical [KEY_THRESHOLD_CRITICAL [KEY_THRESHOLD_CRITICAL ...]]
                        Critical threshold for these values
                        (key1[>alias],CriticalRange
                        key2[>alias],CriticalRange. CriticalRange is in the
                        format [@]start:end, more information at nagios-
                        plugins.org/doc/guidelines.html.
  -e [KEY_LIST [KEY_LIST ...]], --key_exists [KEY_LIST [KEY_LIST ...]]
                        Checks existence of these keys to determine status.
                        Return warning if key is not present.
  -E [KEY_LIST_CRITICAL [KEY_LIST_CRITICAL ...]], --key_exists_critical [KEY_LIST_CRITICAL [KEY_LIST_CRITICAL ...]]
                        Same as -e but return critical if key is not present.
  -q [KEY_VALUE_LIST [KEY_VALUE_LIST ...]], --key_equals [KEY_VALUE_LIST [KEY_VALUE_LIST ...]]
                        Checks equality of these keys and values
                        (key[>alias],value key2,value2) to determine status.
                        Multiple key values can be delimited with colon
                        (key,value1:value2). Return warning if equality check
                        fails
  -Q [KEY_VALUE_LIST_CRITICAL [KEY_VALUE_LIST_CRITICAL ...]], --key_equals_critical [KEY_VALUE_LIST_CRITICAL [KEY_VALUE_LIST_CRITICAL ...]]
                        Same as -q but return critical if equality check
                        fails.
  -m [METRIC_LIST [METRIC_LIST ...]], --key_metric [METRIC_LIST [METRIC_LIST ...]]
                        Gathers the values of these keys (key[>alias],UnitOfMe
                        asure,WarnRange,CriticalRange,Min,Max) for Nagios
                        performance data. More information about Range format
                        and units of measure for nagios can be found at
                        nagios-plugins.org/doc/guidelines.html Additional
                        formats for this parameter are: (key[>alias]),
                        (key[>alias],UnitOfMeasure),
                        (key[>alias],UnitOfMeasure,WarnRange,CriticalRange).
```

Access a specific JSON field by following this syntax: `alpha.beta.gamma(3).theta.omega(0)`
Dots are field separators (changeable), parentheses are for entering arrays.

If the root of the JSON data is itself an array like the following:

```
[
{ "gauges": { "jvm.buffers.direct.capacity": {"value": 215415}}}
]
```

The beginning of the key should start with ($index) as in this example:

```
./check_http_json.py -H localhost:8081 -p metrics --key_exists "(0)_gauges_jvm.buffers.direct.capacity_value" -f _
```

More info about Nagios Range format and Units of Measure can be found at [https://nagios-plugins.org/doc/guidelines.html](https://nagios-plugins.org/doc/guidelines.html).

### Docker Info Example Plugin

#### Description

Let's say we want to use `check_http_json.py` to read from Docker's `/info` HTTP API endpoint with the following parameters:

##### Connection information

* Host = 127.0.0.1:4243
* Path = /info

##### Rules for "aliveness"

* Verify that the key `Containers` exists in the outputted JSON
* Verify that the key `IPv4Forwarding` has a value of `1`
* Verify that the key `Debug` has a value less than or equal to `2`
* Verify that the key `Images` has a value greater than or equal to `1`
* If any of these criteria are not met, report a WARNING to Nagios

##### Gather Metrics

* Report value of the key `Containers` with a MinValue of 0 and a MaxValue of 1000 as performance data
* Report value of the key `Images` as performance data
* Report value of the key `NEventsListener` as performance data
* Report value of the key `NFd` as performance data
* Report value of the key `NGoroutines` as performance data
* Report value of the key `SwapLimit` as performance data

#### Service Definition

`localhost.cfg`

```
define service {
        use                             local-service
        host_name                       localhost
        service_description             Docker info status checker
        check_command                   check_docker
        }
```

#### Command Definition with Arguments

`commands.cfg`

```
define command{
        command_name    check_docker
        command_line    /usr/bin/python /usr/local/nagios/libexec/plugins/check_http_json.py -H 127.0.0.1:4243 -p info -e Containers -q IPv4Forwarding,1 -w Debug,2:2 -c Images,1:1 -m Containers,0:250,0:500,0,1000 Images NEventsListener NFd NGoroutines SwapLimit
        }
```

#### Sample Output

```
OK: Status OK.|'Containers'=1;0;1000 'Images'=11;0;0 'NEventsListener'=3;0;0 'NFd'=10;0;0 'NGoroutines'=14;0;0 'SwapLimit'=1;0;0
```

### Docker Container Monitor Example Plugin

`check_http_json.py` is generic enough to read and evaluate rules on any HTTP endpoint that returns JSON. In this example we'll get the status of a specific container using it's ID which camn be found by using the list containers endpoint (`curl http://127.0.0.1:4243/containers/json?all=1`).

##### Connection information

* Host = 127.0.0.1:4243
* Path = /containers/2356e8ccb3de8308ccb16cf8f5d157bc85ded5c3d8327b0dfb11818222b6f615/json

##### Rules for "aliveness"

* Verify that the key `ID` exists and is equal to the value `2356e8ccb3de8308ccb16cf8f5d157bc85ded5c3d8327b0dfb11818222b6f615`
* Verify that the key `State.Running` has a value of `True`

#### Service Definition

`localhost.cfg`

```
define service {
        use                             local-service
        host_name                       localhost
        service_description             Docker container liveness check
        check_command                   check_my_container
        }
```

#### Command Definition with Arguments

`commands.cfg`

```
define command{
        command_name    check_my_container
        command_line    /usr/bin/python /usr/local/nagios/libexec/plugins/check_http_json.py -H 127.0.0.1:4243 -p /containers/2356e8ccb3de8308ccb16cf8f5d157bc85ded5c3d8327b0dfb11818222b6f615/json -q ID,2356e8ccb3de8308ccb16cf8f5d157bc85ded5c3d8327b0dfb11818222b6f615 State.Running,True
        }
```

#### Sample Output

```
WARNING: Status check failed, reason: Value True for key State.Running did not match.
```

The plugin threw a warning because the Container ID I used on my system has the following State object:

```
 u'State': {...
            u'Running': False,
            ...
```

If I change the command to have the parameter -q parameter `State.Running,False`, the output becomes:

```
OK: Status OK.
```

### Dropwizard / Fieldnames Containing '.' Example

Simply choose a separator to  deal with data such as this:

```
{ "gauges": { "jvm.buffers.direct.capacity": {"value": 215415}}}
```

In this example I've chosen `_` to separate `guages` from `jvm` and `capacity` from `value`. The CLI invocation then becomes:

```
./check_http_json.py -H localhost:8081 -p metrics --key_exists gauges_jvm.buffers.direct.capacity_value -f _
```

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
