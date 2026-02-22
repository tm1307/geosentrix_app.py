# 🛰️ GeoSentrix Command Center

> **Mission-critical geotechnical tunnel monitoring system** built for Indian infrastructure operators — NHIDCL, Ministry of Railways, and RITES.

![System Status](https://img.shields.io/badge/System-Active-22c55e?style=for-the-badge&logo=statuspage)
![Flask](https://img.shields.io/badge/Flask-3.x-f59e0b?style=for-the-badge&logo=flask)
![ESP32](https://img.shields.io/badge/ESP32-Wokwi-06b6d4?style=for-the-badge&logo=espressif)
![License](https://img.shields.io/badge/License-MIT-white?style=for-the-badge)
![Compliance](https://img.shields.io/badge/IS:14268-Compliant-ef4444?style=for-the-badge)

---

## 📸 Overview

GeoSentrix Command Center is a real-time geotechnical monitoring dashboard that connects physical/simulated ESP32 sensors to a web-based mission control interface. It detects rock strain, pore water pressure, and structural movement in tunnels — and alerts engineers before failures occur.

Built for:
- 🏗️ **NHIDCL** tunnel projects
- 🚂 **Ministry of Railways** infrastructure
- 🛣️ **MoRT&H** highway tunnels

---

## ✨ Features

### 🖥️ Dashboard (`/`)
- **3D Tunnel Visualization** — Three.js rendered sector model (A, B, C) with real-time glow alerts
- **Live Charts** — Chart.js line graphs for Rock Strain (mm) and Pore Water Pressure (kPa)
- **MatrixCore AI** — Collapse probability ring with structural/hydro/seismic risk breakdown
- **Activity Feed** — Real-time sensor event log
- **Sensor Data Inject** — Manual POST panel for testing

### 📋 Inspection Module (`/inspection`)
- Full digital inspection form (IS:14268 compliant)
- IS:14268 checklist with live completion score
- Past inspection records with risk-coded history
- Field team roster and scheduled inspection calendar
- Digital sign & submit with auto-generated inspection ID

### 📡 Hardware Interface (`/hardware`)
- GeoScout device cards with battery, signal, and status
- Protocol switcher — MQTT / RS-485 / LoRa / HTTP REST
- Interactive terminal with live commands
- Live telemetry table (updates every 2 seconds)
- OTA firmware management panel

### 📄 Compliance Report (`/report`)
- Auto-generated PDF report
- Covers sensor data, inspection records, AI assessment, hardware status
- IS:14268 · IRC:SP:91 · NHIDCL SOP-GT-2021 · ISO 9001:2015 compliant

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   WOKWI SIMULATOR                   │
│   ESP32 + HC-SR04 Ultrasonic Sensor                 │
│   Detects rock wall movement → calculates strain    │
└────────────────────┬────────────────────────────────┘
                     │ POST /update (REST API)
                     │ {"sensor_id":"B-01",
                     │  "strain_value":3.2,
                     │  "vibration":0.4}
                     ▼
┌─────────────────────────────────────────────────────┐
│              FLASK BACKEND (Python)                 │
│   /         → Dashboard HTML                        │
│   /update   → Receives sensor data                  │
│   /api/state → Returns current sensor state         │
│   /inspection → Inspection module                   │
│   /hardware  → Hardware interface                   │
│   /report    → PDF generation (ReportLab)           │
└────────────────────┬────────────────────────────────┘
                     │ GET /api/state every 3s
                     ▼
┌─────────────────────────────────────────────────────┐
│              BROWSER DASHBOARD                      │
│   Three.js  → 3D tunnel visualization               │
│   Chart.js  → Real-time strain/pressure graphs      │
│   Fetch API → Polls /api/state for live data        │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- A Wokwi account (free) — [wokwi.com](https://wokwi.com)

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/geosentrix-command-center.git
cd geosentrix-command-center
```

### 2. Set up virtual environment
```bash
python3 -m venv geosentrix-env
source geosentrix-env/bin/activate  # Mac/Linux
# OR
geosentrix-env\Scripts\activate     # Windows
```

### 3. Install dependencies
```bash
pip install flask flask-cors reportlab
```

### 4. Run the server
```bash
python3 geosentrix_app.py
```

### 5. Open dashboard
```
http://localhost:5050
```

---

## 📡 Wokwi ESP32 Integration

### Hardware Setup (in Wokwi)
| Component | Pin |
|---|---|
| HC-SR04 TRIG | GPIO 5 |
| HC-SR04 ECHO | GPIO 18 |
| Red Alert LED | GPIO 2 |

### Step 1 — Get your local IP
```bash
ipconfig getifaddr en0      # Mac
ipconfig                    # Windows (look for IPv4)
```

### Step 2 — Wokwi sketch (`sketch.ino`)
```cpp
#include <WiFi.h>
#include <HTTPClient.h>

const int TRIG_PIN = 5;
const int ECHO_PIN = 18;
const int LED_PIN  = 2;

const char* ssid     = "Wokwi-GUEST";
const char* password = "";
const char* SERVER   = "http://YOUR_IP:5050/update";  // ← your IP here

float baseDistance = 0;
float threshold    = 2.0;
unsigned long lastSent = 0;

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN,  OUTPUT);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nWiFi Connected!");
  delay(500);
  baseDistance = getDistance();
}

void loop() {
  float current  = getDistance();
  float movement = abs(baseDistance - current);
  float strain   = constrain(movement, 0.0, 5.0);
  digitalWrite(LED_PIN, movement > threshold ? (millis()/250)%2 : LOW);
  if (millis() - lastSent >= 5000) {
    lastSent = millis();
    HTTPClient http;
    http.begin(SERVER);
    http.addHeader("Content-Type", "application/json");
    String payload = "{\"sensor_id\":\"B-01\",\"strain_value\":"
                     + String(strain, 2) + ",\"vibration\":0.2}";
    int code = http.POST(payload);
    Serial.println(code == 200 ? "✓ Sent!" : "✗ Failed");
    http.end();
  }
  delay(500);
}

float getDistance() {
  digitalWrite(TRIG_PIN, LOW); delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  return pulseIn(ECHO_PIN, HIGH) * 0.034 / 2;
}
```

### Step 3 — Data flow
```
Slide the HC-SR04 distance slider in Wokwi
        ↓
ESP32 calculates rock movement
        ↓  every 5 seconds
POST /update → Flask updates sensor_state
        ↓  every 3 seconds
Browser fetches /api/state
        ↓
Charts update with real sensor values
Activity feed logs the event
```

---

## 🔌 REST API Reference

### `POST /update`
Receives sensor data from ESP32/Wokwi.

**Request:**
```json
{
  "sensor_id": "B-01",
  "strain_value": 3.2,
  "vibration": 0.4
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Sensor B-01 updated",
  "sector": "sector_b",
  "strain_received": 3.2,
  "alert": true,
  "timestamp": "2026-02-21T15:30:45.123456"
}
```

---

### `GET /api/state`
Returns current sensor state for all sectors.

**Response:**
```json
{
  "sector_a": {"strain": 1.2, "pressure": 45.0, "vibration": 0.08, "status": "normal"},
  "sector_b": {"strain": 3.8, "pressure": 89.0, "vibration": 0.41, "status": "critical"},
  "sector_c": {"strain": 2.1, "pressure": 62.0, "vibration": 0.19, "status": "warning"},
  "collapse_probability": 34.7,
  "last_updated": "2026-02-21T15:30:45.123456"
}
```

---

### `POST /inspection/submit`
Submits a new manual inspection record.

**Request:**
```json
{
  "inspector": "Er. Ramesh Tiwari",
  "sector": "Sector B — Mid Tunnel",
  "findings": "Hairline cracks at chainage 0+480",
  "risk": "High"
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Inspection submitted and digitally signed",
  "id": "INS-2026-02211530"
}
```

---

### `GET /report`
Downloads auto-generated PDF compliance report.

---

## 📁 Project Structure

```
geosentrix-command-center/
│
├── geosentrix_app.py          # Main Flask application
│   ├── sensor_state{}         # In-memory sensor database
│   ├── hardware_devices[]     # Device registry
│   ├── inspections[]          # Inspection records
│   ├── SHARED_CSS             # Global styles (dark industrial theme)
│   ├── DASHBOARD_HTML         # Page 1 — Three.js + Charts
│   ├── INSPECTION_HTML        # Page 2 — Manual inspection module
│   ├── HARDWARE_HTML          # Page 3 — Device management
│   ├── /update                # REST endpoint for ESP32
│   ├── /api/state             # REST endpoint for browser
│   └── /report                # PDF generation (ReportLab)
│
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python + Flask | REST API server |
| CORS | flask-cors | Allow Wokwi browser requests |
| PDF | ReportLab | Compliance report generation |
| 3D Viz | Three.js r128 | Tunnel sector model |
| Charts | Chart.js 4.4 | Real-time sensor graphs |
| Fonts | Google Fonts | Rajdhani, Share Tech Mono, Exo 2 |
| Hardware | ESP32 (Wokwi) | Sensor simulation |
| Sensor | HC-SR04 | Ultrasonic distance/movement |
| Protocol | REST / HTTP | ESP32 ↔ Flask communication |

---

## 📋 Compliance Standards

| Standard | Description |
|---|---|
| IS:14268 | Indian Standard — Geotechnical Investigation |
| IRC:SP:91 | Guidelines for Road Tunnels |
| NHIDCL SOP-GT-2021 | NHIDCL Geotechnical Standard Operating Procedure |
| ISO 9001:2015 | Quality Management Systems |
| MoRT&H | Ministry of Road Transport & Highways guidelines |

---

## 🗺️ Roadmap

- [ ] WebSocket support for instant real-time updates
- [ ] MQTT broker integration for real hardware
- [ ] PostgreSQL / InfluxDB for persistent data storage
- [ ] Multi-tunnel support
- [ ] Mobile app for field engineers
- [ ] SMS/email alerts via Twilio/SendGrid
- [ ] Second ESP32 for Sector A monitoring
- [ ] OLED display on ESP32 for on-device readings

---

## 👥 Built For

| Organization | Role |
|---|---|
| NHIDCL | National Highways & Infrastructure Development Corporation |
| Ministry of Railways | Tunnel infrastructure monitoring |
| MoRT&H | Road transport and highway compliance |
| RITES / RVNL | Rail infrastructure consultancy |

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- [Wokwi](https://wokwi.com) — ESP32 simulation platform
- [Three.js](https://threejs.org) — 3D visualization
- [Chart.js](https://chartjs.org) — Real-time charting
- [ReportLab](https://reportlab.com) — PDF generation
- [Flask](https://flask.palletsprojects.com) — Python web framework

---

<div align="center">
  <strong>GeoSentrix Technologies Pvt. Ltd.</strong><br/>
  Built with ❤️ for Indian Infrastructure Safety<br/>
  NHIDCL · MoRT&H · IS:14268 · IRC:SP:91
</div>
