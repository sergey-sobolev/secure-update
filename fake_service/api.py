from flask import Flask, request, jsonify
import threading
from fake_handlers_list import FakeDPHandler
from fake_handler_base import FakeHandler


host_name = "0.0.0.0"
port = 6100

app = Flask(__name__)             # create an app instance

_fake_services = {}
_supported_fake_handlers = {
    "data_processor": FakeDPHandler
}
_broker_config = None

@app.route("/modes", methods=['GET'])
def get_supported_modes():    
    handlers = []
    for h, _ in _supported_fake_handlers.items():
        handlers.append(h)
    return jsonify(handlers), 200


@app.route("/mode", methods=['POST'])
def change_faking_mod():
    content = request.json
    
    try:
        print(f"[info] requested faking mode change: {content}")
        f_services = content['fake_services']        
        for f_service in f_services:
            if f_service not in _fake_services:
                # create missing fake service
                print(f"[debug] shall create fake {f_service}")
                handler = _supported_fake_handlers[f_service]()
                handler.start_consumer(_broker_config)
            else:
                # modify existing fake service behavior
                handler = _fake_services[f_service]
            if 'active_modifiers' in content:
                handler.set_active_modifiers(content['active_modifiers'])
                
                
    except Exception as e:
        error_message = f"malformed request {request.data}: {e}"
        print(error_message)
        return error_message, 400

    # queue = get_requested_events_queue()
    # events_cache = {}
    # try:
    #     events = queue.get()  # will block until data is received
    #     for event in events:
    #         events_cache[event["id"]] = event
    # except Exception as e:
    #     return e, 500
    # return jsonify(events_cache)
    return jsonify({"fake_mode_change": "accepted"}), 200


def start_rest(broker_config):
    global _broker_config
    _broker_config = broker_config
    threading.Thread(target=lambda: app.run(host=host_name, port=port, debug=True, use_reloader=False)).start()


if __name__ == "__main__":        # on running python app.py
    start_rest()