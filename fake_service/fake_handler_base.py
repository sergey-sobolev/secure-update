from confluent_kafka import Consumer
import threading
from multiprocessing import Queue
import json


class FakeHandler:

    def __init__(self, consumer: Consumer or None = None) -> None:
        self._consumer = None
        self._topic_name = None
        self._control_events_queue = Queue()
        self._fake_behavior = {}
        self._active_modifiers = []

    def set_active_modifiers(self, modifiers):
        print(f"[debug][FH] changing active modifiers to {modifiers}")
        self._active_modifiers = modifiers

    def queue_control_event(self, event):
        self._control_events_queue.put(event)

    def handle_event(id: str, details: dict):
        print(
            f"[debug] base class method executed: handle event {id}, {details}")

    def _process_control_event(self, event):
        pass

    def _consumer_job(self, config):
        consumer = Consumer(config)
        # Subscribe to topic, by default it will be monitor
        if self._topic_name is None:
            topic = "monitor"
        else:
            topic = self._topic_name
        consumer.subscribe([topic])

        # Poll for new messages from Kafka and print them.
        try:
            while True:
                try:
                    control_event = self._control_events_queue.get_nowait()
                except:
                    control_event = None
                if control_event is not None \
                        and control_event["scope"] == "consumer" \
                        and control_event["type"] == "subscription_control" \
                        and control_event["command"] == "stop":
                    print("[info] requested subscriber thread stop")
                    break
                else:
                    self._process_control_event(control_event)

                msg = consumer.poll(1.0)
                if msg is None:
                    pass
                elif msg.error():
                    print(f"[error] {msg.error()}")
                else:
                    try:
                        id = msg.key().decode('utf-8')
                        details = json.loads(msg.value().decode('utf-8'))
                        if self._event_handler is not None:
                            self._event_handler(id, details)
                    except Exception as e:
                        print(
                            f"[error] malformed event received from topic {topic}: {msg.value()}. {e}")
        except KeyboardInterrupt:
            pass
        finally:
            # Leave group and commit final offsets
            consumer.close()
        print("[info] consumer stopped")

    def start_consumer(self, config):
        threading.Thread(target=lambda: self._consumer_job(config)).start()
