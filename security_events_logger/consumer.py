# implements Kafka topic consumer functionality

import threading
from confluent_kafka import Consumer, OFFSET_BEGINNING
import json

LOGS_PATH = "security_events_logger/data/"



def handle_event(id: str, details: dict):
    # print(f"[debug] handling event {id}, {details}")
    print(
        f"[info] handling event {id}, {details['source']}->{details['deliver_to']}: {details['operation']}")
    try:
        with open("security_events_logger/logs/security_events.log", "a+") as f:
            f.write(json.dumps(details)+"\n")
    except Exception as e:
        print(f"[error] failed to handle request: {e}")


def consumer_job(args, config):
    # Create Consumer instance
    consumer = Consumer(config)

    # Set up a callback to handle the '--reset' flag.
    def reset_offset(consumer, partitions):
        if args.reset:
            for p in partitions:
                p.offset = OFFSET_BEGINNING
            consumer.assign(partitions)

    # Subscribe to topic
    topic = "security_events_logger"
    consumer.subscribe([topic], on_assign=reset_offset)

    # Poll for new messages from Kafka and print them.
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                # Initial message consumption may take up to
                # `session.timeout.ms` for the consumer group to
                # rebalance and start consuming
                # print("Waiting...")
                pass
            elif msg.error():
                print(f"[error] {msg.error()}")
            else:
                # Extract the (optional) key and value, and print.
                try:
                    id = msg.key().decode('utf-8')
                    details = json.loads(msg.value().decode('utf-8'))
                    # print(
                    #     f"[debug] consumed event from topic {topic}: key = {id} value = {details}")
                    handle_event(id, details)
                except Exception as e:
                    print(
                        f"[error] Malformed event received from topic {topic}: {msg.value()}. {e}")
    except KeyboardInterrupt:
        pass
    finally:
        # Leave group and commit final offsets
        consumer.close()


def start_consumer(args, config) -> threading.Thread:
    consumer_thread = threading.Thread(target=lambda: consumer_job(args, config))
    consumer_thread.start()
    return consumer_thread
