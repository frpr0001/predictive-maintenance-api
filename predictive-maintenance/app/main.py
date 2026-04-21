from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import sqlite3
import logging

# --- Logging setup ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Intelligent IoT Solutions – Predictive Maintenance API - wup wup",
    description="REST API Microservice til modtagelse af sensordata og detektion af anomalier.",
    version="1.0.0"
)

DB_PATH = "data/events.db"

# --- Threshold config ---
THRESHOLDS = {
    "temperature": {"min": 0.0,  "max": 85.0},
    "vibration":   {"min": 0.0,  "max": 5.0},
    "pressure":    {"min": 0.5,  "max": 10.0},
}

# --- Pydantic models ---
class SensorReading(BaseModel):
    device_id: str = Field(..., example="sensor-42")
    sensor_type: str = Field(..., example="temperature")
    value: float = Field(..., example=92.5)
    unit: str = Field(..., example="celsius")

class SensorResponse(BaseModel):
    event_id: int
    device_id: str
    sensor_type: str
    value: float
    unit: str
    status: str           # "OK" or "ALARM"
    message: str
    timestamp: str

# --- DB helpers ---
def get_db():
    import os
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sensor_events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id   TEXT NOT NULL,
            sensor_type TEXT NOT NULL,
            value       REAL NOT NULL,
            unit        TEXT NOT NULL,
            status      TEXT NOT NULL,
            message     TEXT NOT NULL,
            timestamp   TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialized")

@app.on_event("startup")
def startup():
    init_db()

# --- Business logic ---
def check_threshold(sensor_type: str, value: float) -> tuple[str, str]:
    """Returns (status, message)"""
    limits = THRESHOLDS.get(sensor_type)
    if limits is None:
        return "OK", f"Ingen threshold konfigureret for '{sensor_type}' – værdi accepteret."
    if value < limits["min"] or value > limits["max"]:
        return (
            "ALARM",
            f"ANOMALI DETEKTERET: {sensor_type} = {value} er uden for grænseværdi "
            f"[{limits['min']}, {limits['max']}]"
        )
    return "OK", f"Sensorværdi inden for normal grænse [{limits['min']}, {limits['max']}]."

# --- Endpoints ---
@app.get("/", tags=["Health"])
def root():
    return {"status": "running", "service": "Predictive Maintenance API"}

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/sensor-data", response_model=SensorResponse, tags=["Sensor Events"])
def receive_sensor_data(reading: SensorReading):
    """
    Modtag sensordata fra IoT-device.
    Tjekker threshold og gemmer event i databasen.
    Returnerer status OK eller ALARM.
    """
    if reading.sensor_type not in ["temperature", "vibration", "pressure"]:
        raise HTTPException(
            status_code=400,
            detail=f"Ukendt sensor_type '{reading.sensor_type}'. Tilladt: temperature, vibration, pressure."
        )

    status, message = check_threshold(reading.sensor_type, reading.value)
    timestamp = datetime.utcnow().isoformat()

    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO sensor_events (device_id, sensor_type, value, unit, status, message, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (reading.device_id, reading.sensor_type, reading.value, reading.unit, status, message, timestamp)
    )
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()

    logger.info(f"Event #{event_id} | {reading.device_id} | {reading.sensor_type}={reading.value} | {status}")

    return SensorResponse(
        event_id=event_id,
        device_id=reading.device_id,
        sensor_type=reading.sensor_type,
        value=reading.value,
        unit=reading.unit,
        status=status,
        message=message,
        timestamp=timestamp
    )

@app.get("/events", tags=["Events"])
def get_all_events(limit: int = 50):
    """Hent de seneste sensor events fra databasen."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM sensor_events ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/alarms", tags=["Events"])
def get_alarms(limit: int = 50):
    """Hent kun events med status = ALARM."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM sensor_events WHERE status='ALARM' ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/events/{event_id}", tags=["Events"])
def get_event(event_id: int):
    """Hent ét specifikt event via ID."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM sensor_events WHERE id=?", (event_id,)
    ).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Event ikke fundet.")
    return dict(row)
