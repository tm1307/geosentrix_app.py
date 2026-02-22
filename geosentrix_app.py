from flask import Flask, request, jsonify, render_template_string, send_file, redirect, url_for
from datetime import datetime
import json, io, threading, random, time

app = Flask(__name__)
from flask_cors import CORS
CORS(app)

# ── SHARED STATE ──────────────────────────────────────────────────────────────
sensor_state = {
    "sector_a": {"strain": 1.2, "pressure": 45.0, "vibration": 0.08, "temp": 22.1, "status": "normal"},
    "sector_b": {"strain": 3.8, "pressure": 89.0, "vibration": 0.41, "temp": 28.7, "status": "critical"},
    "sector_c": {"strain": 2.1, "pressure": 62.0, "vibration": 0.19, "temp": 24.3, "status": "warning"},
    "last_updated": datetime.now().isoformat(),
    "collapse_probability": 34.7,
}

hardware_devices = [
    {"id": "GS-HW-001", "name": "GeoScout Alpha", "type": "Strain Gauge Array", "sector": "A", "status": "online", "battery": 87, "signal": 94, "last_ping": "00:00:12"},
    {"id": "GS-HW-002", "name": "GeoScout Beta",  "type": "Piezometer Unit",    "sector": "B", "status": "online", "battery": 43, "signal": 71, "last_ping": "00:00:08"},
    {"id": "GS-HW-003", "name": "GeoScout Gamma", "type": "Vibration Sensor",   "sector": "B", "status": "alert",  "battery": 12, "signal": 55, "last_ping": "00:00:31"},
    {"id": "GS-HW-004", "name": "GeoScout Delta", "type": "Inclinometer",       "sector": "C", "status": "online", "battery": 76, "signal": 88, "last_ping": "00:00:05"},
    {"id": "GS-HW-005", "name": "GeoScout Epsilon","type": "Crack Meter",       "sector": "C", "status": "offline","battery":  0, "signal":  0, "last_ping": "02:14:07"},
    {"id": "GS-HW-006", "name": "Base Station",   "type": "Data Aggregator",   "sector": "—", "status": "online", "battery": 100,"signal": 99, "last_ping": "00:00:01"},
]

inspections = [
    {"id":"INS-2024-041","date":"2026-02-18","inspector":"Er. Ramesh Tiwari","sector":"B","findings":"Visible hairline cracks at chainage 0+480. Wet seepage observed.","risk":"High","action":"Grouting scheduled","signed":True},
    {"id":"INS-2024-040","date":"2026-02-10","inspector":"Er. Priya Menon","sector":"A","findings":"No structural anomalies. Surface coating intact.","risk":"Low","action":"Routine monitoring","signed":True},
    {"id":"INS-2024-039","date":"2026-02-03","inspector":"Er. Ramesh Tiwari","sector":"C","findings":"Minor efflorescence at crown. Drainage partially blocked.","risk":"Medium","action":"Drain cleaning ordered","signed":True},
]

activity_log = [
    {"time":"08:41:22","type":"info","msg":"GeoScout Mobile Unit: Scan Complete — Sector A"},
    {"time":"08:39:55","type":"warn","msg":"Alert: Sector B showing anomalous creep (Δ2.6mm)"},
    {"time":"08:35:10","type":"info","msg":"MatrixCore AI: Recalibration cycle complete"},
    {"time":"08:30:00","type":"info","msg":"System boot — All sensors online"},
]

# ── SHARED CSS + NAV (injected into every page) ───────────────────────────────
SHARED_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&family=Exo+2:wght@300;400;600;800&display=swap" rel="stylesheet"/>
<style>
:root {
  --bg-void:#0a0b0d; --bg-panel:#111318; --bg-card:#161a1f; --bg-elevated:#1c2128;
  --amber:#f59e0b; --amber-dim:#92600a; --red-alert:#ef4444; --green-ok:#22c55e;
  --cyan:#06b6d4; --blue:#3b82f6;
  --text-primary:#e8eaed; --text-secondary:#8b9099; --text-muted:#4a5058;
  --border:rgba(245,158,11,0.12); --border-bright:rgba(245,158,11,0.35);
}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg-void);color:var(--text-primary);font-family:'Exo 2',sans-serif;min-height:100vh;}
body::before{content:'';position:fixed;inset:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 39px,rgba(245,158,11,0.025) 39px,rgba(245,158,11,0.025) 40px),
             repeating-linear-gradient(90deg,transparent,transparent 39px,rgba(245,158,11,0.025) 39px,rgba(245,158,11,0.025) 40px);
  pointer-events:none;z-index:0;}

/* NAV */
header{position:sticky;top:0;z-index:100;background:rgba(10,11,13,0.97);backdrop-filter:blur(12px);
  border-bottom:1px solid var(--border-bright);height:64px;display:flex;align-items:center;
  justify-content:space-between;padding:0 24px;box-shadow:0 2px 32px rgba(245,158,11,0.08);}
.logo-block{display:flex;align-items:center;gap:14px;}
.logo-hex{width:40px;height:40px;background:linear-gradient(135deg,#f59e0b,#d97706);
  clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
  display:flex;align-items:center;justify-content:center;
  font-family:'Share Tech Mono';font-size:12px;font-weight:700;color:#0a0b0d;
  box-shadow:0 0 20px rgba(245,158,11,0.5);}
.logo-text{font-family:'Rajdhani';font-weight:700;font-size:20px;letter-spacing:3px;color:#fff;}
.logo-sub{font-family:'Share Tech Mono';font-size:8px;color:var(--amber);letter-spacing:4px;}
nav{display:flex;gap:4px;}
nav a{font-family:'Share Tech Mono';font-size:10px;letter-spacing:2px;text-transform:uppercase;
  color:var(--text-muted);text-decoration:none;padding:8px 14px;border-radius:2px;
  border:1px solid transparent;transition:all 0.2s;display:flex;align-items:center;gap:6px;}
nav a:hover{color:var(--amber);border-color:var(--border);}
nav a.active{color:var(--amber);border-color:var(--border-bright);background:rgba(245,158,11,0.06);}
.header-right{display:flex;align-items:center;gap:16px;}
.status-badge{display:flex;align-items:center;gap:6px;padding:5px 12px;
  border:1px solid rgba(34,197,94,0.4);border-radius:2px;
  font-family:'Share Tech Mono';font-size:10px;color:var(--green-ok);letter-spacing:2px;
  background:rgba(34,197,94,0.05);}
.status-dot{width:7px;height:7px;border-radius:50%;background:var(--green-ok);
  box-shadow:0 0 8px var(--green-ok);animation:pg 2s infinite;}
@keyframes pg{0%,100%{opacity:1}50%{opacity:0.5}}
.clock{font-family:'Share Tech Mono';font-size:12px;color:var(--amber);letter-spacing:2px;}

/* PANELS */
.panel{background:var(--bg-card);border:1px solid var(--border);border-radius:4px;overflow:hidden;position:relative;}
.panel::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,var(--amber),transparent);}
.panel-header{padding:10px 16px;border-bottom:1px solid var(--border);display:flex;
  align-items:center;justify-content:space-between;background:var(--bg-elevated);}
.panel-title{font-family:'Rajdhani';font-weight:700;font-size:12px;letter-spacing:3px;
  text-transform:uppercase;color:var(--amber);display:flex;align-items:center;gap:8px;}
.panel-title::before{content:'▶';font-size:7px;opacity:0.6;}
.panel-body{padding:16px;}

/* BADGES */
.badge{display:inline-block;padding:2px 8px;border-radius:2px;font-size:9px;font-weight:700;letter-spacing:2px;font-family:'Share Tech Mono';}
.badge-crit{background:rgba(239,68,68,0.15);color:var(--red-alert);border:1px solid rgba(239,68,68,0.3);}
.badge-warn{background:rgba(245,158,11,0.1);color:var(--amber);border:1px solid rgba(245,158,11,0.3);}
.badge-ok{background:rgba(34,197,94,0.1);color:var(--green-ok);border:1px solid rgba(34,197,94,0.25);}
.badge-off{background:rgba(139,144,153,0.1);color:var(--text-muted);border:1px solid rgba(139,144,153,0.2);}
.badge-blue{background:rgba(59,130,246,0.1);color:var(--blue);border:1px solid rgba(59,130,246,0.25);}

/* BUTTONS */
.btn{padding:8px 18px;border-radius:3px;font-family:'Rajdhani';font-weight:700;font-size:12px;
  letter-spacing:2px;cursor:pointer;transition:all 0.2s;border:1px solid;}
