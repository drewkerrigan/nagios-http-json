# Example Data for Testing

Example calls:

```bash
python check_http_json.py -H localhost:8080 -p data0.json -q "age,20"
UNKNOWN: Status UNKNOWN. Could not find JSON in HTTP body.
```

```bash
python check_http_json.py -H localhost:8080 -p data1.json -e date
WARNING: Status WARNING. Key date did not exist.

python check_http_json.py -H localhost:8080 -p data1.json -E age
OK: Status OK.

python check_http_json.py -H localhost:8080 -p data1.json -w "age,30"
OK: Status OK.

python check_http_json.py -H localhost:8080 -p data1.json -w "age,20"
WARNING: Status WARNING. Value (30) for key age was outside the range 0:20.

python check_http_json.py -H localhost:8080 -p data1.json -q "age,20"
WARNING: Status WARNING. Key age mismatch. 20 != 30
```

```bash
python check_http_json.py -H localhost:8080 -p data2.json -q "(1).id,123"
WARNING: Status WARNING. Key (1).id mismatch. 123 != 2

python check_http_json.py -H localhost:8080 -p data2.json -Y "(1).id,2"
CRITICAL: Status CRITICAL. Key (1).id match found. 2 == 2

python check_http_json.py -H localhost:8080 -p data2.json -E "(1).author"
OK: Status OK.

python check_http_json.py -H localhost:8080 -p data2.json -E "(1).pages"
CRITICAL: Status CRITICAL. Key (1).pages did not exist.
```

```bash
python check_http_json.py -H localhost:8080 -p data3.json -q "company.employees.(0).role,Developer"
OK: Status OK.

python check_http_json.py -H localhost:8080 -p data3.json -q "company.employees.(0).role,Dev"
WARNING: Status WARNING. Key company.employees.(0).role mismatch. Dev != Developer

python check_http_json.py -H localhost:8080 -p data3.json -q "company.employees.(0).role,Developer" "company.employees.(1).role,Designer" 
OK: Status OK.
```

```bash
python check_http_json.py -H localhost:8080 -p data4.json -u "ratings(0),4.5"
OK: Status OK.

python check_http_json.py -H localhost:8080 -p data4.json -u "ratings(0),4.1"
UNKNOWN: Status UNKNOWN. Key ratings(0) mismatch. 4.1 != 4.5
```

```bash
python check_http_json.py -H localhost:8080 -p data5.json -q service1.status,True service2.status,True service3.status,True
OK: Status OK.
```
