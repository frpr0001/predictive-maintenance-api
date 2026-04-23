import pytest
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Brug en test-database
os.environ["TESTING"] = "1"

from app.main import app, DB_PATH
import app.main as main_module

# Overskriv DB_PATH til test-database
main_module.DB_PATH = ":memory:"

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "running" in r.json()["status"]

def test_sensor_ok():
    r = client.post("/sensor-data", json={
        "device_id": "sensor-01",
        "sensor_type": "temperature",
        "value": 45.0,
        "unit": "celsius"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "OK"
    assert data["device_id"] == "sensor-01"

def test_sensor_alarm_temperature():
    r = client.post("/sensor-data", json={
        "device_id": "sensor-02",
        "sensor_type": "temperature",
        "value": 120.0,
        "unit": "celsius"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ALARM"

def test_sensor_alarm_vibration():
    r = client.post("/sensor-data", json={
        "device_id": "sensor-03",
        "sensor_type": "vibration",
        "value": 9.9,
        "unit": "m/s2"
    })
    assert r.status_code == 200
    assert r.json()["status"] == "ALARM"

def test_invalid_sensor_type():
    r = client.post("/sensor-data", json={
        "device_id": "sensor-04",
        "sensor_type": "humidity",
        "value": 80.0,
        "unit": "%"
    })
    assert r.status_code == 400

def test_get_events():
    r = client.get("/events")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_get_alarms():
    r = client.get("/alarms")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_event_not_found():
    r = client.get("/events/99999")
    assert r.status_code == 404
