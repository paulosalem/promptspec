# FieldPulse — IoT Agricultural Monitoring Platform

@refine programming/base-spec-author.promptspec.md
@refine programming/stack-python-fastapi-postgres.promptspec.md
@refine programming/type-saas-webapp.promptspec.md
@refine programming/module-auth.promptspec.md
@refine programming/module-rest-api.promptspec.md
@refine programming/module-realtime.promptspec.md
@refine programming/module-notifications.promptspec.md
@refine programming/module-ai-features.promptspec.md

@audience "backend/IoT engineer implementing from this spec"
@style "precise, systems-oriented, handles edge cases"

## Product Vision

FieldPulse is an **IoT-powered agricultural monitoring platform** that collects
sensor data from fields (soil moisture, temperature, humidity, light, pH),
visualizes it in real-time dashboards, and uses ML models to generate actionable
irrigation and fertilization recommendations. Targets small-to-mid farms
(10–500 acres) with 50–5000 sensors.

## Data Ingestion

### Sensor Protocol
- Sensors communicate via MQTT (QoS 1) to a broker (Mosquitto/EMQX).
- Topic format: `fieldpulse/{farm_id}/sensors/{sensor_id}/data`
- Payload (JSON):
  ```json
  {
    "ts": "2025-01-15T10:30:00Z",
    "readings": {
      "soil_moisture": 42.5,
      "temperature_c": 22.3,
      "humidity_pct": 65.0,
      "light_lux": 48000,
      "ph": 6.8
    },
    "battery_pct": 87,
    "signal_rssi": -72
  }
  ```
- Ingestion rate: sensors report every 5 minutes. System MUST handle 5000 sensors
  × 12 readings/hour = 60,000 messages/hour sustained.

### Data Pipeline
- MQTT subscriber → validates schema → writes to TimescaleDB hypertable.
- Hypertable: `sensor_readings`, partitioned by time (1-day chunks).
- Retention: raw data 90 days, hourly aggregates 2 years, daily aggregates indefinitely.
- Continuous aggregates (TimescaleDB): hourly and daily rollups computed automatically.
- Dead sensor detection: if no reading received for 30 minutes, mark sensor `status: offline`
  and trigger alert.

### Sensor Management
- Registration: admin adds sensor with `(sensor_id, type, field_id, location_lat, location_lng, depth_cm)`.
- Calibration: each sensor type has calibration coefficients stored in DB.
  Raw reading × coefficient = calibrated value.
- Battery alerts: warn at 20%, critical at 10%.

## Field & Zone Management

- A **farm** has multiple **fields** (named areas, e.g., "North Wheat Field").
- A **field** has multiple **zones** (subdivisions for granular management).
- Each **zone** has assigned sensors and a **crop profile** (crop type, planting date,
  expected harvest, growth stage).
- Map view: satellite/aerial imagery with zone boundaries drawn as GeoJSON polygons.
  Sensors shown as pins colored by status (green=ok, yellow=warning, red=alert).

## Intelligent Recommendations

@if include_ml
  ### Irrigation Engine
  - Inputs: soil moisture (current + 24h trend), weather forecast (API: OpenWeatherMap),
    crop water requirements (lookup table by crop + growth stage), soil type.
  - Output: per-zone recommendation: "irrigate X mm within next Y hours" or "no action needed".
  - Model: gradient-boosted decision tree trained on historical yield + irrigation data.
  - Fallback (no model): rule-based thresholds per crop type.
  - Recommendations refresh every 6 hours or on-demand.

  ### Anomaly Detection
  - Detect: sudden drops in soil moisture (pipe leak?), temperature spikes (sensor malfunction?),
    pH drift (contamination?).
  - Method: z-score against rolling 7-day window per sensor. Threshold: |z| > 3.
  - On anomaly: create alert, notify farm manager, flag reading in dashboard.

  ### Yield Prediction
  - Weekly yield estimate per field based on sensor data + weather + historical harvests.
  - Confidence interval: show as range bar in dashboard.
  - Accuracy tracking: after harvest, compare prediction to actual; retrain if error > 15%.

## Real-Time Dashboard

@expand
  - Live sensor map with zone health heatmap overlay (interpolated from sensor readings).
  - Per-zone detail view: line charts for each reading type (last 24h, 7d, 30d).
  - Alert timeline: chronological feed of all alerts with status (new, acknowledged, resolved).
  - Weather widget: current conditions + 5-day forecast for farm location.
  - Irrigation schedule: calendar view showing past and recommended future irrigation events.

## Alerting

- Alert rules configurable per zone:
  `"Soil moisture in Zone A drops below 25%"` → notify via push + email.
- Escalation: if alert not acknowledged within 1 hour, escalate to farm owner.
- Quiet hours: suppress non-critical alerts between 10 PM – 6 AM (configurable).

@match deployment_mode
  "cloud" ==>
    ## Cloud Deployment
    - AWS: ECS Fargate for API, RDS for PostgreSQL, ElastiCache for Redis,
      Amazon MQ for MQTT broker, S3 for satellite imagery tiles.
    - Auto-scaling: API scales 2–10 containers based on CPU > 70%.
    - CDN: CloudFront for static assets and map tiles.

  "edge" ==>
    ## Edge + Cloud Hybrid Deployment
    - Edge gateway (Raspberry Pi 4 or similar) at each farm:
      runs MQTT broker, local data buffer (SQLite), and alerting engine.
    - Edge syncs to cloud every 5 minutes (or immediately for critical alerts).
    - Offline resilience: edge operates independently for up to 72 hours.
    - Cloud: same as cloud mode but receives pre-aggregated data from edge.
    - Conflict resolution: edge timestamp is authoritative; cloud deduplicates by sensor_id + ts.

  _ ==>
    ## Default Deployment
    - Docker Compose for single-server deployment (development and small farms).
    - All services (API, worker, MQTT broker, PostgreSQL, Redis) in one compose file.

@assert "Every sensor reading type must specify units, valid range, and calibration method"
@assert "The data pipeline must specify throughput capacity and retention policy"
@assert "ML recommendations must include a rule-based fallback for when models are unavailable"

@output_format "markdown"
  Structure the output as:
  1. System Architecture (diagram description + component list)
  2. Data Models (all tables with full schemas, including TimescaleDB hypertables)
  3. MQTT Topics & Message Schemas
  4. API Endpoints (sensor management, field/zone CRUD, readings query, recommendations)
  5. Real-Time & WebSocket Events
  6. ML Pipeline (training data, model serving, fallback logic)
  7. Alerting Rules Engine
  8. Deployment Configurations (per deployment_mode)
  9. Testing Strategy (unit, integration, load testing for ingestion pipeline)
