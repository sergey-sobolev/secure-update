import multiprocessing
from flask import Flask, request, jsonify
from uuid import uuid4
import threading
import os
from dotenv import load_dotenv

load_dotenv()

host_name = "0.0.0.0"
port = os.getenv("DATA_OUTPUT_API_PORT", default=5006)

app = Flask(__name__)             # create an instance

_events_queue: multiprocessing.Queue = None

@app.route("/events", methods=['GET'])
def get_events():    
    if 'auth' not in request.headers:
        return "unauthorized", 401
    auth = request.headers['auth']    
    if auth != 'very-secure-token':
        return "unauthorized", 401

    events = []
    while True:
        try:        
            event = _events_queue.get_nowait()    
            # extract alerts only, if any
            events.append(event["alerts"])
        except:
            # no events
            break              
    return jsonify(events)

def start_rest(events_queue):
    global _events_queue 
    _events_queue = events_queue
    threading.Thread(target=lambda: app.run(host=host_name, port=port, debug=True, use_reloader=False)).start()

if __name__ == "__main__":        # on running python app.py
    start_rest()