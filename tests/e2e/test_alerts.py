from pytest import fixture
from time import sleep
import json
from urllib.request import urlopen, Request

DATA_INPUT_URL = "http://localhost:6000/ingest"
DATA_OUTPUT_URL = "http://localhost:6001/alerts"
AUTH_TOKEN = "very-secure-token"

RAW_TEST_FIELD_DATA = [
    {
        "param_name": "current",
        "param_units": "A",
        "param_value": 260
    },
    {
        "param_name": "temperature",
        "param_units": "C",
        "param_value": 500
    }
]


def headers():
    return {'content-type': 'application/json', 'auth': AUTH_TOKEN}


def send_raw_data(data: list) -> dict:    
    req = Request(DATA_INPUT_URL, data=json.dumps(
        data).encode(), headers=headers())
    response = urlopen(req)
    assert response.getcode() == 200
    result = json.loads(response.read().decode())
    id = result["id"]
    # print(f"[debug] new event sent, id {id}")
    return result


def request_new_alerts() -> list:    
    req = Request(DATA_OUTPUT_URL, headers=headers())
    response = urlopen(req)
    assert response.getcode() == 200
    return json.loads(response.read().decode())


def test_detect_alerts():
    # read alerts to flush past notifications
    request_new_alerts()

    # now send new events
    result = send_raw_data(RAW_TEST_FIELD_DATA)
    assert result["operation"] == "new data received"

    # store the request id and check it for new alerts
    id = result["id"]

    # let the system to process the new event
    retries = 20
    while retries > 0:
        sleep(0.5)
        alerts = request_new_alerts()
        if alerts != []:
            break
        else:
            retries -= 1            
    assert retries > 0    
    assert len(alerts) == 2

    for alert in alerts:
        assert alert["source_id"] == id

    assert alerts[0]["event"] == "overload"
    assert alerts[1]["event"] == "overheating"
