"""Mock metrics generator for offline testing and Homarr UI layout preview."""

from datetime import datetime, timezone
import math
import random
import time

from config import ROUTER_IP
from utils.formatters import format_bytes_human, format_traffic_rate, format_uptime

_mock_start_time = time.time() - 3600 * 24 * 3  # 3 days ago


def generate_mock_metrics() -> dict:
  """Generates simulated real-time metrics for local development and Homarr preview."""
  now = time.time()
  uptime_sec = int(now - _mock_start_time)

  t = now * 0.5
  down_mbps = max(
      2.5, round(45.0 + 30.0 * math.sin(t) + random.uniform(-4.0, 4.0), 2)
  )
  up_mbps = max(
      0.8, round(12.0 + 8.0 * math.cos(t * 0.7) + random.uniform(-1.5, 1.5), 2)
  )

  down_bytes_sec = int((down_mbps * 1_000_000) / 8)
  up_bytes_sec = int((up_mbps * 1_000_000) / 8)

  max_down_mbps = 112.1
  max_up_mbps = 31.3

  return {
      "status": "online",
      "router": {
          "ip": ROUTER_IP,
          "model": "FRITZ!Box 7530 AX (Simulation)",
          "software_version": "256.08.25",
          "firmware": "FRITZ!OS 8.25",
          "access_type": "VDSL2",
          "external_ip": "93.180.42.15",
          "is_connected": True,
          "dns_servers": "1.1.1.1, 1.0.0.1",
          "wifi_bands": "2.4G + 5G",
          "connected_devices": 8,
          "total_devices": 94,
          "active_devices_list": [
              {"name": "MacBook-Pro-M2", "ip": "192.168.178.20", "type": "wifi"},
              {"name": "iPhone-15-Pro", "ip": "192.168.178.25", "type": "wifi"},
              {"name": "iPad-Air", "ip": "192.168.178.28", "type": "wifi"},
              {"name": "Samsung-Smart-TV", "ip": "192.168.178.30", "type": "lan"},
              {"name": "Synology-NAS", "ip": "192.168.178.35", "type": "lan"},
              {"name": "HomePod-Mini", "ip": "192.168.178.42", "type": "wifi"},
              {"name": "Philips-Hue-Bridge", "ip": "192.168.178.50", "type": "lan"},
              {"name": "Apple-Watch", "ip": "192.168.178.55", "type": "wifi"},
          ],
      },
      "traffic": {
          "download": {
              **format_traffic_rate(down_bytes_sec),
              "max_mbps": max_down_mbps,
              "utilization_pct": round(
                  min(100.0, (down_mbps / max_down_mbps) * 100), 1
              ),
              "total_bytes": 14_850_000_000,
              "total_formatted": format_bytes_human(14_850_000_000),
          },
          "upload": {
              **format_traffic_rate(up_bytes_sec),
              "max_mbps": max_up_mbps,
              "utilization_pct": round(
                  min(100.0, (up_mbps / max_up_mbps) * 100), 1
              ),
              "total_bytes": 2_350_000_000,
              "total_formatted": format_bytes_human(2_350_000_000),
          },
      },
      "uptime": format_uptime(uptime_sec),
      "timestamp": datetime.now(timezone.utc).isoformat(),
      "mock_mode": True,
  }
