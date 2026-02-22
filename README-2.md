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
| Buzzer | GPIO 13 |
| Button | GPIO 4 |
| LCD I2C (16x2) | SDA/SCL |

### Step 1 — Get your local IP
```bash
ipconfig getifaddr en0      # Mac
ipconfig                    # Windows (look for IPv4)
```

### Step 2 — Hardware Setup (in Wokwi)

| Component | Pin | Purpose |
|---|---|---|
| HC-SR04 TRIG | GPIO 5 | Ultrasonic trigger |
| HC-SR04 ECHO | GPIO 18 | Ultrasonic echo |
| Buzzer | GPIO 13 | Audio alert on danger |
| Button | GPIO 4 | Field calibration reset |
| LCD I2C (16x2) | SDA/SCL | On-device display |

### Step 3 — Final Wokwi sketch (`sketch.ino`)
```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <LiquidCrystal_I2C.h>

// Setup LCD (Address 0x27)
LiquidCrystal_I2C lcd(0x27, 16, 2);

const int TRIG_PIN   = 5;
const int ECHO_PIN   = 18;
const int BUZZER_PIN = 13;
const int BUTTON_PIN = 4;       // Calibration button

const char* ssid     = "Wokwi-GUEST";
const char* password = "";
const char* SERVER   = "http://YOUR_IP:5050/update";  // ← replace with your IP

float baseDistance = 0;
float threshold    = 5.0;       // Alert if rock moves > 5cm
unsigned long lastSent = 0;

void setup() {
  Serial.begin(115200);
  lcd.init();
  lcd.backlight();
  pinMode(TRIG_PIN,   OUTPUT);
  pinMode(ECHO_PIN,   INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  lcd.setCursor(0, 0);
  lcd.print("GEOSENTRIX v1.0");

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(200); }

  calibrate();
}

void loop() {
  // Field engineer presses button to recalibrate baseline
  if (digitalRead(BUTTON_PIN) == LOW) {
    calibrate();
    delay(500);
  }

  float current   = getDistance();
  float movement  = abs(baseDistance - current);
  float strain_mm = movement * 10.0;

  // LCD display
  lcd.setCursor(0, 0);
  lcd.print("SHIFT: "); lcd.print(strain_mm, 1); lcd.print("mm   ");
  lcd.setCursor(0, 1);

  if (movement > threshold) {
    lcd.print("STATUS: DANGER! ");
    tone(BUZZER_PIN, 1000); delay(100); tone(BUZZER_PIN, 1500);
  } else {
    lcd.print("STATUS: STABLE  ");
    noTone(BUZZER_PIN);
  }

  // Send to GeoSentrix every 5 seconds
  if (millis() - lastSent >= 5000) {
    lastSent = millis();
    sendData(strain_mm, (movement > threshold));
  }
}

void calibrate() {
  lcd.clear();
  lcd.print("CALIBRATING...");
  delay(1000);
  baseDistance = getDistance();
  lcd.clear();
  lcd.print("BASELINE SET!");
  delay(1000);
}

void sendData(float strain, bool isDanger) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(SERVER);
    http.addHeader("Content-Type", "application/json");

    // GeoSentrix /update expects sensor_id and strain_value
    String payload = "{\"sensor_id\":\"B-01\",\"strain_value\":"
                     + String(strain) + ",\"vibration\":0.2}";

    int httpCode = http.POST(payload);
    Serial.print("Cloud Sync: "); Serial.println(httpCode);
    http.end();
  }
}

float getDistance() {
  digitalWrite(TRIG_PIN, LOW); delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  return pulseIn(ECHO_PIN, HIGH) * 0.034 / 2;
}
```

### Step 4 — Data flow
```
Field engineer presses button → calibrate() resets baseline
HC-SR04 reads distance        → calculates rock movement
strain_mm shown on LCD        → top row of display
movement > 5cm                → LCD says DANGER + buzzer beeps
Every 5 seconds               → POST to Flask /update
Flask                         → updates sector_b strain value
Browser fetches /api/state    → every 3 seconds
Charts spike with real data   → Rock Strain graph updates
Activity feed logs event      → "Sensor B-01: strain=Xmm"
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
| Hardware | ESP32 + HC-SR04 + LCD + Buzzer + Button (Wokwi) | Sensor simulation |
| Sensor | HC-SR04 Ultrasonic | Rock wall distance/movement detection |
| Display | LCD I2C 16x2 | On-device strain + status display |
| Alert | Piezo Buzzer | Audio danger alert |
| Input | Push Button (GPIO 4) | Field calibration reset |
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