.btn-amber{background:rgba(245,158,11,0.1);border-color:var(--amber);color:var(--amber);}
.btn-amber:hover{background:rgba(245,158,11,0.2);box-shadow:0 0 16px rgba(245,158,11,0.2);}
.btn-red{background:rgba(239,68,68,0.1);border-color:var(--red-alert);color:var(--red-alert);}
.btn-red:hover{background:rgba(239,68,68,0.2);}
.btn-cyan{background:rgba(6,182,212,0.1);border-color:var(--cyan);color:var(--cyan);}
.btn-cyan:hover{background:rgba(6,182,212,0.2);}
.btn-green{background:rgba(34,197,94,0.1);border-color:var(--green-ok);color:var(--green-ok);}
.btn-green:hover{background:rgba(34,197,94,0.2);}

/* FORMS */
input,select,textarea{background:var(--bg-void);border:1px solid var(--border);color:var(--text-primary);
  font-family:'Share Tech Mono';font-size:10px;padding:8px 10px;border-radius:2px;width:100%;}
input:focus,select:focus,textarea:focus{outline:none;border-color:var(--amber);}
label{font-family:'Share Tech Mono';font-size:9px;letter-spacing:2px;color:var(--text-muted);
  display:block;margin-bottom:4px;text-transform:uppercase;}
.form-group{margin-bottom:12px;}
select option{background:var(--bg-card);}

/* MISC */
.page-wrap{position:relative;z-index:1;padding:20px;max-width:1400px;margin:0 auto;}
.page-title{font-family:'Rajdhani';font-size:26px;font-weight:800;letter-spacing:4px;
  color:#fff;margin-bottom:4px;}
.page-sub{font-family:'Share Tech Mono';font-size:9px;color:var(--text-muted);letter-spacing:3px;margin-bottom:20px;}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
.grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;}
.blink{animation:blink 1s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.4}}
.scan-line{position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,rgba(6,182,212,0.5),transparent);
  animation:scan 3s linear infinite;pointer-events:none;}
@keyframes scan{0%{top:0%}100%{top:100%}}
table{width:100%;border-collapse:collapse;}
th{font-family:'Share Tech Mono';font-size:9px;letter-spacing:2px;color:var(--text-muted);
  text-align:left;padding:8px 10px;border-bottom:1px solid var(--border);}
td{font-family:'Share Tech Mono';font-size:10px;padding:10px 10px;
  border-bottom:1px solid rgba(255,255,255,0.03);color:var(--text-secondary);}
tr:hover td{background:rgba(245,158,11,0.03);}
.tag{display:inline-block;font-family:'Share Tech Mono';font-size:8px;letter-spacing:1px;
  padding:2px 6px;border-radius:1px;margin:1px;}
</style>
"""

def nav_bar(active):
    pages = {'dash': '/', 'insp': '/inspection', 'hw': '/hardware'}
    icons = {'dash': '⬛ Dashboard', 'insp': '📋 Inspection', 'hw': '📡 Hardware'}
    links = ''.join(
        f'<a href="{pages[k]}" class="{"active" if k==active else ""}">{icons[k]}</a>'
        for k in pages
    )
    return f"""
<header>
  <div class="logo-block">
    <div class="logo-hex">GS</div>
    <div>
      <div class="logo-text">GEOSENTRIX</div>
      <div class="logo-sub">Command Center v3.2.1</div>
    </div>
  </div>
  <nav>{links}<a href="/report" target="_blank" class="">⬇ Report</a></nav>
  <div class="header-right">
    <div class="status-badge"><div class="status-dot"></div>SYSTEM: ACTIVE</div>
    <div class="clock" id="clock">--:--:--</div>
  </div>
</header>
<script>
function updateClock(){{
  const n=new Date();
  document.getElementById('clock').textContent=n.toLocaleTimeString('en-IN',{{hour12:false}})+' IST';
}}
setInterval(updateClock,1000);updateClock();
</script>
"""

# ── PAGE 1: DASHBOARD ─────────────────────────────────────────────────────────
DASHBOARD_HTML = """<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>GeoSentrix — Dashboard</title>
""" + SHARED_CSS + """
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
.main-layout{display:grid;grid-template-columns:1fr 300px;gap:16px;align-items:start;}
.metric-strip{display:flex;gap:12px;margin-bottom:16px;}
.metric-card{flex:1;padding:12px 14px;background:var(--bg-elevated);border:1px solid var(--border);border-radius:3px;}
.metric-card.alert{border-color:rgba(239,68,68,0.4);background:rgba(239,68,68,0.04);}
.metric-card.warn{border-color:rgba(245,158,11,0.3);}
.metric-label{font-family:'Share Tech Mono';font-size:8px;letter-spacing:3px;color:var(--text-muted);}
.metric-val{font-family:'Rajdhani';font-size:26px;font-weight:700;line-height:1.1;margin:2px 0;}
.metric-val.red{color:var(--red-alert);text-shadow:0 0 12px rgba(239,68,68,0.4);}
.metric-val.amber{color:var(--amber);}
.metric-val.green{color:var(--green-ok);}
.metric-val.cyan{color:var(--cyan);}
.metric-unit{font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);}
.charts-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px;}
.chart-wrap{height:170px;position:relative;}
#tunnel-canvas{width:100%;height:300px;display:block;}
.sector-overlay{position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;display:flex;}
.sec-lbl{flex:1;display:flex;align-items:flex-end;justify-content:center;padding-bottom:10px;}
.sec-lbl span{font-family:'Share Tech Mono';font-size:10px;letter-spacing:2px;padding:3px 8px;border-radius:2px;border:1px solid;}
.s-ok span{color:var(--green-ok);border-color:rgba(34,197,94,0.4);background:rgba(34,197,94,0.08);}
.s-crit span{color:var(--red-alert);border-color:rgba(239,68,68,0.5);background:rgba(239,68,68,0.1);animation:blink 1s infinite;}
.s-warn span{color:var(--amber);border-color:rgba(245,158,11,0.4);background:rgba(245,158,11,0.07);}
/* AI sidebar */
.collapse-ring{width:110px;height:110px;margin:0 auto 10px;position:relative;display:flex;align-items:center;justify-content:center;}
.collapse-ring svg{position:absolute;top:0;left:0;width:100%;height:100%;transform:rotate(-90deg);}
.ring-bg{fill:none;stroke:rgba(239,68,68,0.1);stroke-width:8;}
.ring-fill{fill:none;stroke:var(--red-alert);stroke-width:8;stroke-linecap:round;
  stroke-dasharray:330;stroke-dashoffset:215;filter:drop-shadow(0 0 5px rgba(239,68,68,0.6));}
