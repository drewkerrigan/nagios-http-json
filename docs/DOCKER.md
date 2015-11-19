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
