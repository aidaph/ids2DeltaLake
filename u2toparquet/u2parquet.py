# -*- coding: utf-8 -*-

"""Read unified2 log files and output records as Parquet for save into hadoop"""

from __future__ import print_function

import sys
import os
import os.path
import base64
import string
import json
import logging
from pathlib import Path

if sys.argv[0] == __file__:
    sys.path.insert(
        0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))


import argparse

from idstools import unified2
from idstools import maps
from idstools import util

import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
LOG = logging.getLogger()

class Formatter(object):

    #def __init__(self):

    def create_schema_event(self):
        return pa.schema([
                    pa.field('type', pa.string()),
                    pa.field('impact', pa.int64()),
                    pa.field('generator-id', pa.int64()),
                    pa.field('protocol', pa.int64()),
                    pa.field('dport-icode', pa.int64()),
                    pa.field('signature-revision', pa.int64()),
                    pa.field('classification-id', pa.int64()),
                    pa.field('signature-id', pa.int64()),
                    pa.field('sensor-id', pa.int64()),
                    pa.field('impact-flag', pa.int64()),
                    pa.field('sport-itype', pa.int64()),
                    pa.field('priority', pa.int64()),
                    pa.field('event-second', pa.int64()),
                    pa.field('pad2', pa.int64()),
                    pa.field('destination-ip', pa.string()),
                    pa.field('event-id', pa.int64()),
                    pa.field('mpls-label', pa.int64()),
                    pa.field('vlan-id', pa.int64()),
                    pa.field('source-ip', pa.string()),
                    pa.field('event-microsecond', pa.int64()),
                    pa.field('blocked', pa.int64())
                ])
    def create_schema_packet(self):
        return pa.schema([
                    pa.field('type', pa.string()),
                    pa.field('packet-second', pa.int64()),
                    pa.field('linktype', pa.int64()),
                    pa.field('sensor-id', pa.int64()),
                    pa.field('packet-microsecond', pa.int64()),
                    pa.field('event-second', pa.int64()),
                    pa.field('length', pa.int64()),
                    pa.field('data', pa.string()),
                    pa.field('event-id', pa.int64())
                ])

    def create_schema(self):
        return pa.schema([
                    pa.field('type', pa.string()),
                    pa.field('impact', pa.int64()),
                    pa.field('generator-id', pa.int64()),
                    pa.field('protocol', pa.int64()),
                    pa.field('dport-icode', pa.int64()),
                    pa.field('signature-revision', pa.int64()),
                    pa.field('classification-id', pa.int64()),
                    pa.field('signature-id', pa.int64()),
                    pa.field('impact-flag', pa.int64()),
                    pa.field('sport-itype', pa.int64()),
                    pa.field('priority', pa.int64()),
                    pa.field('pad2', pa.int64()),
                    pa.field('destination-ip', pa.string()),
                    pa.field('mpls-label', pa.int64()),
                    pa.field('vlan-id', pa.int64()),
                    pa.field('source-ip', pa.string()),
                    pa.field('event-microsecond', pa.int64()),
                    pa.field('blocked', pa.float64()),
                    pa.field('packet-second', pa.int64()),
                    pa.field('linktype', pa.int64()),
                    pa.field('sensor-id', pa.int64()),
                    pa.field('packet-microsecond', pa.int64()),
                    pa.field('event-second', pa.int64()),
                    pa.field('length', pa.int64()),
                    pa.field('data', pa.string()),
                    pa.field('event-id', pa.int64())
                ])


    def format(self, record, record_prev, schema, column_data, type_data):
        """
        record: Array in Unified2 format
        schema: PyArrow schema object or list of column names

        return: array_data: Array of one record
        """
        for column in schema.names:
            _col = column_data.get(column, [])
            if column == "type":
                _col.append(type_data)
            elif column == "data" and (record.get(column) is not None or record_prev.get(column) is not None):
                data = base64.b64encode(record.get(column)).decode("utf-8")
                _col.append(data)
            elif record.get(column) is not None:
                _col.append(record.get(column))
            else:
                _col.append(record_prev.get(column))

            column_data[column] = _col

class OutputWrapper(object):

    def __init__(self, filename, fileobj=None):
        self.filename = filename
        self.fileobj = fileobj


        if self.fileobj is None:
            self.isfile = True
            self.reopen()
        else:
            self.isfile = False

    def reopen(self):
        if not self.isfile:
            return
        if self.fileobj:
            self.fileobj.close()
        self.fileobj = open(self.filename, "a")

    def write(self, buf):
        if self.isfile:
            if not os.path.exists(self.filename):
                self.reopen()
        self.fileobj.write(buf)
        self.fileobj.write("\n")
        self.fileobj.flush()