.collapse-val{font-family:'Rajdhani';font-size:28px;font-weight:800;color:var(--red-alert);text-align:center;}
.risk-row{display:flex;align-items:center;gap:6px;margin-bottom:5px;}
.risk-name{font-family:'Share Tech Mono';font-size:8px;color:var(--text-secondary);width:60px;}
.risk-track{flex:1;height:3px;background:rgba(255,255,255,0.05);border-radius:2px;overflow:hidden;}
.risk-fill{height:100%;border-radius:2px;}
.activity-feed{max-height:220px;overflow-y:auto;}
.log-entry{padding:7px 10px;border-bottom:1px solid rgba(255,255,255,0.03);display:flex;gap:7px;align-items:flex-start;}
.log-time{font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);white-space:nowrap;padding-top:2px;}
.log-dot{width:5px;height:5px;border-radius:50%;margin-top:4px;flex-shrink:0;}
.log-dot.info{background:var(--cyan);}
.log-dot.warn{background:var(--red-alert);animation:blink 1s infinite;}
.log-msg{font-family:'Share Tech Mono';font-size:9px;color:var(--text-secondary);line-height:1.5;}
.api-inject input{margin-bottom:6px;}
.btn-full{width:100%;padding:9px;margin-top:4px;}
</style>
</head><body>
__NAV__
<div class="page-wrap">
  <div style="margin-bottom:14px;">
    <div class="page-title">COMMAND DASHBOARD</div>
    <div class="page-sub">NHIDCL · MINISTRY OF RAILWAYS · GEOTECHNICAL MONITORING SYSTEM</div>
  </div>

  <!-- METRIC STRIP -->
  <div class="metric-strip">
    <div class="metric-card alert">
      <div class="metric-label">Peak Rock Strain</div>
      <div class="metric-val red" id="m-strain">3.8</div>
      <div class="metric-unit">mm — SECTOR B</div>
    </div>
    <div class="metric-card warn">
      <div class="metric-label">Pore Water Pressure</div>
      <div class="metric-val amber">89.0</div>
      <div class="metric-unit">kPa — SECTOR B</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Active Sensors</div>
      <div class="metric-val green">24/24</div>
      <div class="metric-unit">ONLINE</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Collapse Probability</div>
      <div class="metric-val red">34.7%</div>
      <div class="metric-unit">MatrixCore AI</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Last Inspection</div>
      <div class="metric-val cyan" style="font-size:18px;">18 Feb</div>
      <div class="metric-unit">Er. R. Tiwari</div>
    </div>
  </div>

  <div class="main-layout">
    <div>
      <!-- TUNNEL -->
      <div class="panel" style="margin-bottom:12px;">
        <div class="panel-header">
          <span class="panel-title">3D Tunnel Model — Sector View</span>
          <span style="font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);">LIVE · REAL-TIME</span>
        </div>
        <div class="panel-body" style="padding:10px;position:relative;">
          <canvas id="tunnel-canvas"></canvas>
          <div class="sector-overlay">
            <div class="sec-lbl s-ok"><span>SECTOR A — OK</span></div>
            <div class="sec-lbl s-crit"><span>SECTOR B — CRITICAL</span></div>
            <div class="sec-lbl s-warn"><span>SECTOR C — WARN</span></div>
          </div>
        </div>
      </div>

      <!-- CHARTS -->
      <div class="charts-grid">
        <div class="panel">
          <div class="panel-header"><span class="panel-title">Rock Strain (mm)</span></div>
          <div class="panel-body"><div class="chart-wrap"><canvas id="strainChart"></canvas></div></div>
        </div>
        <div class="panel">
          <div class="panel-header"><span class="panel-title">Pore Water Pressure (kPa)</span></div>
          <div class="panel-body"><div class="chart-wrap"><canvas id="pressureChart"></canvas></div></div>
        </div>
      </div>

      <!-- SECTOR TABLE -->
      <div class="panel" style="margin-top:12px;">
        <div class="panel-header"><span class="panel-title">Sector Status Overview</span></div>
        <div class="panel-body" style="padding:0 16px 12px;">
          <table>
            <thead><tr><th>SECTOR</th><th>STRAIN (mm)</th><th>PRESSURE (kPa)</th><th>VIBRATION</th><th>TEMP °C</th><th>STATUS</th></tr></thead>
            <tbody>
              <tr><td>A — North Portal</td><td>1.2</td><td>45.0</td><td>0.08g</td><td>22.1</td><td><span class="badge badge-ok">NOMINAL</span></td></tr>
              <tr><td style="color:var(--red-alert)">B — Mid Tunnel</td><td style="color:var(--red-alert)">3.8</td><td style="color:var(--red-alert)">89.0</td><td style="color:var(--red-alert)">0.41g</td><td>28.7</td><td><span class="badge badge-crit">CRITICAL</span></td></tr>
              <tr><td style="color:var(--amber)">C — South Portal</td><td style="color:var(--amber)">2.1</td><td>62.0</td><td>0.19g</td><td>24.3</td><td><span class="badge badge-warn">WARNING</span></td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- SIDEBAR -->
    <div style="display:flex;flex-direction:column;gap:12px;">
      <!-- MatrixCore AI -->
      <div class="panel" style="border-color:rgba(6,182,212,0.2);">
        <div class="panel-header"><span class="panel-title" style="color:var(--cyan);">MatrixCore AI</span></div>
        <div class="panel-body" style="position:relative;">
          <div class="scan-line"></div>
          <div class="collapse-ring">
            <svg viewBox="0 0 110 110">
              <circle class="ring-bg" cx="55" cy="55" r="48"/>
              <circle class="ring-fill" cx="55" cy="55" r="48"/>
            </svg>
            <div>
              <div class="collapse-val">34.7%</div>
              <div style="font-family:'Share Tech Mono';font-size:7px;color:var(--text-muted);text-align:center;letter-spacing:2px;">COLLAPSE RISK</div>
            </div>
          </div>
          <div class="risk-row"><div class="risk-name">STRUCTURAL</div><div class="risk-track"><div class="risk-fill" style="width:72%;background:var(--red-alert);"></div></div><span style="font-family:'Share Tech Mono';font-size:8px;color:var(--red-alert);">72%</span></div>
          <div class="risk-row"><div class="risk-name">HYDRO</div><div class="risk-track"><div class="risk-fill" style="width:58%;background:var(--amber);"></div></div><span style="font-family:'Share Tech Mono';font-size:8px;color:var(--amber);">58%</span></div>
          <div class="risk-row"><div class="risk-name">SEISMIC</div><div class="risk-track"><div class="risk-fill" style="width:23%;background:var(--cyan);"></div></div><span style="font-family:'Share Tech Mono';font-size:8px;color:var(--cyan);">23%</span></div>
          <div style="margin-top:10px;padding:7px;background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.2);border-radius:3px;">
            <div style="font-family:'Share Tech Mono';font-size:7px;color:var(--red-alert);letter-spacing:2px;">⚠ RECOMMENDATION</div>
            <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--text-secondary);margin-top:4px;line-height:1.5;">Sector B: Grouting intervention advised within 24h. Halt heavy vehicles.</div>
          </div>
        </div>
      </div>

      <!-- API Inject -->
      <div class="panel">
        <div class="panel-header"><span class="panel-title">Sensor Data Inject</span></div>
        <div class="panel-body api-inject">
          <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);letter-spacing:2px;margin-bottom:8px;">POST → /update</div>
          <input id="inp-sensor" placeholder="sensor_id (e.g. B-01)"/>
          <input id="inp-strain" placeholder="strain_value (mm)" style="margin-top:6px;"/>
          <input id="inp-vibration" placeholder="vibration (g)" style="margin-top:6px;"/>
          <button class="btn btn-cyan btn-full" onclick="sendUpdate()">TRANSMIT DATA</button>
          <div id="api-resp" style="margin-top:6px;font-family:'Share Tech Mono';font-size:8px;min-height:12px;"></div>
        </div>
      </div>

      <!-- Activity Feed -->
      <div class="panel">
        <div class="panel-header"><span class="panel-title">Activity Feed</span></div>
        <div class="panel-body" style="padding:0;">
          <div class="activity-feed" id="activity-feed">
            <div class="log-entry"><div class="log-time">08:41</div><div class="log-dot info"></div><div class="log-msg">GeoScout Alpha: Scan Complete — Sector A</div></div>
            <div class="log-entry"><div class="log-time">08:39</div><div class="log-dot warn"></div><div class="log-msg">Alert: Sector B anomalous creep (Δ2.6mm)</div></div>
            <div class="log-entry"><div class="log-time">08:35</div><div class="log-dot info"></div><div class="log-msg">MatrixCore AI: Recalibration complete</div></div>
            <div class="log-entry"><div class="log-time">08:30</div><div class="log-dot info"></div><div class="log-msg">System boot — All sensors online</div></div>
          </div>
        </div>
      </div>

      <button class="btn btn-amber" style="width:100%;padding:11px;" onclick="window.open('/report','_blank')">⬇ GENERATE COMPLIANCE REPORT</button>
      <div style="font-family:'Share Tech Mono';font-size:7px;color:var(--text-muted);text-align:center;letter-spacing:2px;">NHIDCL · MoRT&H · IS:14268 · IRC:SP:91</div>
    </div>
  </div>
</div>

<script>
// THREE.JS
(function(){
  const canvas=document.getElementById('tunnel-canvas');
  const W=canvas.parentElement.offsetWidth,H=300;
  canvas.width=W;canvas.height=H;
  const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});
  renderer.setSize(W,H);renderer.setClearColor(0x000000,0);
  const scene=new THREE.Scene();
  const camera=new THREE.PerspectiveCamera(55,W/H,0.1,200);
  camera.position.set(0,0,12);
  scene.add(new THREE.AmbientLight(0x111111));
  const sectors=[
    {x:-6.5,color:0x22c55e,emissive:0x0a3015,alert:false},
    {x:0,   color:0xef4444,emissive:0x5a0a0a,alert:true},
    {x:6.5, color:0xf59e0b,emissive:0x3d2800,alert:false},
  ];
  sectors.forEach(s=>{
    const geo=new THREE.TorusGeometry(2.2,0.18,16,60);
    const mat=new THREE.MeshStandardMaterial({color:s.color,emissive:s.emissive,roughness:0.4,metalness:0.8});
    const torus=new THREE.Mesh(geo,mat);
    torus.position.x=s.x;scene.add(torus);
    const tubeGeo=new THREE.CylinderGeometry(2.2,2.2,3,32,1,true);
    const tubeMat=new THREE.MeshStandardMaterial({color:s.color,emissive:s.emissive,transparent:true,opacity:s.alert?0.12:0.05,side:THREE.BackSide});
    const tube=new THREE.Mesh(tubeGeo,tubeMat);tube.rotation.z=Math.PI/2;tube.position.x=s.x;scene.add(tube);
    const light=new THREE.PointLight(s.color,s.alert?2.5:0.8,8);light.position.set(s.x,0,0);scene.add(light);
    s.mesh=torus;s.light=light;
  });
  scene.add(new THREE.GridHelper(30,20,0x1a2030,0x0d1018)).position.y=-3;
  let t=0;
  function animate(){requestAnimationFrame(animate);t+=0.012;
    sectors.forEach((s,i)=>{s.mesh.rotation.y=t*0.3+i*0.5;if(s.alert)s.light.intensity=1.8+Math.sin(t*3)*0.8;});
    camera.position.y=Math.sin(t*0.2)*0.3;renderer.render(scene,camera);}
  animate();
})();

