# ids_u2toparquet

This packages allows you to format your Unified 2 data provided by Snort to Parquet file. Before storage the data you can chose where the file is stored. In this case, only hdfs storage is allowed.

The type of data in Snort is organized in event and packet. First of all, a schema is defined as below:

event:
- impact
- generator-id
- protocol
- dport-icode
- signature-revision
- classification-id
- signature-id
- sensor-id
- impact-flag
- sport-itype
- priority
- event-second
- pad2
- destination-ip
- event-id
- mpls-label
- vlan-id
- source-ip
- event-microsecond
- blocked

packet:
- type
- packet-second
- linktype
- sensor-id
- packet-microsecond
- event-second
- length
- data
- event-id

## Usage
Install it using ` python setup.py install`.

Export the JAVA_HOME variable before using the program. 

Create the parquet file in hadoop:
```
/usr/local/bin/u2toparquet /path/to/snortU2File/snort.u2.1235677 /user/hadoop/parquet/snort_alerts_test.parquet
```

See if the file was created in hadoop:
```
hadoop fs -ls /user/hadoop/parquet/
```

