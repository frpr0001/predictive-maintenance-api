# 🔧 Predictive Maintenance API
**Intelligent IoT Solutions A/S** – REST API Microservice

## Hvad gør det?
Modtager sensordata fra IoT-devices, tjekker grænseværdier og returnerer OK eller ALARM. Alle events gemmes i en SQLite database.

## Kom hurtigt i gang

### Kør lokalt med Docker
```bash
docker-compose up --build
```
API tilgængeligt på: http://localhost:8000

### Kør uden Docker
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API Endpoints

| Method | URL | Beskrivelse |
|--------|-----|-------------|
| GET | `/` | Status |
| GET | `/health` | Health check |
| POST | `/sensor-data` | Send sensordata |
| GET | `/events` | Alle events |
| GET | `/alarms` | Kun alarmer |
| GET | `/events/{id}` | Ét specifikt event |

## Eksempel – Postman / curl

**Send sensordata:**
```bash
curl -X POST http://localhost:8000/sensor-data \
  -H "Content-Type: application/json" \
  -d '{"device_id": "sensor-42", "sensor_type": "temperature", "value": 95.0, "unit": "celsius"}'
```

**Svar (ALARM):**
```json
{
  "event_id": 1,
  "device_id": "sensor-42",
  "sensor_type": "temperature",
  "value": 95.0,
  "unit": "celsius",
  "status": "ALARM",
  "message": "ANOMALI DETEKTERET: temperature = 95.0 er uden for grænseværdi [0.0, 85.0]",
  "timestamp": "2025-04-21T10:00:00"
}
```

## Threshold-regler

| Sensor | Min | Max | Enhed |
|--------|-----|-----|-------|
| temperature | 0.0 | 85.0 | celsius |
| vibration | 0.0 | 5.0 | m/s² |
| pressure | 0.5 | 10.0 | bar |

## Kør tests
```bash
pytest tests/ -v
```

## Automatisk dokumentation
FastAPI genererer automatisk Swagger UI: http://localhost:8000/docs