// CHARTS
function makeLabels(n){const l=[],now=new Date();for(let i=n-1;i>=0;i--){const d=new Date(now-i*5000);l.push(d.toLocaleTimeString('en-IN',{hour12:false}));}return l;}
function randWalk(base,spread,n){let v=base,a=[];for(let i=0;i<n;i++){v+=( Math.random()-0.5)*spread;v=Math.max(0,v);a.push(+v.toFixed(2));}return a;}
const chartOpts=(color)=>({responsive:true,maintainAspectRatio:false,animation:{duration:300},
  plugins:{legend:{display:false},tooltip:{backgroundColor:'rgba(10,11,13,0.9)',borderColor:color,borderWidth:1,
    titleFont:{family:'Share Tech Mono',size:9},bodyFont:{family:'Share Tech Mono',size:10}}},
  scales:{x:{ticks:{color:'#4a5058',font:{family:'Share Tech Mono',size:7},maxTicksLimit:5},grid:{color:'rgba(255,255,255,0.04)'}},
          y:{ticks:{color:'#4a5058',font:{family:'Share Tech Mono',size:8}},grid:{color:'rgba(255,255,255,0.04)'}}}});
const N=20;
const sChart=new Chart(document.getElementById('strainChart'),{type:'line',data:{labels:makeLabels(N),datasets:[{data:randWalk(2.5,0.4,N),borderColor:'#ef4444',backgroundColor:'rgba(239,68,68,0.07)',borderWidth:2,fill:true,tension:0.4,pointRadius:0}]},options:chartOpts('#ef4444')});
const pChart=new Chart(document.getElementById('pressureChart'),{type:'line',data:{labels:makeLabels(N),datasets:[{data:randWalk(70,5,N),borderColor:'#f59e0b',backgroundColor:'rgba(245,158,11,0.06)',borderWidth:2,fill:true,tension:0.4,pointRadius:0}]},options:chartOpts('#f59e0b')});

setInterval(()=>{
  fetch('/api/state')
    .then(r=>r.json())
    .then(data=>{
      const now=new Date().toLocaleTimeString('en-IN',{hour12:false});
      
      // Push real strain from Wokwi
      const strain = data.sector_b.strain;
      sChart.data.labels.push(now); sChart.data.labels.shift();
      sChart.data.datasets[0].data.push(strain);
      sChart.data.datasets[0].data.shift();
      sChart.update('none');

      // Push real pressure from Wokwi
      const pressure = data.sector_b.pressure;
      pChart.data.labels.push(now); pChart.data.labels.shift();
      pChart.data.datasets[0].data.push(pressure);
      pChart.data.datasets[0].data.shift();
      pChart.update('none');

      // Update metric card
      document.getElementById('m-strain').textContent = strain;
  });
},3000);

