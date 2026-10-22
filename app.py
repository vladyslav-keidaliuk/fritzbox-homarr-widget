"""FRITZ!Box Homarr Dashboard Widget Backend Application Entrypoint.

Lightweight, stateless Flask application serving real-time TR-064 metrics.
"""

from datetime import datetime, timezone
import time
from flask import Flask, jsonify, render_template, request

from config import (
    ACTION_GET_ADDON_INFOS,
    ACTION_GET_INFO,
    CONTROL_URL_DEVICE,
    CONTROL_URL_WAN,
    METRICS_CACHE_TTL,
    MOCK_MODE,
    PORT,
    ROUTER_IP,
    ROUTER_PORT,
    ROUTER_PROTOCOL,
    ROUTER_USERNAME,
    SERVICE_DEVICE,
    SERVICE_WAN,
    logger,
)
from router.client import (
    HAS_FRITZCONNECTION,
    execute_raw_soap,
    get_fritz_connection,
    reset_fritz_connection,
)
from router.mock import generate_mock_metrics
from router.status import meta_cache
from utils.formatters import (
    format_bytes_human,
    format_traffic_rate,
    format_uptime,
)

# Initialize Flask app
app = Flask(__name__, template_folder=".")

# Fast traffic metrics cache (1.5s TTL to prevent router CPU exhaustion)
_metrics_cache = {
    "data": None,
    "timestamp": 0.0,
}


@app.after_request
def set_security_headers(response):
  """Applies hardened security headers while permitting Homarr dashboard iFrame embedding."""
  response.headers["X-Content-Type-Options"] = "nosniff"
  response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
  response.headers["Permissions-Policy"] = (
      "geolocation=(), camera=(), microphone=(), payment=()"
  )
  response.headers["Content-Security-Policy"] = (
      "default-src 'self' 'unsafe-inline' data:; frame-ancestors *;"
  )
  return response


@app.route("/")
def index():
  """Renders the dark-mode responsive dashboard frontend."""
  return render_template("index.html")


@app.route("/health")
def health():
  """Lightweight Docker container health-check endpoint."""
  return jsonify({"status": "healthy"}), 200


