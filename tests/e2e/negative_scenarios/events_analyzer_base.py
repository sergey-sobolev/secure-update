from confluent_kafka import Consumer
import threading
import os
from multiprocessing import Queue
import json
from configparser import ConfigParser


class EventsAnalyzer:

    def __init__(self) -> None:
        self._consumer = None
        self._topic_name = None
        self._control_events_queue = Queue()
        self._fake_behavior = {}
        self._active_modifiers = []
        self._shutdown = False

    def handle_event(self, id: str, details: dict):
        print(
            f"[debug] base class method executed: handle event {id}, {details}")

    def _process_control_event(self, event):
        pass

    def _consumer_job(self, config):
        config["socket.timeout.ms"] = 1200
        config["fetch.wait.max.ms"] = 200
        consumer = Consumer(config)
        # Subscribe to topic, by default it will be monitor
        if self._topic_name is None:
            topic = "monitor"
        else:
            topic = self._topic_name
        consumer.subscribe([topic])

        # Poll for new messages from Kafka and print them.
        try:
            while not self._shutdown:
                msg = consumer.poll(0.5)
                if msg is None:
                    pass
                elif msg.error():
                    print(f"[error] {msg.error()}")
                else:
                    try:
                        id = msg.key().decode('utf-8')
                        details = json.loads(msg.value().decode('utf-8'))
                        self.handle_event(id, details)
                    except Exception as e:
                        print(
                            f"[error] malformed event received from topic {topic}: {msg.value()}. {e}")
        except KeyboardInterrupt:
            pass
        finally:
            # Leave group and commit final offsets
            consumer.close()
        # print("[debug] consumer stopped")

    def start_consumer(self, config: dict or None = None, config_name="config.ini", group_id="monitor"):
        if config is None:
            try:
                config_parser = ConfigParser()
                with open(config_name, "r") as cf:
                    config_parser.read_file(cf)
                    config = dict(config_parser['default'])
                    config["group.id"] = group_id
            except Exception as e:
                print(
                    f"[error] failed to read config: {e}. File: {config_name}, wd: {os.getcwd()}")
                raise e
        threading.Thread(target=lambda: self._consumer_job(config)).start()

    def shutdown(self):
        self._shutdown = True