async function sendUpdate(){
  const sid=document.getElementById('inp-sensor').value||'B-01';
  const sv=parseFloat(document.getElementById('inp-strain').value)||3.9;
  const vib=parseFloat(document.getElementById('inp-vibration').value)||0.45;
  const resp=document.getElementById('api-resp');
  resp.style.color='var(--amber)';resp.textContent='◈ TRANSMITTING...';
  try{
    const r=await fetch('/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sensor_id:sid,strain_value:sv,vibration:vib})});
    const d=await r.json();
    resp.style.color='var(--green-ok)';resp.textContent='✓ ACK: '+d.message;
    const feed=document.getElementById('activity-feed');
    const now=new Date().toLocaleTimeString('en-IN',{hour12:false});
    const entry=document.createElement('div');entry.className='log-entry';
    entry.innerHTML=`<div class="log-time">${now}</div><div class="log-dot ${sv>3?'warn':'info'}"></div><div class="log-msg">Sensor ${sid}: strain=${sv}mm vib=${vib}g</div>`;
    feed.insertBefore(entry,feed.firstChild);
  }catch(e){resp.style.color='var(--red-alert)';resp.textContent='✗ CONNECTION ERROR';}
}
</script>
</body></html>"""

# ── PAGE 2: MANUAL INSPECTION ─────────────────────────────────────────────────
INSPECTION_HTML = """<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>GeoSentrix — Inspection</title>
""" + SHARED_CSS + """
<style>
.insp-layout{display:grid;grid-template-columns:1fr 380px;gap:16px;align-items:start;}
.insp-card{background:var(--bg-card);border:1px solid var(--border);border-radius:4px;padding:16px;margin-bottom:10px;position:relative;transition:border-color 0.2s;}
.insp-card:hover{border-color:var(--border-bright);}
.insp-card::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;border-radius:4px 0 0 4px;}
.insp-card.high::before{background:var(--red-alert);}
.insp-card.medium::before{background:var(--amber);}
.insp-card.low::before{background:var(--green-ok);}
.insp-id{font-family:'Share Tech Mono';font-size:9px;color:var(--text-muted);letter-spacing:2px;}
.insp-title{font-family:'Rajdhani';font-size:16px;font-weight:700;color:var(--text-primary);margin:4px 0;}
.insp-meta{font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);display:flex;gap:16px;margin-bottom:8px;}
.insp-findings{font-family:'Share Tech Mono';font-size:9px;color:var(--text-secondary);line-height:1.6;padding:8px;background:var(--bg-void);border-radius:2px;border-left:2px solid var(--border);}
.insp-actions{display:flex;gap:8px;margin-top:10px;align-items:center;}
.signed-badge{font-family:'Share Tech Mono';font-size:8px;color:var(--green-ok);border:1px solid rgba(34,197,94,0.3);padding:3px 8px;border-radius:2px;}
.photo-slot{width:100%;height:80px;border:1px dashed var(--border);border-radius:3px;display:flex;align-items:center;justify-content:center;font-family:'Share Tech Mono';font-size:9px;color:var(--text-muted);cursor:pointer;transition:all 0.2s;}
.photo-slot:hover{border-color:var(--amber);color:var(--amber);}
.checklist-item{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04);}
.checklist-item input[type=checkbox]{width:16px;height:16px;accent-color:var(--amber);cursor:pointer;}
.checklist-item label{font-family:'Share Tech Mono';font-size:9px;color:var(--text-secondary);cursor:pointer;flex:1;margin:0;}
.checklist-item .chk-sector{font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);}
.score-bar{height:6px;background:rgba(255,255,255,0.05);border-radius:3px;overflow:hidden;margin-top:4px;}
.score-fill{height:100%;border-radius:3px;transition:width 0.5s ease;}
</style>
</head><body>
__NAV__
<div class="page-wrap">
  <div style="margin-bottom:18px;">
    <div class="page-title">MANUAL INSPECTION MODULE</div>
    <div class="page-sub">FIELD ENGINEER INTERFACE · IS:14268 COMPLIANT · NHIDCL SOP-GT-2021</div>
  </div>

  <div class="insp-layout">
    <!-- LEFT: Records + New Form -->
    <div>
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
        <div style="font-family:'Rajdhani';font-size:14px;font-weight:700;letter-spacing:3px;color:var(--amber);">INSPECTION RECORDS</div>
        <button class="btn btn-amber" onclick="document.getElementById('new-form').scrollIntoView({behavior:'smooth'})">+ NEW INSPECTION</button>
      </div>

      <!-- Records -->
      <div class="insp-card high">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
          <div>
            <div class="insp-id">INS-2024-041 · SECTOR B</div>
            <div class="insp-title">Mid Tunnel — Structural Assessment</div>
            <div class="insp-meta">
              <span>📅 18 Feb 2026</span>
              <span>👤 Er. Ramesh Tiwari</span>
              <span>⏱ 14:30–16:45</span>
            </div>
          </div>
          <span class="badge badge-crit">HIGH RISK</span>
        </div>
        <div class="insp-findings">Visible hairline cracks at chainage 0+480. Wet seepage observed at crown. Rock bolt heads showing corrosion. Shotcrete delamination ~2.3m².</div>
        <div class="insp-actions">
          <span class="signed-badge">✓ DIGITALLY SIGNED</span>
          <span class="badge badge-warn">ACTION: GROUTING SCHEDULED</span>
          <button class="btn btn-red" style="margin-left:auto;padding:5px 12px;font-size:10px;" onclick="window.open('/report','_blank')">EXPORT PDF</button>
        </div>
        <div style="margin-top:10px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;">
          <div class="photo-slot" onclick="alert('Photo viewer — connect to GeoScout camera feed')">📷 Photo 1</div>
          <div class="photo-slot" onclick="alert('Photo viewer — connect to GeoScout camera feed')">📷 Photo 2</div>
          <div class="photo-slot">+ Add Photo</div>
        </div>
      </div>

      <div class="insp-card low">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
          <div>
            <div class="insp-id">INS-2024-040 · SECTOR A</div>
            <div class="insp-title">North Portal — Routine Check</div>
            <div class="insp-meta"><span>📅 10 Feb 2026</span><span>👤 Er. Priya Menon</span><span>⏱ 09:00–10:30</span></div>
          </div>
          <span class="badge badge-ok">LOW RISK</span>
        </div>
        <div class="insp-findings">No structural anomalies detected. Surface coating intact. Drainage channels clear. All rock bolt torque values within IS:14268 limits.</div>
        <div class="insp-actions"><span class="signed-badge">✓ DIGITALLY SIGNED</span><span class="badge badge-ok">ACTION: ROUTINE MONITORING</span></div>
      </div>

      <div class="insp-card medium">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
          <div>
            <div class="insp-id">INS-2024-039 · SECTOR C</div>
            <div class="insp-title">South Portal — Drainage Review</div>
            <div class="insp-meta"><span>📅 03 Feb 2026</span><span>👤 Er. Ramesh Tiwari</span><span>⏱ 11:00–12:20</span></div>
          </div>
          <span class="badge badge-warn">MEDIUM RISK</span>
        </div>
        <div class="insp-findings">Minor efflorescence at crown level. Drainage partially blocked with debris. No structural cracks. Instrumentation readings elevated but within warning threshold.</div>
        <div class="insp-actions"><span class="signed-badge">✓ DIGITALLY SIGNED</span><span class="badge badge-blue">ACTION: DRAIN CLEANING ORDERED</span></div>
      </div>

      <!-- NEW INSPECTION FORM -->
      <div class="panel" id="new-form" style="margin-top:4px;">
        <div class="panel-header"><span class="panel-title">New Inspection Entry</span></div>
        <div class="panel-body">
          <div class="grid-2" style="gap:12px;">
            <div class="form-group"><label>Inspector Name</label><input placeholder="Er. Full Name" id="f-inspector"/></div>
            <div class="form-group"><label>Designation</label><input placeholder="Junior Engineer / AE / EE"/></div>
            <div class="form-group"><label>Sector</label>
              <select id="f-sector"><option>Sector A — North Portal</option><option>Sector B — Mid Tunnel</option><option>Sector C — South Portal</option></select>
            </div>
            <div class="form-group"><label>Inspection Date</label><input type="date" id="f-date"/></div>
            <div class="form-group"><label>Start Time</label><input type="time"/></div>
            <div class="form-group"><label>End Time</label><input type="time"/></div>
          </div>
          <div class="form-group"><label>Chainage (from–to)</label><input placeholder="e.g. 0+420 to 0+560"/></div>
          <div class="form-group"><label>Findings & Observations</label>
            <textarea id="f-findings" rows="4" placeholder="Describe structural condition, cracks, seepage, instrumentation readings..."></textarea>
          </div>
          <div class="form-group"><label>Risk Assessment</label>
            <select id="f-risk"><option value="Low">Low — Routine monitoring</option><option value="Medium">Medium — Increased monitoring</option><option value="High">High — Immediate action</option><option value="Critical">Critical — Emergency response</option></select>
          </div>
          <div class="form-group"><label>Recommended Action</label><input placeholder="Grouting / Drainage / Rock bolt / Emergency closure..."/></div>

          <!-- CHECKLIST -->
          <div style="margin:12px 0 8px;font-family:'Share Tech Mono';font-size:9px;color:var(--amber);letter-spacing:3px;">IS:14268 INSPECTION CHECKLIST</div>
          <div class="checklist-item"><input type="checkbox" id="c1"/><label for="c1">Visual crack mapping completed</label><span class="chk-sector">STRUCTURAL</span></div>
          <div class="checklist-item"><input type="checkbox" id="c2"/><label for="c2">Rock bolt torque values recorded</label><span class="chk-sector">STRUCTURAL</span></div>
          <div class="checklist-item"><input type="checkbox" id="c3"/><label for="c3">Drainage system inspected</label><span class="chk-sector">HYDRO</span></div>
          <div class="checklist-item"><input type="checkbox" id="c4"/><label for="c4">Shotcrete condition assessed</label><span class="chk-sector">STRUCTURAL</span></div>
          <div class="checklist-item"><input type="checkbox" id="c5"/><label for="c5">Sensor calibration verified</label><span class="chk-sector">INSTRUMENTS</span></div>
          <div class="checklist-item"><input type="checkbox" id="c6"/><label for="c6">Photographs taken & catalogued</label><span class="chk-sector">DOCUMENTATION</span></div>
          <div class="checklist-item"><input type="checkbox" id="c7"/><label for="c7">Emergency exit routes clear</label><span class="chk-sector">SAFETY</span></div>

          <div style="margin-top:14px;display:flex;gap:10px;">
            <button class="btn btn-green" style="flex:1;" onclick="submitInspection()">✓ SUBMIT & DIGITALLY SIGN</button>
            <button class="btn btn-amber" onclick="window.open('/report','_blank')">⬇ EXPORT PDF</button>
          </div>
          <div id="form-resp" style="margin-top:8px;font-family:'Share Tech Mono';font-size:9px;min-height:14px;"></div>
        </div>
      </div>
    </div>

    <!-- RIGHT SIDEBAR -->
    <div style="display:flex;flex-direction:column;gap:12px;">
      <!-- Completion score -->
      <div class="panel">
        <div class="panel-header"><span class="panel-title">Inspection Health Score</span></div>
        <div class="panel-body">
          <div style="font-family:'Rajdhani';font-size:36px;font-weight:800;color:var(--amber);text-align:center;" id="health-score">0%</div>
          <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);text-align:center;letter-spacing:2px;margin-bottom:10px;">CHECKLIST COMPLETION</div>
          <div class="score-bar"><div class="score-fill" id="score-fill" style="width:0%;background:var(--amber);"></div></div>
          <div style="margin-top:12px;font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);">
            <div style="margin-bottom:4px;">Sector A ████████░░ 80%</div>
            <div style="margin-bottom:4px;">Sector B █████░░░░░ 50%</div>
            <div>Sector C ███████░░░ 70%</div>
          </div>
        </div>
      </div>

      <!-- Team on duty -->
      <div class="panel">
        <div class="panel-header"><span class="panel-title">Field Team — On Duty</span></div>
        <div class="panel-body" style="padding:0 16px 12px;">
          <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.04);">
            <div>
              <div style="font-family:'Rajdhani';font-size:13px;font-weight:600;">Er. Ramesh Tiwari</div>
              <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);">Junior Engineer · Sector B</div>
            </div>
            <span class="badge badge-crit">IN FIELD</span>
          </div>
          <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.04);">
            <div>
              <div style="font-family:'Rajdhani';font-size:13px;font-weight:600;">Er. Priya Menon</div>
              <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);">Asst. Engineer · Sector A</div>
            </div>
            <span class="badge badge-ok">STANDBY</span>
          </div>
          <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;">
            <div>
              <div style="font-family:'Rajdhani';font-size:13px;font-weight:600;">Er. Vikash Kumar</div>
              <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);">Tech. Supervisor · Control Room</div>
            </div>
            <span class="badge badge-blue">CONTROL</span>
          </div>
        </div>
      </div>

      <!-- Next scheduled -->
      <div class="panel">
        <div class="panel-header"><span class="panel-title">Scheduled Inspections</span></div>
        <div class="panel-body" style="padding:0 16px 12px;">
          <div style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04);">
            <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--red-alert);">DUE TODAY</div>
            <div style="font-family:'Rajdhani';font-size:13px;font-weight:600;margin:2px 0;">Sector B — Emergency Follow-up</div>
            <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);">14:00 IST · Er. Ramesh Tiwari</div>
          </div>
          <div style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04);">
            <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--amber);">22 FEB 2026</div>
            <div style="font-family:'Rajdhani';font-size:13px;font-weight:600;margin:2px 0;">Sector C — Drainage Recheck</div>
            <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);">10:00 IST · Er. Priya Menon</div>
          </div>
          <div style="padding:8px 0;">
            <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);">25 FEB 2026</div>
            <div style="font-family:'Rajdhani';font-size:13px;font-weight:600;margin:2px 0;">Full Tunnel — Monthly Audit</div>
            <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);">08:00 IST · All Engineers</div>
          </div>
        </div>
      </div>

      <div style="font-family:'Share Tech Mono';font-size:7px;color:var(--text-muted);text-align:center;letter-spacing:2px;line-height:1.8;">
        NHIDCL INSPECTION PROTOCOL v2.1<br/>
        IS:14268 · IRC:SP:91 · BIS CED 43<br/>
        DIGITALLY SIGNED VIA GeoSentrix PKI
      </div>
    </div>
  </div>
</div>