epilog = """If --directory and --prefix are provided files will be
read from the specified 'spool' directory.  Otherwise files on the
command line will be processed.
"""

def main():

    parser = argparse.ArgumentParser(
        fromfile_prefix_chars='@', epilog=epilog)
    parser.add_argument(
        "--directory", metavar="<spool directory>",
        help="spool directory (eg: /var/log/snort)")
    parser.add_argument(
        "--prefix", metavar="<spool file prefix>",
        help="spool filename prefix (eg: unified2.log)")
    parser.add_argument(
        "--bookmark", metavar="<filename>", help="enable bookmarking")
    parser.add_argument(
        "--follow", action="store_true", default=False,
        help="follow files/continuous mode (spool mode only)")
    parser.add_argument(
        "--delete", action="store_true", default=False,
        help="delete spool files")
    parser.add_argument(
        "--output", metavar="<filename>",
        help="output directory (eg: /var/log/snort/alerts.parquet")
    parser.add_argument(
        "--stdout", action="store_true", default=False,
        help="also log to stdout if --output is a file")
    #parser.add_argument(
    #    "--parquet", action="store_true", default=False,
    #    help="parquet output file path")
    parser.add_argument(
        "--verbose", action="store_true", default=False,
        help="be more verbose")
    parser.add_argument(
        "filenames", nargs="*")
    parser.add_argument(
        "parquet", type=os.path.abspath,
        help="path to parquet file in hdfs")
    args = parser.parse_args()

    if args.verbose:
        LOG.setLevel(logging.DEBUG)

    if args.filenames:
        if args.bookmark:
            LOG.error("Bookmarking not valid in file mode.")
            return 1
        if args.follow:
            LOG.error("Follow not valid in file mode.")
            return 1
        if args.delete:
            LOG.error("Delete not valid in file mode.")
            return 1
        reader = unified2.FileRecordReader(*args.filenames)
    else:
        LOG.error("No spool or files provided.")
        return 1

    if not args.parquet:
        LOG.error("A parquet output path must be specified.")

    formatter = Formatter()

    #column_data_event = {}
    #column_data_packet = {}
    column_data = {}
    array_data = []
    record_prev = None

    # Create schemas
    schema_event = formatter.create_schema_event()
    schema_packet = formatter.create_schema_packet()
    schema = formatter.create_schema()
    #parquet_out=os.path.dirname(os.path.abspath(args.parquet))

    print("########### COLUMN DATA: ",column_data)
    try:
        limit = 10
        for index,record in enumerate(reader):
            try:
                print("########### record: ",record)
                #if isinstance(record, unified2.Event):
                #elif isinstance(record, unified2.Packet):
                #else:
                #    LOG.warning("Unknown record type: %s: %s" % (
                #    str(record.__class__), str(record)))
                if record_prev is not None and record.get("event-id") == record_prev.get("event-id"):
                    formatter.format(record, record_prev, schema, column_data, type_data="event")
                else:
                    LOG.warning("The packet does not belong to the same event")

                record_prev = record
                if index == limit:
                    break
            except Exception as err:
                LOG.error("Failed to encode record as Parquet: %s: %s" % (
                    str(err), str(record)))
                raise
        df = pd.DataFrame(data=column_data)

        for column in schema:
            _col = column_data.get(column.name)
            array_data.append(pa.array(_col, type=column.type))
    except unified2.UnknownRecordType as err:
        if count == 0:
            LOG.error("%s: Is this a unified2 file?" % (err))
        else:
            LOG.error(err)

    ## Write data in parquet
    try:
        table = pa.Table.from_pandas(df)
    except TypeError:
        table = pa.Table.from_pandas([df])
    #pq.write_table(table, args.output)
    print("######## table: ", table)

    # Move file to HDFS
    fs = pa.hdfs.connect(host='hadoop-namenode', port=9820, user="hadoopuser")
    #pq.write_to_dataset(table, root_path='/user/hadoop/parquet/snort_alerts1.parquet', filesystem=fs)
    pq.write_to_dataset(table, root_path=args.parquet, filesystem=fs)

if __name__ == "__main__":
    sys.exit(main())
