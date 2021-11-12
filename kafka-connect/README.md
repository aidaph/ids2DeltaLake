## Kafka-connect in ids2DeltaLake

Kafka-connect is a framework for connecting kafka with external systems. In this platform it is used to collect records from the the json-alert files and send them to kafka in a **distributed** way. The so-called `connectors` help us to import the data faster and with low latency thanks to the kafka technology. 

### Setup

Kafka-connect is installed in the IDS machine. Commonly, kafka-connect is installed via Confluent Platform but in order to follow a better customize process use the kafka-source tar file that can be downloaded from [the official site](https://kafka.apache.org/downloads). At the time the testing has been performed, the version of kafka was 2.8.0. 

To work with kafka-connect with highly performance we need to launch it in a distributed mode. Copy the settings file and the connector configuration, the `connect-distributed.properties` and `connect-file-spooldir.json` files, respectively from `conf` dir. Adapted them for your environment.

To import data from a directory where JSON files are writing in real time I use the kafka-connect-spooldir connector from [this](https://github.com/jcustenborder/kafka-connect-spooldir) repository. Once the zip is downloaded, move it to the /usr/share/java folder (in my case) where all the jar files are stored. 

```
unzip jcustenborder-kafka-connect-spooldir-2.0-SNAPSHOT.zip -d /usr/share/java/kafka-connect-spooldir/
```

If you don't hava Java installed, the default-jdf package must be a installed for kafka-connect. If the jar are saved in another path than the default one, set plugin.path for your kafka-connect-spooldir directory. 


### Start Kafka-connect

We can start Connect in distributed mode as follows:
```
/path/to/kafka/bin/connect-distributed.sh /path/to/kafka/config/connect-distributed.properties
```

For adding the connector, use the REST API insted of passing it as argument. For this, we need to use the POST request to  http://kafka-connector:8083/connectors. Do it from the config folder inside Kafka path. 

```
curl -s -X POST -H 'Content-Type: application/json' --data @connect-file-spooldir.json http://localhost:8083/connectors
```
Verify that the connector is running well performing the kafka-consumer that is gathering the records. 

```
/path/to/kafka-console-consumer --bootstrap-server <kafka-ip>:9092 --topic connect-distributed --from-beginning
```

To remove the connector use the DELETE request via curl passing the name of the connector.
```
curl -X DELETE http://kafka-connector:8083/connectors/local-file-source
```


