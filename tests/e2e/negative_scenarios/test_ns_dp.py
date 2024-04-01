from pytest import fixture
from time import sleep
import subprocess
import json
from urllib.request import urlopen, Request

from .monitor_events_analyzer import MonitorEventsAnalyzer
from ..test_alerts import headers, send_raw_data, request_new_alerts

FAKE_SERVICE_CONTROL_URL = "http://localhost:6100"
FAKE_SERVICE_NAME = 'fake_service'
FAKE_SERVICE_INSTANCE = None

# fake service will set current threshold to 200 and temperature threshold to 1000
RAW_SUPER_BAD_DATA = [
    {
        "param_name": "current",
        "param_units": "A",
        "param_value": 160 # still ok
    },
    {
        "param_name": "temperature",
        "param_units": "C",
        "param_value": 1500 # alert must be created
    }
]

def setup_module(module):
    assert module is not None
    

def teardown_module():
    print(f"stopping fake service {FAKE_SERVICE_INSTANCE}..")
    if FAKE_SERVICE_INSTANCE is not None:
        subprocess.run(["docker", "stop", FAKE_SERVICE_INSTANCE])
        subprocess.run(["docker", "rm", "-f", FAKE_SERVICE_INSTANCE])        
    else:
        subprocess.run(["docker", "stop", FAKE_SERVICE_NAME])
    print("done")

@fixture(autouse=True, scope='session')
def mea():
    # print("[debug] configuring mea")
    analyzer = MonitorEventsAnalyzer()
    analyzer.start_consumer()
    yield analyzer
    analyzer.shutdown()
    # print("[debug] releasing mea")


@fixture(autouse=True, scope="function")
def flush_alerts():
    # automatically clear all past alerts before each test
    request_new_alerts()
    # print("[debug] alerts flushed")
    return True

@fixture
def new_event_id():
    response = send_raw_data(RAW_SUPER_BAD_DATA)    
    return response["id"]


def test_dp_mea(mea):
    assert mea is not None


# def test_ns_feed_data(new_event_id, mea: MonitorEventsAnalyzer):
#     assert new_event_id is not None
#     expected_event = {
#         "source": "data_input",
#         "deliver_to": "data_processor",
#         "operation": "process_new_data",
#         "id": new_event_id
#     }
#     assert mea.wait_event(expected_event, timeout_s=5) is True


@fixture(scope='session')
def fake_service():
    # print("[debug] requested fake service start")
    # check if the fake service is already running
    dc = subprocess.Popen(("docker-compose", "ps"), stdout=subprocess.PIPE)
    
    try:
        output = subprocess.check_output(('grep', FAKE_SERVICE_NAME), stdin=dc.stdout).decode()
    except:
        output = ""
    dc.wait()
    
    if "Up" not in output:
        # the fake service is not running yet, so run it now
        dc = subprocess.Popen(("docker-compose", "run", "-d", "-p",
                    "6100:6100", FAKE_SERVICE_NAME), stdout=subprocess.PIPE)
        
        global FAKE_SERVICE_INSTANCE
        FAKE_SERVICE_INSTANCE = dc.stdout.read().decode().replace('\n', '')

        retries = 10
        req = Request(FAKE_SERVICE_CONTROL_URL + "/modes", headers=headers())
        while retries > 0:
            try:
                resp = urlopen(req)            
                if resp.getcode() == 200:
                    break
                else:
                    sleep(1)
                    retries -= 1
            except:
                sleep(1)
                retries -= 1
        if retries == 0:
            teardown_module()
            assert retries > 0
    

    yield FAKE_SERVICE_CONTROL_URL


@fixture
def fake_dp_modify_payload(fake_service):    
    assert fake_service is not None
    mode = {
        "fake_services": ["data_processor"],
        "active_modifiers": ["modify_payload"]
    }
    # stop the original service if it's running
    subprocess.run(["docker-compose", "stop", "data_processor"])
    req = Request(fake_service + "/mode",
                  data=json.dumps(mode).encode(), headers=headers())
    resp = urlopen(req)
    resp_data = resp.read().decode()
    data = json.loads(resp_data.replace("\\n", " "))
    assert data is not None
    assert resp.getcode() == 200
    yield resp
    # start the original service
    subprocess.run(["docker-compose", "start", "data_processor"])


def check_modified_payload(mea: MonitorEventsAnalyzer, id):
    expected_event = {
        "source": "data_processor",
        "deliver_to": "data_output",
        "operation": "process_new_events",
        "id": id
    }
    assert mea.wait_event(expected_event, timeout_s=60) is True

    # now check the alerts
    alerts = request_new_alerts()        
    # there can be also past alerts, check the one(s) with expected id
    assert len(alerts) > 0
    alert_found = False
    for alert in alerts:
        assert alert_found is False # we expect only one alert in this test!
        if alert["source_id"] == id:
            assert alert["event"] == "overheating"
            assert alert["temperature_threshold"] == 1000
            assert alert["temperature_value"] == RAW_SUPER_BAD_DATA[1]["param_value"]
            alert_found = True
    assert alert_found



def test_fake_dp_modify_payload(fake_dp_modify_payload, mea: MonitorEventsAnalyzer, new_event_id):    
    assert fake_dp_modify_payload is not None
    assert mea is not None
    assert new_event_id is not None
    # common_dp_recovery_checks(mea=mea, id=new_event_id)
    check_modified_payload(mea=mea, id=new_event_id)
