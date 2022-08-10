# implements Kafka topic consumer functionality

import threading
from confluent_kafka import Consumer, OFFSET_BEGINNING
import json
from producer import proceed_to_deliver
import base64
from hashlib import sha256


def verify_payload(details) -> bool:
    payload_digest = sha256()
    update_payload_b64 = details['blob']
    update_payload = base64.b64decode(update_payload_b64)
    # update_payload = details['blob']
    if details['digest_alg'] != 'sha256':
        print(f"[error] unsupported digest alg {details['digest_alg']}")
        return False
    payload_digest.update(update_payload)
    hexdigest = payload_digest.hexdigest()
    if hexdigest != details['digest']:
        print(
            f"[warning] digest verification failed, actual {hexdigest}, expected {details['digest']}")
        return False
    return True


def cleanup_extra_fields(details):
    # remove the blob content from the message payload before sending
    del details['blob']
    # also remove digest details as it will not be further used
    del details['digest_alg']
    del details['digest']


def handle_event(id, details_str):
    details = json.loads(details_str)
    # print(f"[debug] handling event {id}, {details}")
    print(f"[info] handling event {id}, {details['source']}->{details['deliver_to']}: {details['operation']}")
    try:
        delivery_required = False
        if details['operation'] == 'verification_requested':
            # get the blob for verification from storage
            details['deliver_to'] = 'storage'
            details['operation'] = 'get_blob'
            # we need to remember who asked for verification, 
            # store this information in the message itself
            details['verification_requester'] = details['source']
            delivery_required = True
        elif details['operation'] == 'blob_content':
            # got the blob from storage, verify and notify manager
            verified = verify_payload(details)
            cleanup_extra_fields(details)
            details['operation'] = 'handle_verification_result'
            details['verified'] = verified
            if not verified:
                print('[error] !!! update payload verification failed !!!\n'\
                      f"{details}")
            try:
                # try to send verification result to the original requester                
                details['deliver_to'] = details['verification_requester']
                # if the field is present, remove it, it's not needed anymore
                del details['verification_requester']
                delivery_required = True
            except:
                # we don't know who asked for verification, so drop this result
                # by default status if 'not verified', so no security risk here
                print("[warning] no information about verification requester found")                        
        if delivery_required:
            proceed_to_deliver(id, details)
        else:
            print(f"[warning] unknown operation!\n{details}")
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
    topic = "verifier"
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
                    details_str = msg.value().decode('utf-8')
                    # print("[debug] Consumed event from topic {topic}: key = {key:12} value = {value:12}".format(
                    #     topic=msg.topic(), key=id, value=details_str))
                    handle_event(id, details_str)
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
