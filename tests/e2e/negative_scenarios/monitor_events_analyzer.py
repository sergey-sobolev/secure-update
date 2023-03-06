from time import sleep
from .events_analyzer_base import EventsAnalyzer



class MonitorEventsAnalyzer(EventsAnalyzer):

    def __init__(self) -> None:
        super().__init__()
        self._topic_name = 'monitor'
        self._events_cache = []

    def handle_event(self, id: str, details: dict):
        # print(
        #     f"[debug] [MEA]: handle event {id}, {details}")
        self._events_cache.append(details)

    def event_present(self, event):
        if len(self._events_cache) == 0:
            return False
        matches = 0

        for e in self._events_cache:
            for key, value in event.items():
                if key in e and e[key] != value:
                    matches = 0
                    # print(f"[debug] event doesn't match: expected {event}, received {e}")
                    break
                else:
                    matches += 1
            if matches == len(event.items()):
                break
        if matches > 0:
            # print(f"[debug] event present: expected {event}, received {e}")
            return True
        return False

    def wait_event(self, event: dict, timeout_s: int):
        # print(f"[debug] waiting for {event}")
        while timeout_s > 0:
            if self.event_present(event):
                return True                
            else:
                sleep(1.0)
                timeout_s -= 1
        # timeout
        return False
