# FRITZ!Box Homarr Widget (FRITZ!OS 8.25+)

A stateless, ultra-lightweight real-time web widget and backend to monitor your AVM FRITZ!Box router directly from your [Homarr](https://homarr.dev/) dashboard via an embedded iFrame tile.

Designed specifically for **FRITZ!OS 8.25** (and compatible with FRITZ!OS 7.50+), strictly adhering to AVM's TR-064 SOAP specifications with HTTP Digest Authentication (RFC 2617).

![Widget Preview](https://img.shields.io/badge/Docker-Alpine%20%3C%2080MB-blue?logo=docker)
![FRITZ!OS](https://img.shields.io/badge/FRITZ!OS-8.25%20Verified-red)
[![Live Demo](https://img.shields.io/badge/Demo-Live%20Preview-brightgreen?logo=github)](https://vladyslav-keidaliuk.github.io/fritzbox-homarr-widget/?demo=1)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🌐 Live Interactive Demo

Experience the widget live in your browser with zero installation:

👉 **[Open Live Demo on GitHub Pages](https://vladyslav-keidaliuk.github.io/fritzbox-homarr-widget/?demo=1)**

- ⚡ Live simulated bandwidth fluctuations and 60-second canvas sparkline.
- 🔄 Click Download / Upload cards to toggle between **`Mbps`** and **`MB/s`**.
- 📶 Click the **`8 active`** badge to open the client inspection modal with search filtering.
- 👁️ Click the WAN IP pill to toggle privacy masking.

---

## Screenshots

<div align="center">
  <img src="docs/screenshots/dashboard.png" alt="FRITZ!Box Homarr Widget Dashboard" width="750" />
</div>

<div align="center">
  <img src="docs/screenshots/active-devices.png" alt="FRITZ!Box Homarr Widget Dashboard" width="750" />
  <p><em>Real-time traffic throughput, line utilization, active devices counter, and 60-second sparkline activity chart.</em></p>
</div>

<div align="center">
  <img src="docs/screenshots/homarr-iframe-widget.png" alt="FRITZ!Box Homarr Widget Dashboard" width="750" />
  <p><em>Homarr real-time iFrame widget.</em></p>
</div>
---

## Features

- **Real-Time Traffic Monitoring**: Queries `urn:dslforum-org:service:WANCommonInterfaceConfig:1` (`GetAddonInfos`) to extract `NewByteReceiveRate` and `NewByteSendRate`, computing live download and upload throughput.
- **Dual Display & Unit Switcher**: Easily switch between **Mbps** (Megabits/s) and **MB/s** (Megabytes/s) via a 1-click toggle, with dual conversions displayed side-by-side.
- **Internet Plan Line Utilization**: Extracts maximum sync bandwidth (`GetCommonLinkProperties`) and shows a live utilization bar with % of your line capacity.
- **Actively Connected Devices & Client Modal**: Real-time badge tracking online active clients (filtering out stale/historical DHCP leases). Click the badge to open an interactive dark-mode popup listing all online devices with hostnames, IP addresses, connection type badges (Wi-Fi 📶 vs LAN 🔌), and instant search filter.
- **External Public IP with Privacy Toggle**: Auto-discovers public WAN IP across DSL/PPPoE, Fiber, and Cable connections with a 1-click privacy mask toggle (👁) to keep IP addresses safe from accidental exposure in screenshots.
- **Wi-Fi Bands & DNS Status**: Real-time indicators showing active broadcasting bands (2.4G + 5G) and primary upstream DNS servers.
- **Accurate Uptime Tracking**: Queries `urn:dslforum-org:service:DeviceInfo:1` (`GetInfo`) to extract `NewUpTime` and cleanly formats it into days, hours, and minutes.
- **Non-blocking & DoS-Protected**: Slower-changing metadata and active host enumeration refresh asynchronously in background worker threads with an in-memory cache layer (`1.5s` traffic, `20s` metadata) to protect router CPU from query exhaustion.
- **FRITZ!OS 8.25 Compatibility**: Handled via `fritzconnection` with full TR-064 challenge-response authentication, nonces, and session reuse.
- **Homarr Dark Mode Native**: Modern slate dark-theme UI with responsive flex layout, subtle glowing accents, and zero scrollbars for iFrame embedding.
- **Embedded Sparkline Graph**: Real-time traffic activity canvas (last 60 seconds) with pure vanilla JS (0 external frontend dependencies).
- **Ultra-lightweight Container**: Built on Alpine Linux (`python:3.12-alpine`) with production Gunicorn WSGI server. Image size is **under 75MB**.
- **Safe Public Repo Setup**: Pre-configured `.gitignore` prevents accidental leaking of router credentials. Template provided in `.env.example`.

---

## Architecture & Endpoints

```
┌────────────────────────┐         SOAP / HTTP Digest Auth         ┌─────────────────────────┐
│                        │────────────────────────────────────────▶│                         │
│  FRITZ!Box Widget      │  GetAddonInfos (Byte Rates, Totals)     │  AVM FRITZ!Box          │
│  (Flask + Gunicorn)    │  GetInfo (Uptime, Firmware, Model)      │  (FRITZ!OS 8.25)        │
│                        │◀────────────────────────────────────────│  Port 49000 / 49443     │
└────────────────────────┘                                         └─────────────────────────┘
         ▲
         │ Polling every 2s (JSON)
         │
┌────────────────────────┐
│  Homarr Dashboard      │
│  (Embedded iFrame)     │
└────────────────────────┘
```

- `GET /` — Dark-mode responsive widget frontend for Homarr.
- `GET /api/metrics` — JSON endpoint returning live bandwidth (Mbps, Kbps, bytes/sec), uptime, and router status.
- `GET /health` — Lightweight health-check endpoint for container orchestration.

---

## 1. FRITZ!Box Preparation (FRITZ!OS 8.25+)

FRITZ!OS 8.25 strictly requires an authenticated user account with TR-064 permissions:

1. **Allow TR-064 Application Access**:
   - Open your router interface (default `http://192.168.178.1` or `http://fritz.box`).
   - Navigate to: **Home Network (*Heimnetz*)** → **Network (*Netzwerk*)** → **Network Settings (*Netzwerkeinstellungen*)**.
   - Under *LAN Settings*, enable the checkbox: **"Allow access for applications" (*Zugriff für Anwendungen zulassen*)**.
   - Click **Apply (*Übernehmen*)**.

2. **Create a Dedicated User Account**:
   - Navigate to: **System** → **FRITZ!Box Users (*FRITZ!Box-Benutzer*)**.
   - Click **Add User (*Benutzer hinzufügen*)**.
   - Set a username (e.g., `homarr-monitor`) and a secure password.
   - Under *Permissions (*Berechtigungen*)*, check **FRITZ!Box Settings (*FRITZ!Box-Einstellungen*)**.
   - Click **Apply (*Übernehmen*)**.

---

## 2. Configuration (`.env`)

Copy the example configuration:
```bash
cp .env.example .env
```

Edit `.env` with your router details:
```env
# Router IP or hostname
ROUTER_IP=192.168.178.1

# TR-064 Port (49000 for HTTP, 49443 for HTTPS)
ROUTER_PORT=49000
ROUTER_PROTOCOL=http

# Router User Credentials (created in step 1)
ROUTER_USERNAME=homarr-monitor
ROUTER_PASSWORD=your_secret_password

# Port where this widget will be served (default: 5050)
PORT=5050

# Set to 'true' if you want simulated metrics for dashboard preview without router access
MOCK_MODE=false
```

> [!IMPORTANT]
> The `.env` file is listed in `.gitignore` and will never be committed to your Git repository.

---

## 3. Running with Docker

### Option A: Docker Compose (Recommended)
```bash
docker compose up -d
```

### Option B: Docker CLI
```bash
# Build the minimal image (~75MB)
docker build -t fritzbox-homarr-widget .

# Run the container
docker run -d \
  --name fritzbox-homarr-widget \
  --restart unless-stopped \
  -p 5050:5050 \
  --env-file .env \
  fritzbox-homarr-widget
```

Verify it is running:
```bash
curl http://localhost:5050/api/metrics
```

---

## 4. Adding to Homarr Dashboard

The widget is specifically designed to embed into Homarr via an **iFrame tile** with zero scrollbars, transparent backgrounds, and a native dark slate theme matching Homarr's UI.

### Step-by-Step Setup

1. **Open Homarr** in your browser and enter **Edit Mode** (click the pencil ✏️ icon in the top navigation).
2. Click **+ Add Item** (or **+ Add Tile**).
3. Search for and select the **`iFrame`** widget (labeled **`Embed`** or **`Custom Web Page`** in some versions).
4. Configure the tile properties:
   - **URL / Source**: 
     - *Local network setup:* `http://<YOUR_SERVER_IP>:5050` (e.g. `http://192.168.178.71:5050`)
     - *Reverse proxy / HTTPS setup:* `https://<YOUR_DOMAIN>/fritz` or relative `/fritz` (see below)
   - **Title**: `FRITZ!Box` *(or leave blank for a clean borderless card)*
   - **Width**: `3` grid units
   - **Height**: `2` grid units *(recommended to comfortably display the sparkline chart and active clients badge)*
5. Click **Save** on the tile, then click the **Save / Checkmark** icon in Homarr's top bar to persist your dashboard layout.

---

### Important: HTTPS & Mixed Content Handling

If your Homarr dashboard is running over **HTTPS** (e.g. at `https://dashboard.yourdomain.com`), modern web browsers strictly block insecure `http://` iFrames due to browser **Mixed Content** security policies.

To embed the widget on an HTTPS dashboard:

#### Method A: Sub-Path Routing on the Same Domain (Recommended)
Route `/fritz` on your existing dashboard domain to the widget container on port `5050`:
- **Coolify**: Set the widget's domain to `https://dashboard.yourdomain.com/fritz`
- **Traefik**: Add a router rule `PathPrefix(`/fritz`)`
- **Caddy**: `handle_path /fritz* { reverse_proxy fritzbox-widget:5050 }`
- **Nginx**: `location /fritz/ { proxy_pass http://fritzbox-widget:5050/; }`

Then in Homarr's iFrame settings, simply set the Embed URL to:
```
/fritz
```
*(or `https://dashboard.yourdomain.com/fritz`)*

Because both Homarr and the widget share the exact same HTTPS domain, it loads with **zero SSL warnings, zero Cloudflare DNS changes, and zero browser blocks**.

#### Method B: Browser Insecure Content Override (Quick Local Testing)
If accessing your HTTPS Homarr without setting up a reverse proxy path:
1. In Chrome, click the **tune / site settings icon (🎚️)** next to your dashboard URL.
2. Open **Site settings** → scroll to **Insecure content** → change to **Allow**.
3. Reload Homarr. The local `http://` iFrame will render immediately.

---

### Interactive Dashboard Features

Once added to your dashboard, the widget provides several interactive controls:
- **Mbps / MB/s Toggle**: Click either the Download or Upload card to switch between Megabits/s and Megabytes/s. Your preferred unit is automatically remembered across reloads.
- **Active Clients Inspection**: Click the **`X active`** badge in the header to open an embedded slide-over modal displaying all currently connected devices with hostnames, IP addresses, Wi-Fi (📶) vs LAN (🔌) indicators, and real-time search filtering. Press <kbd>Esc</kbd> or click <kbd>✕</kbd> to close.
- **Public IP Privacy Mask**: Click the public IP pill (👁) in the bottom bar to toggle masking on/off (`•••.•••.•••.•••`), keeping your real IP safe from accidental exposure in screenshots.

---

## API Response Example (`/api/metrics`)

```json
{
  "status": "online",
  "router": {
    "ip": "192.168.178.1",
    "model": "FRITZ!Box 7530 AX",
    "firmware": "FRITZ!OS 8.25",
    "software_version": "256.08.25",
    "access_type": "DSL",
    "connected_devices": 14
  },
  "traffic": {
    "download": {
      "mbps": 82.45,
      "mbyte_s": 10.31,
      "kbps": 82450.0,
      "bytes_per_sec": 10306250,
      "max_mbps": 100.0,
      "utilization_pct": 82.5,
      "formatted_mbps": "82.45 Mbps",
      "formatted_mbytes": "10.31 MB/s",
      "total_bytes": 48234928120,
      "total_formatted": "44.92 GB"
    },
    "upload": {
      "mbps": 19.32,
      "mbyte_s": 2.42,
      "kbps": 19320.0,
      "bytes_per_sec": 2415000,
      "max_mbps": 40.0,
      "utilization_pct": 48.3,
      "formatted_mbps": "19.32 Mbps",
      "formatted_mbytes": "2.42 MB/s",
      "total_bytes": 5839201948,
      "total_formatted": "5.44 GB"
    }
  },
  "uptime": {
    "total_seconds": 328400,
    "days": 3,
    "hours": 19,
    "minutes": 13,
    "seconds": 20,
    "formatted": "3d 19h 13m"
  },
  "timestamp": "2026-10-22T20:25:30.123456+00:00",
  "mock_mode": false
}
```

---

## Troubleshooting

- **HTTP ERROR 403 on `localhost:5000` (macOS AirPlay conflict)**:
  - macOS Monterey, Ventura, Sonoma, and Sequoia bind port `5000` to Apple's **AirPlay Receiver** (`ControlCenter`) by default.
  - This widget defaults to port **`5050`** to avoid this issue. If you specifically need port `5000`, disable AirPlay Receiver in **System Settings → General → AirDrop & AirPlay → AirPlay Receiver (toggle off)**.
- **HTTP 401 Unauthorized**:
  - Verify that the user exists in **System → FRITZ!Box Users**.
  - Ensure **"Allow access for applications"** is checked in **Home Network → Network → Network Settings**.
  - Modern FRITZ!OS versions do not accept empty usernames.
- **Connection Refused / Timeout**:
  - Ensure the Docker host has network connectivity to the FRITZ!Box IP (usually `192.168.178.1`).
  - If running in Docker across subnets, verify TR-064 port `49000` is routable.
- **Testing the UI without router connection**:
  - Set `MOCK_MODE=true` in `.env` to test layout, canvas charts, and responsiveness.
