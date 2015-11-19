# Riak Stats Example

## Description

For this example we're going to use `check_http_json.py` as a pure CLI tool to read Riak's `/stats` endpoint

## Connection information

* Host = 127.0.0.1:8098
* Path = /stats

## JSON Stats Data

* Full Riak HTTP Stats information can be found here: [http://docs.basho.com/riak/latest/dev/references/http/status/](http://docs.basho.com/riak/latest/dev/references/http/status/)
* Information related to specific interesting stats can be found here: [http://docs.basho.com/riak/latest/ops/running/stats-and-monitoring/](http://docs.basho.com/riak/latest/ops/running/stats-and-monitoring/)

## Connectivity Check

* `ring_members`: We can use an existence check to monitor the number of ring members
* `connected_nodes`: Similarly we can check the number of nodes that are in communication with this node, but this list will be empty in a 1 node cluster

#### Sample Command

For a single node dev "cluster", you might have a `ring_members` value like this:

```
"ring_members": [
    "riak@127.0.0.1"
],
```

To validate that we have a single node, we can use this check:

```
$ ./check_http_json.py -H localhost -P 8098 -p stats -E "ring_members(0)"
OK: Status OK.
```

If we were expecting at least 2 nodes in the cluster, we would use this check:

```
$ ./check_http_json.py -H localhost -P 8098 -p stats -E "ring_members(1)"
CRITICAL: Status CRITICAL. Key ring_members(1) did not exist.
```

Obviously this fails because we only had a single `ring_member`. If we prefer to only get a warning instead of a critical for this check, we just use the correct flag:

```
$ ./check_http_json.py -H localhost -P 8098 -p stats -e "ring_members(1)"
WARNING: Status WARNING. Key ring_members(1) did not exist.
```

## Gather Metrics

The thresholds for acceptable values for these metrics will vary from system to system, following are the stats we'll be checking:

### Throughput Metrics:

* `node_gets`
* `node_puts`
* `vnode_counter_update`
* `vnode_set_update`
* `vnode_map_update`
* `search_query_throughput_one`
* `search_index_throughtput_one`
* `consistent_gets`
* `consistent_puts`
* `vnode_index_reads`

#### Sample Command

```
./check_http_json.py -H localhost -P 8098 -p stats -m \
    "node_gets" \
    "node_puts" \
    "vnode_counter_update" \
    "vnode_set_update" \
    "vnode_map_update" \
    "search_query_throughput_one" \
    "search_index_throughtput_one" \
    "consistent_gets" \
    "consistent_puts" \
    "vnode_index_reads"
```

#### Sample Output

```
OK: Status OK.|'node_gets'=0 'node_puts'=0 'vnode_counter_update'=0 'vnode_set_update'=0 'vnode_map_update'=0 'search_query_throughput_one'=0 'consistent_gets'=0 'consistent_puts'=0 'vnode_index_reads'=0
```

### Latency Metrics:

* `node_get_fsm_time_mean,_median,_95,_99,_100`
* `node_put_fsm_time_mean,_median,_95,_99,_100`
* `object_counter_merge_time_mean,_median,_95,_99,_100`
* `object_set_merge_time_mean,_median,_95,_99,_100`
* `object_map_merge_time_mean,_median,_95,_99,_100`
* `search_query_latency_median,_min,_95,_99,_999`
* `search_index_latency_median,_min,_95,_99,_999`
* `consistent_get_time_mean,_median,_95,_99,_100`
* `consistent_put_time_mean,_median,_95,_99,_100`

#### Sample Command

```
./check_http_json.py -H localhost -P 8098 -p stats -m \
    "node_get_fsm_time_mean,,0:100,0:1000" \
    "node_get_fsm_time_median,,0:100,0:1000" \
    "node_get_fsm_time_95,,0:100,0:1000" \
    "node_get_fsm_time_99,,0:100,0:1000" \
    "node_get_fsm_time_100,,0:100,0:1000" \
    "node_put_fsm_time_mean,,0:100,0:1000" \
    "node_put_fsm_time_median,,0:100,0:1000" \
    "node_put_fsm_time_95,,0:100,0:1000" \
    "node_put_fsm_time_99,,0:100,0:1000" \
    "node_put_fsm_time_100,,0:100,0:1000" \
    "object_counter_merge_time_mean,,0:100,0:1000" \
    "object_counter_merge_time_median,,0:100,0:1000" \
    "object_counter_merge_time_95,,0:100,0:1000" \
    "object_counter_merge_time_99,,0:100,0:1000" \
    "object_counter_merge_time_100,,0:100,0:1000" \
    "object_set_merge_time_mean,,0:100,0:1000" \
    "object_set_merge_time_median,,0:100,0:1000" \
    "object_set_merge_time_95,,0:100,0:1000" \
    "object_set_merge_time_99,,0:100,0:1000" \
    "object_set_merge_time_100,,0:100,0:1000" \
    "object_map_merge_time_mean,,0:100,0:1000" \
    "object_map_merge_time_median,,0:100,0:1000" \
    "object_map_merge_time_95,,0:100,0:1000" \
    "object_map_merge_time_99,,0:100,0:1000" \
    "object_map_merge_time_100,,0:100,0:1000" \
    "consistent_get_time_mean,,0:100,0:1000" \
    "consistent_get_time_median,,0:100,0:1000" \
    "consistent_get_time_95,,0:100,0:1000" \
    "consistent_get_time_99,,0:100,0:1000" \
    "consistent_get_time_100,,0:100,0:1000" \
    "consistent_put_time_mean,,0:100,0:1000" \
    "consistent_put_time_median,,0:100,0:1000" \
    "consistent_put_time_95,,0:100,0:1000" \
    "consistent_put_time_99,,0:100,0:1000" \
    "consistent_put_time_100,,0:100,0:1000" \
    "search_query_latency_median,,0:100,0:1000" \
    "search_query_latency_min,,0:100,0:1000" \
    "search_query_latency_95,,0:100,0:1000" \
    "search_query_latency_99,,0:100,0:1000" \
    "search_query_latency_999,,0:100,0:1000" \
    "search_index_latency_median,,0:100,0:1000" \
    "search_index_latency_min,,0:100,0:1000" \
    "search_index_latency_95,,0:100,0:1000" \
    "search_index_latency_99,,0:100,0:1000" \
    "search_index_latency_999,,0:100,0:1000"
```

#### Sample Output

```
OK: Status OK.|'node_get_fsm_time_mean'=0;0:100;0:1000 'node_get_fsm_time_median'=0;0:100;0:1000 'node_get_fsm_time_95'=0;0:100;0:1000 'node_get_fsm_time_99'=0;0:100;0:1000 'node_get_fsm_time_100'=0;0:100;0:1000 'node_put_fsm_time_mean'=0;0:100;0:1000 'node_put_fsm_time_median'=0;0:100;0:1000 'node_put_fsm_time_95'=0;0:100;0:1000 'node_put_fsm_time_99'=0;0:100;0:1000 'node_put_fsm_time_100'=0;0:100;0:1000 'object_counter_merge_time_mean'=0;0:100;0:1000 'object_counter_merge_time_median'=0;0:100;0:1000 'object_counter_merge_time_95'=0;0:100;0:1000 'object_counter_merge_time_99'=0;0:100;0:1000 'object_counter_merge_time_100'=0;0:100;0:1000 'object_set_merge_time_mean'=0;0:100;0:1000 'object_set_merge_time_median'=0;0:100;0:1000 'object_set_merge_time_95'=0;0:100;0:1000 'object_set_merge_time_99'=0;0:100;0:1000 'object_set_merge_time_100'=0;0:100;0:1000 'object_map_merge_time_mean'=0;0:100;0:1000 'object_map_merge_time_median'=0;0:100;0:1000 'object_map_merge_time_95'=0;0:100;0:1000 'object_map_merge_time_99'=0;0:100;0:1000 'object_map_merge_time_100'=0;0:100;0:1000 'consistent_get_time_mean'=0;0:100;0:1000 'consistent_get_time_median'=0;0:100;0:1000 'consistent_get_time_95'=0;0:100;0:1000 'consistent_get_time_99'=0;0:100;0:1000 'consistent_get_time_100'=0;0:100;0:1000 'consistent_put_time_mean'=0;0:100;0:1000 'consistent_put_time_median'=0;0:100;0:1000 'consistent_put_time_95'=0;0:100;0:1000 'consistent_put_time_99'=0;0:100;0:1000 'consistent_put_time_100'=0;0:100;0:1000 'search_query_latency_median'=0;0:100;0:1000 'search_query_latency_min'=0;0:100;0:1000 'search_query_latency_95'=0;0:100;0:1000 'search_query_latency_99'=0;0:100;0:1000 'search_query_latency_999'=0;0:100;0:1000 'search_index_latency_median'=0;0:100;0:1000 'search_index_latency_min'=0;0:100;0:1000 'search_index_latency_95'=0;0:100;0:1000 'search_index_latency_99'=0;0:100;0:1000 'search_index_latency_999'=0;0:100;0:1000
```

### Erlang Resource Usage Metrics:

* `sys_process_count`
* `memory_processes`
* `memory_processes_used`

#### Sample Command

```
./check_http_json.py -H localhost -P 8098 -p stats -m \
    "sys_process_count,,0:5000,0:10000" \
    "memory_processes,,0:50000000,0:100000000" \
    "memory_processes_used,,0:50000000,0:100000000"
```

#### Sample Output

```
OK: Status OK.|'sys_process_count'=1637;0:5000;0:10000 'memory_processes'=46481112;0:50000000;0:100000000 'memory_processes_used'=46476880;0:50000000;0:100000000
```

### General Riak Load / Health Metrics:

* `node_get_fsm_siblings_mean,_median,_95,_99,_100`
* `node_get_fsm_objsize_mean,_median,_95,_99,_100`
* `riak_search_vnodeq_mean,_median,_95,_99,_100`
* `search_index_fail_one`
* `pbc_active`
* `pbc_connects`
* `read_repairs`
* `list_fsm_active`
* `node_get_fsm_rejected`
* `node_put_fsm_rejected`

#### Sample Command

```
./check_http_json.py -H localhost -P 8098 -p stats -m \
    "node_get_fsm_siblings_mean,,0:100,0:1000" \
    "node_get_fsm_siblings_median,,0:100,0:1000" \
    "node_get_fsm_siblings_95,,0:100,0:1000" \
    "node_get_fsm_siblings_99,,0:100,0:1000" \
    "node_get_fsm_siblings_100,,0:100,0:1000" \
    "node_get_fsm_objsize_mean,,0:100,0:1000" \
    "node_get_fsm_objsize_median,,0:100,0:1000" \
    "node_get_fsm_objsize_95,,0:100,0:1000" \
    "node_get_fsm_objsize_99,,0:100,0:1000" \
    "node_get_fsm_objsize_100,,0:100,0:1000" \
    "riak_search_vnodeq_mean,,0:100,0:1000" \
    "riak_search_vnodeq_median,,0:100,0:1000" \
    "riak_search_vnodeq_95,,0:100,0:1000" \
    "riak_search_vnodeq_99,,0:100,0:1000" \
    "riak_search_vnodeq_100,,0:100,0:1000" \
    "search_index_fail_one,,0:100,0:1000" \
    "pbc_active,,0:100,0:1000" \
    "pbc_connects,,0:100,0:1000" \
    "read_repairs,,0:100,0:1000" \
    "list_fsm_active,,0:100,0:1000" \
    "node_get_fsm_rejected,,0:100,0:1000" \
    "node_put_fsm_rejected,,0:100,0:1000"
```

#### Sample Output

```
OK: Status OK.|'node_get_fsm_siblings_mean'=0;0:100;0:1000 'node_get_fsm_siblings_median'=0;0:100;0:1000 'node_get_fsm_siblings_95'=0;0:100;0:1000 'node_get_fsm_siblings_99'=0;0:100;0:1000 'node_get_fsm_siblings_100'=0;0:100;0:1000 'node_get_fsm_objsize_mean'=0;0:100;0:1000 'node_get_fsm_objsize_median'=0;0:100;0:1000 'node_get_fsm_objsize_95'=0;0:100;0:1000 'node_get_fsm_objsize_99'=0;0:100;0:1000 'node_get_fsm_objsize_100'=0;0:100;0:1000      'search_index_fail_one'=0;0:100;0:1000 'pbc_active'=0;0:100;0:1000 'pbc_connects'=0;0:100;0:1000 'read_repairs'=0;0:100;0:1000 'list_fsm_active'=0;0:100;0:1000 'node_get_fsm_rejected'=0;0:100;0:1000 'node_put_fsm_rejected'=0;0:100;0:1000
```
