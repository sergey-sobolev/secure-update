# implements Kafka topic consumer functionality

import os
import threading
from confluent_kafka import Consumer, OFFSET_BEGINNING
import json
from producer import proceed_to_deliver
import base64
import subprocess

UPDATE_CWD = "updater/"
STORAGE_PATH = "tmp/"
UPDATE_SCRIPT_NAME = "./update-and-restart-app.sh"
APP_PATH = "../app/"


def execute_update(id, details):
    # print(f"[debug]===== EXECUTING UPDATE ====\nDetails: {details}")    
    print(f"[info]===== EXECUTING UPDATE {id} ====")    
    update_payload_b64 = details['blob']
    if details['update_file_encoding'] != 'base64':
        print('[error] unsupported blob encoding')
        return
    update_payload = base64.b64decode(update_payload_b64)
    try:
        with open(UPDATE_CWD+STORAGE_PATH+id, "wb") as f:
            f.write(update_payload)
        f.close()
        result = subprocess.call(['bash', '-c', f"{UPDATE_SCRIPT_NAME} {STORAGE_PATH+id} {APP_PATH}"], cwd=UPDATE_CWD)
        print(f"[info] update result code {result}")
    except Exception as e:
        print(f'[error] failed to execute update: {e}. cwd: {os.getcwd()}')
    


def handle_event(id: str, details: dict):
    # print(f"[debug] handling event {id}, {details}")
    print(f"[info] handling event {id}, {details['source']}->{details['deliver_to']}: {details['operation']}")
    delivery_required = False
    try:
        if details['operation'] == 'proceed_with_update':
            # it's a request from manager for an update
            # get the blob by its id
            details['deliver_to'] = 'storage'
            details['operation'] = 'get_blob'
            delivery_required = True
            
        elif details['operation'] == 'blob_content':
            # blob with an update arrived
            execute_update(id, details)
    except Exception as e:
        print(f"[error] failed to handle request: {e}")
    if delivery_required:
        proceed_to_deliver(id, details)



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
    topic = "updater"
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
                        f"Malformed event received from topic {topic}: {msg.value()}. {e}")
    except KeyboardInterrupt:
        pass
    finally:
        # Leave group and commit final offsets
        verifier_consumer.close()


def start_consumer(args, config):
    threading.Thread(target=lambda: consumer_job(args, config)).start()


if __name__ == '__main__':
    start_consumer(None)