<script>
// Checklist score
const boxes=document.querySelectorAll('.checklist-item input[type=checkbox]');
function updateScore(){
  const checked=[...boxes].filter(b=>b.checked).length;
  const pct=Math.round(checked/boxes.length*100);
  document.getElementById('health-score').textContent=pct+'%';
  document.getElementById('score-fill').style.width=pct+'%';
  document.getElementById('score-fill').style.background=pct>=80?'var(--green-ok)':pct>=50?'var(--amber)':'var(--red-alert)';
  document.getElementById('health-score').style.color=pct>=80?'var(--green-ok)':pct>=50?'var(--amber)':'var(--red-alert)';
}
boxes.forEach(b=>b.addEventListener('change',updateScore));

async function submitInspection(){
  const resp=document.getElementById('form-resp');
  const inspector=document.getElementById('f-inspector').value;
  const sector=document.getElementById('f-sector').value;
  const findings=document.getElementById('f-findings').value;
  const risk=document.getElementById('f-risk').value;
  if(!inspector||!findings){resp.style.color='var(--red-alert)';resp.textContent='✗ Fill inspector name and findings';return;}
  try{
    const r=await fetch('/inspection/submit',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({inspector,sector,findings,risk,date:new Date().toISOString()})});
    const d=await r.json();
    resp.style.color='var(--green-ok)';resp.textContent='✓ '+d.message+' — ID: '+d.id;
  }catch(e){resp.style.color='var(--red-alert)';resp.textContent='✗ Submission failed';}
}

// Set today's date
document.getElementById('f-date').value=new Date().toISOString().split('T')[0];
</script>
</body></html>"""

# ── PAGE 3: HARDWARE CONNECTION ───────────────────────────────────────────────
HARDWARE_HTML = """<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>GeoSentrix — Hardware</title>
""" + SHARED_CSS + """
<style>
.hw-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:16px;}
.hw-card{background:var(--bg-card);border:1px solid var(--border);border-radius:4px;padding:14px;position:relative;overflow:hidden;transition:border-color 0.2s;}
.hw-card:hover{border-color:var(--border-bright);}
.hw-card.online::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--green-ok),transparent);}
.hw-card.alert::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--red-alert),transparent);animation:blink 1s infinite;}
.hw-card.offline{opacity:0.5;}
.hw-card.offline::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--text-muted);}
.hw-name{font-family:'Rajdhani';font-size:15px;font-weight:700;color:var(--text-primary);margin-bottom:2px;}
.hw-id{font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);letter-spacing:2px;}
.hw-type{font-family:'Share Tech Mono';font-size:8px;color:var(--cyan);margin:6px 0;}
.hw-stats{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:8px;}
.hw-stat{background:var(--bg-void);padding:5px 8px;border-radius:2px;border:1px solid rgba(255,255,255,0.04);}
.hw-stat-label{font-family:'Share Tech Mono';font-size:7px;color:var(--text-muted);letter-spacing:2px;}
.hw-stat-val{font-family:'Rajdhani';font-size:16px;font-weight:700;}
.batt-bar{height:4px;background:rgba(255,255,255,0.06);border-radius:2px;overflow:hidden;margin-top:3px;}
.batt-fill{height:100%;border-radius:2px;}
.signal-dot{display:inline-block;width:5px;height:5px;border-radius:50%;margin-right:4px;}
.conn-panel{background:var(--bg-card);border:1px solid var(--border);border-radius:4px;padding:16px;position:relative;}
.conn-panel::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--cyan),transparent);}
.terminal{background:var(--bg-void);border:1px solid rgba(6,182,212,0.2);border-radius:3px;padding:12px;height:180px;overflow-y:auto;font-family:'Share Tech Mono';font-size:9px;line-height:1.8;color:var(--text-secondary);}
.terminal::-webkit-scrollbar{width:3px;}
.terminal::-webkit-scrollbar-thumb{background:var(--amber-dim);}
.t-green{color:var(--green-ok);}
.t-amber{color:var(--amber);}
.t-red{color:var(--red-alert);}
.t-cyan{color:var(--cyan);}
.t-muted{color:var(--text-muted);}
.proto-btn{padding:6px 12px;border-radius:2px;font-family:'Share Tech Mono';font-size:9px;cursor:pointer;border:1px solid;transition:all 0.2s;letter-spacing:1px;}
.proto-btn.active{background:rgba(6,182,212,0.15);border-color:var(--cyan);color:var(--cyan);}
.proto-btn:not(.active){background:transparent;border-color:var(--text-muted);color:var(--text-muted);}
.proto-btn:not(.active):hover{border-color:var(--amber);color:var(--amber);}
.live-table-wrap{overflow-x:auto;}
</style>
</head><body>
__NAV__
<div class="page-wrap">
  <div style="margin-bottom:18px;display:flex;align-items:flex-end;justify-content:space-between;">
    <div>
      <div class="page-title">HARDWARE INTERFACE</div>
      <div class="page-sub">GEOSCOUT DEVICE NETWORK · MQTT / RS-485 / LoRa BRIDGE</div>
    </div>
    <div style="display:flex;gap:8px;">
      <button class="btn btn-cyan" onclick="pingAll()">◈ PING ALL DEVICES</button>
      <button class="btn btn-amber" onclick="syncAll()">↻ SYNC CONFIG</button>
    </div>
  </div>

  <!-- DEVICE CARDS -->
  <div class="hw-grid" id="device-grid">
    <!-- Populated by JS -->
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;">
    <!-- CONNECTION CONFIG -->
    <div class="conn-panel">
      <div style="font-family:'Rajdhani';font-size:13px;font-weight:700;letter-spacing:3px;color:var(--cyan);margin-bottom:12px;">COMMUNICATION CONFIG</div>
      <div style="display:flex;gap:6px;margin-bottom:12px;" id="proto-btns">
        <button class="proto-btn active" onclick="setProto(this,'MQTT')">MQTT</button>
        <button class="proto-btn" onclick="setProto(this,'RS-485')">RS-485</button>
        <button class="proto-btn" onclick="setProto(this,'LoRa')">LoRa</button>
        <button class="proto-btn" onclick="setProto(this,'HTTP')">HTTP REST</button>
      </div>
      <div class="form-group"><label>Broker / Host IP</label><input id="broker" value="192.168.10.1" placeholder="192.168.x.x or mqtt.geosentrix.in"/></div>
      <div class="grid-2" style="gap:8px;">
        <div class="form-group"><label>Port</label><input id="port" value="1883" placeholder="1883"/></div>
        <div class="form-group"><label>Topic / Channel</label><input value="geosentrix/tunnel/+" placeholder="MQTT topic"/></div>
      </div>
      <div class="grid-2" style="gap:8px;">
        <div class="form-group"><label>Username</label><input value="gs_admin" placeholder="Username"/></div>
        <div class="form-group"><label>Password</label><input type="password" value="••••••••" placeholder="Password"/></div>
      </div>
      <div style="display:flex;gap:8px;margin-top:4px;">
        <button class="btn btn-green" style="flex:1;" onclick="testConnection()">TEST CONNECTION</button>
        <button class="btn btn-cyan" onclick="saveConfig()">SAVE CONFIG</button>
      </div>
      <div id="conn-resp" style="margin-top:6px;font-family:'Share Tech Mono';font-size:8px;min-height:12px;"></div>
    </div>

    <!-- TERMINAL -->
    <div class="conn-panel">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
        <div style="font-family:'Rajdhani';font-size:13px;font-weight:700;letter-spacing:3px;color:var(--cyan);">SYSTEM TERMINAL</div>
        <button class="btn btn-cyan" style="padding:4px 10px;font-size:9px;" onclick="clearTerminal()">CLEAR</button>
      </div>
      <div class="terminal" id="terminal">
        <span class="t-muted">[GeoSentrix Shell v3.2.1]</span><br/>
        <span class="t-cyan">$ </span>system.init()<br/>
        <span class="t-green">✓ Core systems nominal</span><br/>
        <span class="t-cyan">$ </span>hardware.scan()<br/>
        <span class="t-green">✓ Found 6 devices on network</span><br/>
        <span class="t-amber">⚠ GS-HW-003 battery critical (12%)</span><br/>
        <span class="t-red">✗ GS-HW-005 offline — last seen 2h ago</span><br/>
        <span class="t-cyan">$ </span>mqtt.connect(192.168.10.1:1883)<br/>
        <span class="t-green">✓ MQTT broker connected</span><br/>
        <span class="t-muted">Subscribed: geosentrix/tunnel/+</span><br/>
        <span class="t-cyan">$ </span><span id="cursor" style="animation:blink 1s infinite;">█</span>
      </div>
      <div style="display:flex;gap:6px;margin-top:8px;">
        <input id="cmd-input" placeholder="Enter command..." style="flex:1;" onkeydown="if(event.key==='Enter')runCmd()"/>
        <button class="btn btn-cyan" style="padding:6px 12px;" onclick="runCmd()">RUN</button>
      </div>
    </div>
  </div>

  <!-- LIVE DATA TABLE -->
  <div class="panel">
    <div class="panel-header">
      <span class="panel-title">Live Sensor Telemetry</span>
      <span style="font-family:'Share Tech Mono';font-size:8px;color:var(--green-ok);">● STREAMING · 1Hz</span>
    </div>
    <div class="panel-body" style="padding:0 16px 12px;">
      <div class="live-table-wrap">
        <table>
          <thead><tr><th>DEVICE ID</th><th>SENSOR TYPE</th><th>SECTOR</th><th>VALUE</th><th>UNIT</th><th>TIMESTAMP</th><th>QUALITY</th><th>ACTION</th></tr></thead>
          <tbody id="live-table"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- FIRMWARE -->
  <div class="panel" style="margin-top:16px;">
    <div class="panel-header"><span class="panel-title">Firmware & OTA Management</span></div>
    <div class="panel-body">
      <div class="grid-3" style="gap:12px;">
        <div style="background:var(--bg-elevated);padding:12px;border-radius:3px;border:1px solid var(--border);">
          <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);letter-spacing:2px;">CURRENT FIRMWARE</div>
          <div style="font-family:'Rajdhani';font-size:18px;font-weight:700;color:var(--cyan);margin:4px 0;">v2.8.4</div>
          <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--green-ok);">All devices up to date</div>
        </div>
        <div style="background:var(--bg-elevated);padding:12px;border-radius:3px;border:1px solid rgba(245,158,11,0.25);">
          <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);letter-spacing:2px;">AVAILABLE UPDATE</div>
          <div style="font-family:'Rajdhani';font-size:18px;font-weight:700;color:var(--amber);margin:4px 0;">v2.9.0</div>
          <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--amber);">LoRa range +30% · Bug fixes</div>
        </div>
        <div style="background:var(--bg-elevated);padding:12px;border-radius:3px;border:1px solid var(--border);display:flex;flex-direction:column;justify-content:space-between;">
          <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);margin-bottom:8px;letter-spacing:2px;">OTA DEPLOYMENT</div>
          <button class="btn btn-amber" style="width:100%;" onclick="otaUpdate()">PUSH OTA UPDATE</button>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