@app.route("/api/metrics")
def get_metrics():
  """TR-064 metrics API endpoint queried by the frontend every 2 seconds."""
  global _metrics_cache

  use_mock = MOCK_MODE or request.args.get("mock", "").lower() in (
      "1",
      "true",
      "yes",
  )
  if use_mock:
    return jsonify(generate_mock_metrics()), 200

  now = time.time()
  # Serve cached traffic metrics if within TTL to protect router CPU
  if (
      _metrics_cache["data"] is not None
      and (now - _metrics_cache["timestamp"]) < METRICS_CACHE_TTL
  ):
    return jsonify(_metrics_cache["data"]), 200

  try:
    if HAS_FRITZCONNECTION:
      fc = get_fritz_connection()

      # 1. Fetch real-time WAN traffic rates
      try:
        wan_data = fc.call_action("WANCommonIFC1", "GetAddonInfos")
      except Exception:
        wan_data = fc.call_action("WANCommonInterfaceConfig1", "GetAddonInfos")

      recv_rate = int(wan_data.get("NewByteReceiveRate", 0))
      send_rate = int(wan_data.get("NewByteSendRate", 0))
      total_recv = int(
          wan_data.get("NewTotalBytesReceived")
          or wan_data.get("NewTotalBytesReceive")
          or 0
      )
      total_sent = int(
          wan_data.get("NewTotalBytesSent")
          or wan_data.get("NewTotalBytesSend")
          or 0
      )

      # 2. Fetch Device Info (uptime & firmware)
      try:
        device_data = fc.call_action("DeviceInfo1", "GetInfo")
      except Exception:
        device_data = fc.call_action("DeviceInfo", "GetInfo")

      uptime_sec = int(device_data.get("NewUpTime", 0))
      model_name = getattr(fc, "modelname", "FRITZ!Box")
      raw_version = getattr(fc, "system_version", "8.25")

      # 3. Fetch Link Properties (sync speeds)
      max_down_bps = 0
      max_up_bps = 0
      wan_type = "WAN"
      try:
        try:
          link_props = fc.call_action("WANCommonIFC1", "GetCommonLinkProperties")
        except Exception:
          link_props = fc.call_action(
              "WANCommonInterfaceConfig1", "GetCommonLinkProperties"
          )
        max_down_bps = int(link_props.get("NewLayer1DownstreamMaxBitRate", 0))
        max_up_bps = int(link_props.get("NewLayer1UpstreamMaxBitRate", 0))
        wan_type = link_props.get("NewWANAccessType", "WAN")
      except Exception as le:
        logger.debug("Could not fetch link properties: %s", le)

      # 4. Connected devices quick count fallback
      connected_devices = None
      try:
        hosts_res = fc.call_action("Hosts1", "GetHostNumberOfEntries")
        connected_devices = int(hosts_res.get("NewHostNumberOfEntries", 0))
      except Exception:
        pass

      # 5. Trigger asynchronous background metadata refresh if stale
      if meta_cache.is_stale():
        meta_cache.refresh_async(fc)

    else:
      # Fallback raw SOAP requests
      wan_data = execute_raw_soap(
          CONTROL_URL_WAN, SERVICE_WAN, ACTION_GET_ADDON_INFOS
      )
      recv_rate = int(wan_data.get("NewByteReceiveRate", 0))
      send_rate = int(wan_data.get("NewByteSendRate", 0))
      total_recv = int(
          wan_data.get("NewTotalBytesReceived")
          or wan_data.get("NewTotalBytesReceive")
          or 0
      )
      total_sent = int(
          wan_data.get("NewTotalBytesSent")
          or wan_data.get("NewTotalBytesSend")
          or 0
      )

      device_data = execute_raw_soap(
          CONTROL_URL_DEVICE, SERVICE_DEVICE, ACTION_GET_INFO
      )
      uptime_sec = int(device_data.get("NewUpTime", 0))
      model_name = device_data.get("NewModelName", "FRITZ!Box")
      raw_version = device_data.get("NewSoftwareVersion", "8.25")
      max_down_bps = 0
      max_up_bps = 0
      wan_type = "WAN"
      connected_devices = None

    # DNS extraction
    dns1 = wan_data.get("NewDNSServer1", "").strip()
    dns2 = wan_data.get("NewDNSServer2", "").strip()
    dns_display = ", ".join(filter(None, [dns1, dns2])) or "Auto"

    # Line capacity and utilization calculations
    max_down_mbps = round(max_down_bps / 1_000_000.0, 1) if max_down_bps > 0 else None
    max_up_mbps = round(max_up_bps / 1_000_000.0, 1) if max_up_bps > 0 else None

    down_util_pct = (
        round(min(100.0, ((recv_rate * 8) / max_down_bps) * 100), 1)
        if max_down_bps > 0
        else 0.0
    )
    up_util_pct = (
        round(min(100.0, ((send_rate * 8) / max_up_bps) * 100), 1)
        if max_up_bps > 0
        else 0.0
    )

    # Firmware formatting
    if "." in raw_version:
      parts = raw_version.split(".")
      firmware_display = f"FRITZ!OS {parts[-2]}.{parts[-1]}"
    else:
      firmware_display = f"FRITZ!OS {raw_version}"

    # Extract active hosts vs historical registered devices from cache
    meta_snap = meta_cache.data
    active_devices_count = connected_devices
    total_devices_count = connected_devices
    active_list = []
    if meta_snap.get("devices_summary"):
      active_devices_count = meta_snap["devices_summary"]["active_count"]
      total_devices_count = meta_snap["devices_summary"]["total_count"]
      active_list = meta_snap["devices_summary"]["active_list"]

    response_data = {
        "status": "online",
        "router": {
            "ip": ROUTER_IP,
            "model": model_name,
            "software_version": raw_version,
            "firmware": firmware_display,
            "access_type": wan_type,
            "external_ip": meta_snap["external_ip"],
            "is_connected": meta_snap["is_connected"],
            "dns_servers": dns_display,
            "wifi_bands": meta_snap["wifi_bands"],
            "connected_devices": active_devices_count,
            "total_devices": total_devices_count,
            "active_devices_list": active_list,
        },
        "traffic": {
            "download": {
                **format_traffic_rate(recv_rate),
                "max_mbps": max_down_mbps,
                "utilization_pct": down_util_pct,
                "total_bytes": total_recv,
                "total_formatted": format_bytes_human(total_recv),
            },
            "upload": {
                **format_traffic_rate(send_rate),
                "max_mbps": max_up_mbps,
                "utilization_pct": up_util_pct,
                "total_bytes": total_sent,
                "total_formatted": format_bytes_human(total_sent),
            },
        },
        "uptime": format_uptime(uptime_sec),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mock_mode": False,
    }

    _metrics_cache["data"] = response_data
    _metrics_cache["timestamp"] = now

    return jsonify(response_data), 200

  except Exception as e:
    reset_fritz_connection()
    logger.exception("TR-064 Query failed: %s", e)

    err_msg = str(e)
    if "401" in err_msg or "security" in err_msg.lower() or "auth" in err_msg.lower():
      user_hint = (
          f"Authentication failed for user '{ROUTER_USERNAME}'. Check your"
          " password in .env."
      )
    elif "refused" in err_msg.lower():
      user_hint = (
          f"Connection refused at {ROUTER_IP}:{ROUTER_PORT}. Check that 'Permit"
          " access for apps' is active."
      )
    else:
      user_hint = f"Error querying FRITZ!Box: {err_msg[:120]}"

    return (
        jsonify({
            "status": "error",
            "error_type": type(e).__name__,
            "message": user_hint,
            "router": {"ip": ROUTER_IP, "model": "FRITZ!Box"},
            "traffic": {
                "download": {"mbps": 0.0, "formatted": "0.00 Mbps"},
                "upload": {"mbps": 0.0, "formatted": "0.00 Mbps"},
            },
            "uptime": {"formatted": "--"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }),
        200,
    )


if __name__ == "__main__":
  logger.info("Starting FRITZ!Box Homarr Widget on port %d...", PORT)
  logger.info("Target Router: %s://%s:%d", ROUTER_PROTOCOL, ROUTER_IP, ROUTER_PORT)
  if MOCK_MODE:
    logger.info("Mock mode is enabled (generating simulated traffic).")
  app.run(host="0.0.0.0", port=PORT, debug=False)
