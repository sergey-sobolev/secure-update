import multiprocessing
from flask import Flask, request, jsonify
from uuid import uuid4
import threading

host_name = "0.0.0.0"
port = 5002

app = Flask(__name__)             # create an app instance

APP_VERSION = "1.0.2"

_requests_queue: multiprocessing.Queue = None

@app.route("/update", methods=['POST'])
def update():
    content = request.json
    auth = request.headers['auth']
    if auth != 'very-secure-token':
        return "unauthorized", 401

    req_id = uuid4().__str__()

    try:
        update_details = {
            "id": req_id,
            "operation": "download_file",
            "target": content['target'],
            "url": content['url'],
            "deliver_to": "downloader",
            "digest": content['digest'],
            "digest_alg": content['digest_alg']
            }
        _requests_queue.put(update_details)
        print(f"update event: {update_details}")
    except:
        error_message = f"malformed request {request.data}"
        print(error_message)
        return error_message, 400
    return jsonify({"operation": "update requested", "id": req_id})

def start_rest(requests_queue):
    global _requests_queue 
    _requests_queue = requests_queue
    threading.Thread(target=lambda: app.run(host=host_name, port=port, debug=True, use_reloader=False)).start()

if __name__ == "__main__":        # on running python app.py
    start_rest()