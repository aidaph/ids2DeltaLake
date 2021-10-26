from json import dumps,loads
import time, ast, sys
from idstools import unified2
from kafka import KafkaProducer
import numpy as np
#import pyarrow as pa
import base64
import logging
import os
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler


try:
        from collections import OrderedDict
except ImportError as err:
        from idstools.compat.ordereddict import OrderedDict

class MyHandler(LoggingEventHandler):
    def on_modified(self, event):
        print('event type:', event.event_type, ' path :', event.src_path)
        self.src_file = event.src_path
        sys.exit()

def main():

    now = time.time()

    # Para que el producer no cancele la conexion con el broker, lanzarlo durante un dia
    try:
        i = 0
        while i < 100:
            create_producer()
    except KeyboardInterrupt:
        os._exit(0)

    final_now = time.time()

    total_time = final_now - now
    print ("total time is %s", total_time)


def create_producer():

    producer = KafkaProducer(bootstrap_servers='mods-kafka-new:9092')#,
                         #value_serializer=lambda x:
                         #dumps(x).encode('latin1'))

    # Open file to read
    column_data = {}

    path = "/var/log/snort/"

    ## Read file in real time
    #read_file = read_realtime(path)

    read_file = "32_unified2.log"

    print( read_file )
    reader = unified2.FileRecordReader(read_file) #"/var/log/snort/snort.u2.1594751955")

    record_prev = None
    for index,record in enumerate(reader):
        # Create a unique record = event + packet (same event-id)
        print ("###### RECORD  %s "% record)
        try:
            if record_prev is not None and record.get("event-id") == record_prev.get("event-id"):
                # convert record to jason and remove the unnecesary fields
                record_json = dumps(format_json(record,record_prev))
                # Convert the json string to a dict
                rjson = loads(record_json)
                record_list = list()
                for key, value in rjson.items():
                    print (value)
                    producer.send('SNORT', value=dumps(value).encode('utf-8'))
            else:
                print ("The packet does not belong to the same event")

            record_prev = record
            if index > 10000 and record_prev.get("event-id") == 0:
                break

            time.sleep(0.01)

            #remove_old_files(path)

        except unified2.UnknownRecordType as err:
            if count == 0:
                LOG.error("%s: Is this a unified2 file?" % (err))
            else:
                LOG.error(err)
    #producer.close(259200000)
    # En cuanto el fichero lleve un rato sin escribirse borrarlo (Max. 256MB)


def read_realtime(path):
    # Read new file in real-time
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    path = "/var/log/snort/"
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        #while True:
        time.sleep(10)
        observer.stop()
    except KeyboardInterrupt:
        observer.stop()

    return event_handler.src_file


def format_json(record, record_prev):
    data = {}

    for key in record:
        if key == "data":
            data["data"] = base64.b64encode(record[key]).decode("utf-8")
        elif key.endswith(".raw"):
            continue
        elif key in ["extra-data", "packets"]:
            continue
        elif key == "appid" and not record["appid"]:
            continue
        else:
            data[key] = record[key]

    for key in record_prev:
        if key == "data":
            data["data"] = base64.b64encode(record_prev[key]).decode("utf-8")
        elif key.endswith(".raw"):
            continue
        elif key in ["extra-data", "packets"]:
            continue
        elif key == "appid" and not record_prev["appid"]:
            continue
        else:
            data[key] = record_prev[key]

    return OrderedDict([("Record", data)])

def remove_old_files(path):
    now = time.time()
    for f in os.listdir(path):
        f = os.path.join(path,f)
        # Remove files older than 1 day
        if os.stat(f).st_mtime < now - 1 * 86400:
            if os.path.isfile(f):
                os.remove(f)


#def format(record, column_data, schema):
#        """
#        record: Array in Unified2 format
#        schema: PyArrow schema object or list of column names

 #       return: array_data: Array of one record
 #       """
        #schema = pa.schema([
        #            pa.field('type', pa.string()),
        #            pa.field('impact', pa.int64()),
        #            pa.field('generator-id', pa.int64()),
        #            pa.field('protocol', pa.int64()),
        #            pa.field('dport-icode', pa.int64()),
        #            pa.field('signature-revision', pa.int64()),
        #            pa.field('classification-id', pa.int64()),
        #            pa.field('signature-id', pa.int64()),
        #            pa.field('impact-flag', pa.int64()),
        #            pa.field('sport-itype', pa.int64()),
        #            pa.field('priority', pa.int64()),
        #            pa.field('pad2', pa.int64()),
        #            pa.field('destination-ip', pa.string()),
        #            pa.field('mpls-label', pa.int64()),
        #            pa.field('vlan-id', pa.int64()),
        #            pa.field('source-ip', pa.string()),
        #            pa.field('event-microsecond', pa.int64()),
        #            pa.field('blocked', pa.float64()),
        #            pa.field('packet-second', pa.int64()),
        #            pa.field('linktype', pa.int64()),
        #            pa.field('sensor-id', pa.int64()),
        #            pa.field('packet-microsecond', pa.int64()),
        #            pa.field('event-second', pa.int64()),
        #            pa.field('length', pa.int64()),
        #            pa.field('data', pa.string()),
        #            pa.field('event-id', pa.int64())
        #        ])

        #record_current = {}
        #for column in schema.names:
        #    _col = column_data.get(column, [])
        #    #if column == "type":
        #    #    _col.append(type_data)
        #    if column == "data" and record.get(column) is not None:
        #        data = base64.b64encode(record.get(column)).decode("utf-8")
        #        _col.append(data)
        #    elif record.get(column) is not None:
        #        _col.append(record.get(column))
        #    else:
        #        column_data[column] = _col
        #record_current = column_data
        #return record_current

if __name__ == "__main__":
    main()