const devices = __DEVICES_JSON__;

function getBattColor(b){return b>50?'var(--green-ok)':b>20?'var(--amber)':'var(--red-alert)';}
function getSignalBars(s){
  const bars=Math.ceil(s/25);
  return '█'.repeat(bars)+'░'.repeat(4-bars);
}

function renderDevices(){
  const grid=document.getElementById('device-grid');
  grid.innerHTML=devices.map(d=>`
    <div class="hw-card ${d.status}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
          <div class="hw-id">${d.id}</div>
          <div class="hw-name">${d.name}</div>
        </div>
        <span class="badge ${d.status==='online'?'badge-ok':d.status==='alert'?'badge-crit':'badge-off'}">${d.status.toUpperCase()}</span>
      </div>
      <div class="hw-type">${d.type}</div>
      <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--text-muted);margin-bottom:6px;">SECTOR ${d.sector} · Last ping: ${d.last_ping} ago</div>
      <div class="hw-stats">
        <div class="hw-stat">
          <div class="hw-stat-label">BATTERY</div>
          <div class="hw-stat-val" style="color:${getBattColor(d.battery)};font-size:14px;">${d.battery}%</div>
          <div class="batt-bar"><div class="batt-fill" style="width:${d.battery}%;background:${getBattColor(d.battery)};"></div></div>
        </div>
        <div class="hw-stat">
          <div class="hw-stat-label">SIGNAL</div>
          <div class="hw-stat-val" style="color:${d.signal>70?'var(--green-ok)':d.signal>40?'var(--amber)':'var(--red-alert)'};font-size:14px;">${d.signal}%</div>
          <div style="font-family:'Share Tech Mono';font-size:9px;color:${d.signal>70?'var(--green-ok)':d.signal>40?'var(--amber)':'var(--red-alert)'};">${getSignalBars(d.signal)}</div>
        </div>
      </div>
      <div style="display:flex;gap:6px;margin-top:8px;">
        <button class="btn btn-cyan" style="flex:1;padding:5px;font-size:9px;" onclick="pingDevice('${d.id}')">PING</button>
        <button class="btn btn-amber" style="padding:5px 10px;font-size:9px;" onclick="calibrate('${d.id}')">CAL</button>
      </div>
    </div>
  `).join('');
}
renderDevices();

// Live table
const liveData = [
  {id:'GS-HW-001',type:'Strain Gauge',sector:'A',value:'1.24',unit:'mm',ts:'',quality:98},
  {id:'GS-HW-002',type:'Piezometer',sector:'B',value:'89.3',unit:'kPa',ts:'',quality:87},
  {id:'GS-HW-003',type:'Vibration',sector:'B',value:'0.41',unit:'g',ts:'',quality:71},
  {id:'GS-HW-004',type:'Inclinometer',sector:'C',value:'0.23',unit:'°',ts:'',quality:94},
];
function renderLiveTable(){
  const now=new Date().toLocaleTimeString('en-IN',{hour12:false});
  document.getElementById('live-table').innerHTML=liveData.map(d=>{
    d.ts=now;
    const q=d.quality;
    const qColor=q>90?'var(--green-ok)':q>70?'var(--amber)':'var(--red-alert)';
    return `<tr>
      <td style="color:var(--cyan);">${d.id}</td><td>${d.type}</td><td>Sector ${d.sector}</td>
      <td style="color:var(--text-primary);font-weight:700;">${d.value}</td><td>${d.unit}</td>
      <td>${d.ts}</td>
      <td><span style="color:${qColor};">${q}%</span></td>
      <td><button class="btn btn-cyan" style="padding:3px 8px;font-size:8px;" onclick="drillDown('${d.id}')">DETAIL</button></td>
    </tr>`;
  }).join('');
  // randomise slightly
  liveData.forEach(d=>{d.value=(parseFloat(d.value)+(Math.random()-0.5)*0.1).toFixed(2);});
}
renderLiveTable();
setInterval(renderLiveTable,2000);

