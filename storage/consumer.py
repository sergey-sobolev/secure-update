# implements Kafka topic consumer functionality

import os
import threading
from confluent_kafka import Consumer, OFFSET_BEGINNING
import json
from producer import proceed_to_deliver
import base64

STORAGE_PATH = "storage/data/"


def commit_blob(id, details):
    stored = False
    update_payload_b64 = details['update_file']
    update_payload = base64.b64decode(update_payload_b64)
    try:
        with open(STORAGE_PATH+id, "wb") as f:
            f.write(update_payload)
        f.close()
        stored = True
    except Exception as e:
        print(f'[error] failed to store blob {id} in {os.getcwd()}: {e}')
    return stored, id


def get_blob(id, details):
    success = False
    encoded_blob = None
    try:
        with open(STORAGE_PATH+details['blob_id'], "rb") as f:
            blob = f.read()
        f.close()
        success = True
        encoded_blob = base64.b64encode(blob).decode('ascii')
    except Exception as e:
        print(f"[error] failed to read blob {details}: {e}")
    return success, encoded_blob


def handle_event(id: str, details: dict):
    # print(f"[debug] handling event {id}, {details}")
    print(f"[info] handling event {id}, {details['source']}->{details['deliver_to']}: {details['operation']}")
    try:
        if details['operation'] == 'commit_blob':                                
            # it's a request to store the blob
            stored, blob_id = commit_blob(id, details)
            if stored:
                details['deliver_to'] = details['source']
                details['blob_id'] = blob_id
                details['operation'] = 'blob_committed'
                # remove the update file payload before sending further
                try:
                    del details['update_file']
                finally:
                    proceed_to_deliver(id, details)
            else:
                print("[error] failed to store blob")
        elif details['operation'] == 'get_blob':
            # someone requested the blob, get it and send it to the requester
            result, blob = get_blob(id, details)
            if result is True:
                details['operation'] = 'blob_content'
                details['blob'] = blob
                details['deliver_to'] = details['source']
                proceed_to_deliver(id, details)
            else:
                print(f"[error] failed to read blob")
    except Exception as e:
        print(f"[error] failed to handle request: {e}")


def consumer_job(args, config):
    # Create Consumer instance
    verifier_consumer = Consumer(config)

    # Set up a callback to handle the '--reset' flag.
    def reset_offset(verifier_consumer, partitions):
        if args.reset:
            for p in partitions:
                p.offset = OFFSET_BEGINNING
            verifier_consumer.assign(partitions)

    # Subscribe to topic
    topic = "storage"
    verifier_consumer.subscribe([topic], on_assign=reset_offset)

    # Poll for new messages from Kafka and print them.
    try:
        while True:
            msg = verifier_consumer.poll(1.0)
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
        verifier_consumer.close()


def start_consumer(args, config):
    threading.Thread(target=lambda: consumer_job(args, config)).start()


if __name__ == '__main__':
    start_consumer(None)
