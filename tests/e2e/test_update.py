from time import sleep
import pytest
import re
import json
from urllib.request import urlopen, Request
from uuid import uuid1

APP_URL = "http://localhost:5000"
FILE_SERVER_URL = "http://localhost:5001"
MANAGER_URL = "http://localhost:5002"

APP_UPDATE_FILE = "file_server/data/app-update.py"

def get_app_version() -> str:
    try:
        response = urlopen(APP_URL)
        data = response.read().decode().split(" ")[-1]
        return data
    except Exception as e:
        print(f"failed to access the application: {e}")
        raise e    

@pytest.fixture
def app_version() -> str:
    return get_app_version()


def test_app_version(app_version):
    assert app_version is not None


def get_update_version():
    with open(APP_UPDATE_FILE, "r") as f:
        version = None
        update_content = f.read()
        m = re.search("APP_VERSION = \"(.+)\"", update_content)
        if m:
            version = m.group(1)
        else:
            raise "version not found"
    return version


def set_update_version(version):
    old_ver = get_update_version()
    with open(APP_UPDATE_FILE, "r") as f:
        data = f.read()
        data = data.replace(old_ver, version)

    with open(APP_UPDATE_FILE, "w") as f:
        f.write(data)

    assert get_update_version() == version

@pytest.fixture
def update_app_version():
    orig_version = get_update_version()
    yield orig_version
    set_update_version(orig_version)


def test_update_app_file_version():
    with open(APP_UPDATE_FILE, "r") as f:
        app_update_version = None
        update_content = f.read()
        m = re.search("APP_VERSION = \"(.+)\"", update_content)
        if m:
            app_update_version = m.group(1)
            # print(app_update_version)
        else:
            print("version not found")
        assert app_update_version


def test_change_file_version(update_app_version):
    new_version = "e2e-test"
    assert update_app_version != new_version

    set_update_version(new_version)

    assert get_update_version() == new_version

def get_update_digest():
    GET_DIGEST_PATH = "/get-digest/app-update.zip"
    try:
        response = urlopen(FILE_SERVER_URL + GET_DIGEST_PATH)
        data = response.read().decode().split(" ")
        return data

    except Exception as e:
        print(f"failed to get update file digest: {e}")
        raise e


@pytest.fixture
def update_digest():
    digest = get_update_digest()
    return digest


def test_file_server_access(update_digest):
    # print(update_digest)
    assert update_digest is not None


def test_modified_digest(update_app_version, update_digest):    
    new_version = "e2e-test"
    assert update_app_version != new_version

    set_update_version(new_version)
    assert get_update_version() == new_version
    new_digest = get_update_digest()
    assert update_digest != new_digest

# manager test

def update_app_to_version(version, validate = True):
    FILE_SERVER_UPDATE_PATHNAME = "/download-update/app-update.zip"    
    FILE_SERVER_URL_DOCKER = "http://file_server:5001"
    MANAGER_UPDATE_PATH = "/update"
    # print(f"updating app to version {version}")
    set_update_version(version)    
    digest_str = get_update_digest()[0]
    header_auth_token = "very-secure-token"
    update_request_body = {
        "url": FILE_SERVER_URL_DOCKER+FILE_SERVER_UPDATE_PATHNAME, 
        "target": "app", 
        "digest": digest_str, 
        "digest_alg": "sha256"
    }
    headers = {'content-type': 'application/json', 'auth': header_auth_token}
    req = Request(MANAGER_URL+MANAGER_UPDATE_PATH, data=json.dumps(update_request_body).encode(), headers=headers)
    resp = urlopen(req)
    assert resp.getcode() == 200
    if validate is True:     
        # check if the requested version is set
        max_retries = 10
        app_version = None
        while max_retries > 0:
            sleep(0.5) 
            max_retries -= 1
            app_version = get_app_version()
            if app_version == version:
                break
        assert app_version == version
    

def test_successful_update(update_app_version, app_version):
    new_version = "e2e-test-" + str(uuid1())
    assert new_version != update_app_version
    assert new_version != app_version
    # will set and validate
    # print(f"changing target app version to {new_version}")
    update_app_to_version(new_version)
    # restore to the original version
    # print(f"restoring app to version {update_app_version}")
    update_app_to_version(update_app_version)

# hacked manager test