// Terminal
const cmds={
  'help':'Available: scan, ping-all, status, clear, mqtt.status, calibrate-all',
  'scan':'Scanning network... Found 6 devices. 4 online, 1 alert, 1 offline.',
  'status':'System: OPERATIONAL | MQTT: CONNECTED | Uptime: 14h 22m',
  'mqtt.status':'Broker: 192.168.10.1:1883 | Messages/s: 24 | Lag: 12ms',
  'calibrate-all':'Sending calibration command to all online devices...\n✓ GS-HW-001 calibrated\n✓ GS-HW-002 calibrated\n⚠ GS-HW-003 low battery, calibration deferred',
};
function addTerminalLine(text,cls=''){
  const t=document.getElementById('terminal');
  text.split('\n').forEach(line=>{
    t.innerHTML+=`<br/><span class="${cls}">${line}</span>`;
  });
  t.scrollTop=t.scrollHeight;
}
function runCmd(){
  const inp=document.getElementById('cmd-input');
  const cmd=inp.value.trim().toLowerCase();
  if(!cmd)return;
  addTerminalLine(`$ ${cmd}`,'t-cyan');
  if(cmd==='clear'){clearTerminal();inp.value='';return;}
  const resp=cmds[cmd]||`Command not found: ${cmd}. Type 'help' for commands.`;
  addTerminalLine(resp, resp.includes('✗')||resp.includes('not found')?'t-red':resp.includes('⚠')?'t-amber':'t-green');
  inp.value='';
}
function clearTerminal(){
  document.getElementById('terminal').innerHTML='<span class="t-muted">[Terminal cleared]</span><br/><span class="t-cyan">$ </span><span id="cursor" style="animation:blink 1s infinite;">█</span>';
}
function pingAll(){addTerminalLine('$ ping-all','t-cyan');addTerminalLine('Pinging all devices...\n✓ GS-HW-001: 12ms\n✓ GS-HW-002: 18ms\n⚠ GS-HW-003: 89ms (degraded)\n✓ GS-HW-004: 9ms\n✗ GS-HW-005: TIMEOUT\n✓ Base Station: 3ms','t-green');}
function syncAll(){addTerminalLine('$ sync-config','t-cyan');addTerminalLine('Config sync sent to 5 online devices.','t-green');}
function testConnection(){
  const r=document.getElementById('conn-resp');
  r.style.color='var(--amber)';r.textContent='◈ Testing connection...';
  setTimeout(()=>{r.style.color='var(--green-ok)';r.textContent='✓ MQTT broker reachable · RTT 14ms · Auth OK';},1200);
}
function saveConfig(){const r=document.getElementById('conn-resp');r.style.color='var(--green-ok)';r.textContent='✓ Configuration saved to device';}
function pingDevice(id){addTerminalLine(`$ ping ${id}`,'t-cyan');addTerminalLine(`✓ ${id}: 21ms response`,'t-green');}
function calibrate(id){addTerminalLine(`$ calibrate ${id}`,'t-cyan');addTerminalLine(`✓ ${id} calibration sequence initiated`,'t-green');}
function drillDown(id){alert(`Detail view for ${id} — Connect to live MQTT stream for full telemetry graph`);}
function otaUpdate(){addTerminalLine('$ ota.push(v2.9.0)','t-cyan');addTerminalLine('OTA package queued for 4 online devices. Estimated: 3min per device.','t-amber');}
function setProto(btn,proto){
  document.querySelectorAll('.proto-btn').forEach(b=>{b.classList.remove('active');b.classList.add('not-active');});
  btn.classList.add('active');
  const portMap={'MQTT':'1883','RS-485':'9600','LoRa':'868','HTTP REST':'5050'};
  document.getElementById('port').value=portMap[proto]||'1883';
}
</script>
</body></html>"""

# ── ROUTES ────────────────────────────────────────────────────────────────────
@app.route('/')
def dashboard():
    import json as _json
    return DASHBOARD_HTML.replace('__NAV__', nav_bar('dash'))

@app.route('/inspection')
def inspection():
    return INSPECTION_HTML.replace('__NAV__', nav_bar('insp'))

@app.route('/hardware')
def hardware():
    import json as _json
    hw_json = _json.dumps(hardware_devices)
    html = HARDWARE_HTML.replace('__NAV__', nav_bar('hw'))
    html = html.replace('__DEVICES_JSON__', hw_json)
    return html

@app.route('/update', methods=['POST'])
def update_sensor():
    data = request.get_json(force=True)
    sensor_id = data.get('sensor_id', 'unknown')
    strain = float(data.get('strain_value', 0))
    vibration = float(data.get('vibration', 0))
    sector = 'sector_b' if 'B' in sensor_id.upper() else \
             'sector_a' if 'A' in sensor_id.upper() else 'sector_c'
    sensor_state[sector]['strain'] = strain
    sensor_state['last_updated'] = datetime.now().isoformat()
    activity_log.insert(0, {"time": datetime.now().strftime('%H:%M:%S'),
        "type": "warn" if strain > 3.0 else "info",
        "msg": f"Sensor {sensor_id}: strain={strain}mm vib={vibration}g"})
    return jsonify({"status":"ok","message":f"Sensor {sensor_id} updated","sector":sector,
                    "strain_received":strain,"alert":strain>3.0,"timestamp":datetime.now().isoformat()})

@app.route('/inspection/submit', methods=['POST'])
def submit_inspection():
    data = request.get_json(force=True)
    insp_id = f"INS-{datetime.now().strftime('%Y-%m%d%H%M')}"
    inspections.insert(0, {**data, "id": insp_id, "signed": True})
    return jsonify({"status":"ok","message":"Inspection submitted and digitally signed","id":insp_id})

@app.route('/api/state')
def get_state():
    return jsonify(sensor_state)

@app.route('/api/hardware')
def get_hardware():
    return jsonify(hardware_devices)

@app.route('/report')
def generate_report():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.units import cm

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    AMBER = colors.HexColor('#f59e0b'); RED = colors.HexColor('#ef4444')
    GREEN = colors.HexColor('#22c55e'); LIGHT = colors.HexColor('#e8eaed')
    MUTED = colors.HexColor('#8b9099'); DARK = colors.HexColor('#1c2128')
    CYAN = colors.HexColor('#06b6d4')

    def ps(name, **kw): return ParagraphStyle(name, parent=styles['Normal'], **kw)
    title_s = ps('t', fontName='Helvetica-Bold', fontSize=20, textColor=AMBER, spaceAfter=4)
    sub_s   = ps('s', fontName='Helvetica', fontSize=9, textColor=MUTED, spaceAfter=8)
    head_s  = ps('h', fontName='Helvetica-Bold', fontSize=11, textColor=AMBER, spaceBefore=14, spaceAfter=4)
    body_s  = ps('b', fontName='Helvetica', fontSize=9, textColor=LIGHT, leading=14, spaceAfter=5)

    story = []
    story.append(Paragraph("GEOSENTRIX COMMAND CENTER", title_s))
    story.append(Paragraph("Government Compliance Report — Geotechnical Tunnel Monitoring", sub_s))
    story.append(Paragraph(f"Report Date: {datetime.now().strftime('%d %B %Y, %H:%M:%S IST')} | Reference: NHIDCL/GS/{datetime.now().strftime('%Y/%m%d')}", sub_s))
    story.append(Paragraph("Classification: RESTRICTED — For Authorised Personnel Only", ps('cls', fontName='Helvetica-Bold', fontSize=8, textColor=RED, spaceAfter=8)))
    story.append(HRFlowable(width='100%', thickness=1, color=AMBER, spaceAfter=8))

    story.append(Paragraph("1. EXECUTIVE SUMMARY", head_s))
    story.append(Paragraph("This report presents real-time geotechnical monitoring data collected by the GeoSentrix Command Center for tunnel infrastructure under NHIDCL/Ministry of Railways jurisdiction. Elevated stress conditions detected in Sector B require immediate engineering intervention.", body_s))

    story.append(Paragraph("2. SENSOR DATA SUMMARY", head_s))
    t = Table([['Sector','Location','Strain (mm)','Pressure (kPa)','Vibration','Temp °C','Status'],
               ['A','North Portal','1.2','45.0','0.08g','22.1','NOMINAL'],
               ['B','Mid Tunnel','3.8','89.0','0.41g','28.7','CRITICAL'],
               ['C','South Portal','2.1','62.0','0.19g','24.3','WARNING']],
              colWidths=[1.2*cm,3.5*cm,2.3*cm,2.8*cm,2.3*cm,2*cm,2.4*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),DARK),('TEXTCOLOR',(0,0),(-1,0),AMBER),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),
        ('BACKGROUND',(0,1),(-1,-1),colors.HexColor('#111318')),('TEXTCOLOR',(0,1),(-1,-1),LIGHT),
        ('TEXTCOLOR',(0,2),(-1,2),RED),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#2a3040')),
        ('ALIGN',(2,0),(-1,-1),'CENTER'),('PADDING',(0,0),(-1,-1),5),
    ]))
    story.append(t)

    story.append(Paragraph("3. MANUAL INSPECTION RECORDS", head_s))
    for ins in inspections[:3]:
        story.append(Paragraph(f"ID: {ins.get('id','—')} | Date: {ins.get('date','—')} | Inspector: {ins.get('inspector','—')} | Risk: {ins.get('risk','—')}", ps('ih', fontName='Helvetica-Bold', fontSize=8, textColor=CYAN, spaceAfter=2)))
        story.append(Paragraph(f"Findings: {ins.get('findings','—')}", body_s))

    story.append(Paragraph("4. HARDWARE STATUS", head_s))
    hw_data = [['Device ID','Name','Type','Sector','Status','Battery','Signal']] + \
              [[d['id'],d['name'],d['type'],d['sector'],d['status'].upper(),f"{d['battery']}%",f"{d['signal']}%"] for d in hardware_devices]
    ht = Table(hw_data, colWidths=[2.5*cm,2.5*cm,3*cm,1.5*cm,1.8*cm,1.5*cm,1.5*cm])
    ht.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),DARK),('TEXTCOLOR',(0,0),(-1,0),CYAN),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),7),
        ('BACKGROUND',(0,1),(-1,-1),colors.HexColor('#111318')),('TEXTCOLOR',(0,1),(-1,-1),LIGHT),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#2a3040')),('PADDING',(0,0),(-1,-1),4),
    ]))
    story.append(ht)

    story.append(Paragraph("5. MATRIXCORE AI ASSESSMENT", head_s))
    story.append(Paragraph("Collapse Probability: 34.7% — ELEVATED | Structural: 72% | Hydro: 58% | Seismic: 23%", body_s))
    story.append(Paragraph("Recommendation: Sector B grouting within 24h. Halt heavy vehicles. Increase scan frequency.", body_s))

    story.append(Paragraph("6. COMPLIANCE", head_s))
    story.append(Paragraph("IS:14268 · IRC:SP:91 · NHIDCL SOP-GT-2021 · ISO 9001:2015 · MoRT&H", body_s))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=MUTED))
    story.append(Paragraph(f"GeoSentrix Technologies Pvt. Ltd. | {datetime.now().strftime('%Y')} | CONFIDENTIAL", ps('ft', fontName='Helvetica', fontSize=7, textColor=MUTED, alignment=1)))

    doc.build(story)
    buf.seek(0)
    fname = f"GeoSentrix_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=fname)

if __name__ == '__main__':
    app.run(debug=True, port=5050)