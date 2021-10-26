import argparse
import base64
from functools import partial
from idstools import unified2
from json import dumps,loads
from kafka import KafkaProducer
import logging
from multiprocessing import Pool, Process, Manager
import os
import time, ast, sys

try:
        from collections import OrderedDict
except ImportError as err:
        from idstools.compat.ordereddict import OrderedDict

snort_data = "/snort-data/"
postfix = "unified2"

def main():

    parser = argparse.ArgumentParser(
        usage = "%(prog)s --threads [num_threads] --kafka [kafka_hosts]",
        description="Parse unified2 files to kafka brokers in parallel."
    )
    parser.add_argument(
        "-t", "--threads",
        metavar="<num_threads>",
        default=24,
        help="threads for parse parallelisation")
    parser.add_argument(
        "-k", "--kafka", metavar="<kafka_brokers>",
        required=True,
        help="comma-separated kafka brokers, e.g.'kafka1:9092','kafka2:9093']"
    )

    args = parser.parse_args()
    kafka_brokers = [item for item in args.kafka.split(',')]
    now = time.time()

    file_list = [f for f in os.listdir(snort_data) if (postfix in f)]

    pool = Pool(args.threads)
    partial_process = partial(process_file, kafka_brokers)
    df_collection = pool.map(partial_process, file_list)
    pool.close()
    pool.join()

    final_now = time.time()

    total_time = final_now - now
    print ("total time is %s", total_time)


def process_file(kafka_brokers, read_file):

    producer = KafkaProducer(bootstrap_servers=kafka_brokers)

    reader = unified2.FileRecordReader(snort_data + read_file)

    print ("###### Qué fichero esta leyendo?? ", read_file)

    record_prev = None
    http_uri = None
    extra_data = None
    for index,record in enumerate(reader):
        try:
            if isinstance(record, unified2.Event):
                extra_data = None
                record_prev = record
                aux = 0
                continue
            elif isinstance(record, unified2.ExtraData):
                if aux == 0:
                    http_uri = record["httpdata"]
                    aux = 1
                else:
                    http_hostname = record["httpdata"]
                    extra_data = [http_uri, http_hostname]
                    http_uri = record["httpdata"]
                    aux=0
                continue
            elif ((isinstance(record, unified2.Packet)) or (isinstance(record, unified2.Buffer))):
                record_json = dumps(format_json(record, record_prev= record_prev, extraData = extra_data ))
            else: # runs only by ExtraDataHdr (not needed to create record for the analysis)
                continue

            # Convert the json string to a dict
            rjson = loads(record_json)
            record_list = list()
            for key, value in rjson.items():
                producer.send('snort3-U2events', value=dumps(value).encode('utf-8'))

            time.sleep(0.01)

        except unified2.UnknownRecordType as err:
            if count == 0:
                LOG.error("%s: Is this a unified2 file?" % (err))
            else:
                LOG.error(err)




def format_json(record, record_prev=None, extraData = None):
    data = {}

    for key in record:
        if key == "data" or key == "httpdata" :
            data[key] = base64.b64encode(record[key]).decode("utf-8")
        elif key.endswith(".raw"):
            continue
        elif key in ["extra-data", "packets"]:
            continue
        elif key == "appid" and not record["appid"]:
            data[key] = None
        else:
            data[key] = record[key]

    if record_prev:
        for key in record_prev:
            if key == "data" or key == "httpdata":
                data[key] = base64.b64encode(record_prev[key]).decode("utf-8")
            elif key.endswith(".raw"):
                continue
            elif key in ["extra-data", "packets"]:
                continue
            elif key == "appid" and not record_prev["appid"]:
                data[key] = None
            else:
                data[key] = record_prev[key]

    if extraData:
        data["HTTP_URI"] = extraData[0]
        data["HTTP_Hostname"] = extraData[1]
#    else: # put extradata to None to make data be consistent
#        data["HTTP_URI"] = None
#        data["HTTP_Hostname"] = None

    return OrderedDict([("Record", data)])


if __name__ == "__main__":
    main()

