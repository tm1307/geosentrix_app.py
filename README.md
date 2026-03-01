# 🛰️ GeoSentrix Command Center

> **Mission-critical geotechnical tunnel monitoring system** for real-time structural surveillance — built for NHIDCL and Ministry of Railways infrastructure.

![Python](https://img.shields.io/badge/Python-3.8+-3b82f6?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-REST_API-f59e0b?style=for-the-badge&logo=flask)
![ESP32](https://img.shields.io/badge/ESP32-Wokwi-06b6d4?style=for-the-badge&logo=espressif)
![Three.js](https://img.shields.io/badge/Three.js-3D_Viz-white?style=for-the-badge)
![Compliance](https://img.shields.io/badge/IS:14268-Compliant-ef4444?style=for-the-badge)

---

## 📌 About

GeoSentrix Command Center is a real-time geotechnical monitoring dashboard that connects ESP32 sensors (physical or Wokwi-simulated) to a web-based mission control interface.

It detects rock strain, pore water pressure, and structural movement in tunnels — and alerts engineers before failures occur.

---

## ✨ Features

- **3D Tunnel Visualization** — Three.js sector model (A, B, C) with real-time glow alerts
- **Live Charts** — Chart.js graphs for Rock Strain (mm) and Pore Water Pressure (kPa)
- **MatrixCore AI Panel** — Collapse probability ring with structural, hydro, and seismic risk scores
- **Manual Inspection Module** — IS:14268 checklist, digital sign & submit, field team roster
- **Hardware Interface** — Device cards, live telemetry table, protocol config, OTA management
- **Activity Feed** — Real-time sensor event log with color-coded severity
- **Compliance PDF Report** — Auto-generated report (IS:14268 · IRC:SP:91 · NHIDCL SOP-GT-2021)

---

## 🖥️ Pages

| Route | Page | Description |
|---|---|---|
| `/` | Dashboard | 3D tunnel + live charts + AI panel + sensor inject |
| `/inspection` | Inspection Module | Field inspection form + records + IS:14268 checklist |
| `/hardware` | Hardware Interface | Device status + telemetry + terminal + OTA |
| `/report` | PDF Report | Downloads government compliance report |

---

## 📁 Project Structure

```
geosentrix/
│
├── geosentrix_app.py     # entire application — backend + frontend in one file
└── README.md
```

### Inside `geosentrix_app.py`

| Section | What it contains |
|---|---|
| **Imports & Setup** | Flask, CORS, ReportLab, datetime |
| **Shared State** | `sensor_state{}`, `hardware_devices[]`, `inspections[]`, `activity_log[]` |
| **`SHARED_CSS`** | Global dark industrial styles used across all pages |
| **`nav_bar()`** | Python function that generates the navigation HTML |
| **`DASHBOARD_HTML`** | Page 1 — Three.js tunnel + Chart.js graphs + MatrixCore AI |
| **`INSPECTION_HTML`** | Page 2 — Inspection form + IS:14268 checklist + team roster |
| **`HARDWARE_HTML`** | Page 3 — Device cards + live table + terminal + OTA panel |
| **`/update`** | POST route — receives sensor data from ESP32 |
| **`/api/state`** | GET route — returns current sensor values to browser |
| **`/api/hardware`** | GET route — returns hardware device list |
| **`/inspection/submit`** | POST route — saves new inspection record |
| **`/report`** | GET route — generates and streams PDF report |

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install flask flask-cors reportlab
```

### 2. Run the server
```bash
python3 geosentrix_app.py
```

### 3. Open in browser
```
http://localhost:5050
```

---

## 📡 ESP32 Integration (Wokwi)

### Hardware Setup

| Component | GPIO Pin | Purpose |
|---|---|---|
| HC-SR04 TRIG | 5 | Ultrasonic trigger |
| HC-SR04 ECHO | 18 | Ultrasonic echo |
| Buzzer | 13 | Audio danger alert |
| Button | 4 | Field calibration reset |
| LCD I2C 16x2 | SDA/SCL | On-device display |

### Get your local IP (Mac)
```bash
ipconfig getifaddr en0
```

### Wokwi Sketch — key lines
```cpp
const char* SERVER = "http://YOUR_IP:5050/update";

// Payload format GeoSentrix expects:
String payload = "{\"sensor_id\":\"B-01\",\"strain_value\":"
                 + String(strain_mm) + ",\"vibration\":0.2}";
```

### Data Flow
```
HC-SR04 reads wall distance
        ↓
ESP32 calculates rock movement → strain_mm
LCD shows SHIFT + STATUS
Buzzer triggers if movement > 5cm
        ↓  every 5 seconds
POST /update → Flask updates sensor_state
        ↓  every 3 seconds
Browser polls /api/state
        ↓
Charts update · Activity feed logs event
```

---

## 🔌 REST API Reference

| Method | Endpoint | Caller | Description |
|---|---|---|---|
| `POST` | `/update` | ESP32 | Send sensor reading |
| `GET` | `/api/state` | Browser | Get current sensor values |
| `GET` | `/api/hardware` | Browser | Get device list |
| `POST` | `/inspection/submit` | Browser | Submit inspection record |
| `GET` | `/report` | Browser | Download PDF report |

### POST `/update` — Example
```json
// Request
{ "sensor_id": "B-01", "strain_value": 3.2, "vibration": 0.4 }

// Response
{ "status": "ok", "message": "Sensor B-01 updated", "alert": true }
```

---

## 📋 Compliance Standards

| Standard | Description |
|---|---|
| IS:14268 | Indian Standard — Geotechnical Investigation |
| IRC:SP:91 | Guidelines for Road Tunnels |
| NHIDCL SOP-GT-2021 | NHIDCL Geotechnical SOP |
| ISO 9001:2015 | Quality Management Systems |
| MoRT&H | Ministry of Road Transport & Highways |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python + Flask |
| Cross-Origin | flask-cors |
| PDF Generation | ReportLab |
| 3D Visualization | Three.js r128 (CDN) |
| Charts | Chart.js 4.4 (CDN) |
| Fonts | Google Fonts — Rajdhani, Share Tech Mono, Exo 2 |
| Hardware | ESP32 on Wokwi |
| Sensor | HC-SR04 Ultrasonic |
| Communication | REST API over HTTP |

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

<div align="center">
  <strong>GeoSentrix Technologies Pvt. Ltd.</strong><br/>
  NHIDCL · MoRT&H · IS:14268 · IRC:SP:91
</div>
