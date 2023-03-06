from fake_handler_base import FakeHandler
from producer import proceed_to_deliver


class FakeDPHandler(FakeHandler):

    def __init__(self) -> None:
        super().__init__()
        self._topic_name = "data_processor"
        self._fake_behavior = {
            "remove_payload": self._modifier_remove_payload,
            "modify_payload": self._modifier_modify_payload
        }
        self._active_modifiers = []

    def _modifier_remove_payload(self, details):
        print(f"[debug][FDP] want to remove some payload parts from msg {details['id']}")
        delivery_requested = False
        try:
            # remove the photo
            del details['payload']['photo']
            details['source'] = details['deliver_to']
            details['deliver_to'] = 'events_service'
            details['operation'] = 'process_event'
            delivery_requested = True
        except Exception as e:
            print(f"[error][FDP] failed to apply the modification {e}")
        return delivery_requested

    def _modifier_modify_payload(self, details):
        # use modified thresholds
        CURRENT_THRESHOLD = 200
        TEMPERATURE_THRESHOLD = 1000
        
        print(f"[debug][FDP] want to modify some payload parts from msg {details['id']}")
        delivery_requested = False
        try:
            
            details["alerts"] = []
            data = details['new_data']
            for sample in data:
                if "param_name" in sample: 
                    if sample["param_name"] == "current":
                        current = sample["param_value"]
                        if current > CURRENT_THRESHOLD:
                            details["alerts"].append(
                                {
                                    "source_id": details["id"],
                                    "event": "overload",
                                    "current_value": current,
                                    "current_threshold": CURRENT_THRESHOLD
                                }
                            )
                    elif sample["param_name"] == "temperature":
                        temperature = sample["param_value"]
                        if temperature > TEMPERATURE_THRESHOLD:
                            details["alerts"].append(
                                {
                                    "source_id": details["id"],
                                    "event": "overheating",
                                    "temperature_value": temperature,
                                    "temperature_threshold": TEMPERATURE_THRESHOLD
                                }
                            )



            details['source'] = details['deliver_to']
            details['deliver_to'] = 'data_output'
            details['operation'] = 'process_new_events'
            delivery_requested = True
        except Exception as e:
            print(f"[error][FDP] failed to apply the modification {e}")
        return delivery_requested

    def _event_handler(self, id: str, details: dict):
        print(
            f"[info][FDP] handling event {id}, {details['source']}->{details['deliver_to']}: {details['operation']}")
        need_delivery = False
        for modifier in self._active_modifiers:
            try:
                need_delivery = need_delivery or self._fake_behavior[modifier](
                    details)
            except Exception as e:
                print(f"[error][FDP] modification failed: {e}")
        if need_delivery:
            proceed_to_deliver(id, details)

    def get_fake_dp_behavior(self):
        return self._fake_behavior
