#!/usr/bin/env python

from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from multiprocessing import Queue
from consumer import start_consumer

if __name__ == '__main__':
    # Parse the command line.
    parser = ArgumentParser()
    parser.add_argument('config_file', type=FileType('r'))
    parser.add_argument('--reset', action='store_true')
    args = parser.parse_args()

    # Parse the configuration.
    # See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    config_parser = ConfigParser()
    config_parser.read_file(args.config_file)
    config = dict(config_parser['default'])
    config.update(config_parser['security_events_logger'])

    requests_queue = Queue()
    consumer_thread = start_consumer(args, config)
    consumer_thread.join()
    print("events logger finished")
