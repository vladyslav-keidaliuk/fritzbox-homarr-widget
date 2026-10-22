"""FRITZ!Box connected network devices discovery and host status parser."""

import xml.etree.ElementTree as ET

from config import (
    ROUTER_IP,
    ROUTER_PORT,
    ROUTER_PROTOCOL,
    ROUTER_TIMEOUT,
    ROUTER_VERIFY_SSL,
    logger,
)
from router.client import session


def fetch_hosts_summary(fc) -> dict | None:
  """Fetches actively connected devices and their details.

  Tries fast single-shot AVM endpoint (X_AVM-DE_GetHostListPath) first;
  falls back to standard FritzHosts iteration.
  """
  # 1. Try single-shot AVM devicehostlist XML endpoint
  try:
    path = None
    for svc in ["Hosts1", "Hosts", "LanDeviceHosts1"]:
      try:
        res = fc.call_action(svc, "X_AVM-DE_GetHostListPath")
        path = res.get("NewX_AVM-DE_HostListPath")
        if path:
          break
      except Exception:
        continue

    if path:
      url = f"{ROUTER_PROTOCOL}://{ROUTER_IP}:{ROUTER_PORT}{path}"
      r = session.get(url, timeout=ROUTER_TIMEOUT, verify=ROUTER_VERIFY_SSL)
      if r.status_code == 200:
        root = ET.fromstring(r.content)
        active_devices = []
        total_count = 0

        for item in root.iter():
          if item.tag.lower() in ("item", "host"):
            total_count += 1
            friendly_name = None
            hostname = None
            ip = None
            mac = None
            itype = ""
            active_val = None

            for child in item:
              tag = child.tag
              val = (child.text or "").strip()
              if tag == "Active":
                active_val = val
              elif tag in ("X_AVM-DE_FriendlyName", "FriendlyName") and val:
                friendly_name = val
              elif tag in ("HostName", "hostname", "Name") and val:
                hostname = val
              elif tag in ("IPAddress", "ip") and val:
                ip = val
              elif tag in ("MACAddress", "mac") and val:
                mac = val
              elif tag in ("InterfaceType", "interface_type", "type") and val:
                itype = val.lower()

            if active_val in ("1", "true", "True", 1):
              # Check interface type: Wi-Fi (802.11 / wlan) vs LAN (Ethernet)
              is_wifi = "802.11" in itype or "wlan" in itype or "wifi" in itype
              dev_name = friendly_name or hostname or ip or "Unnamed Device"
              active_devices.append({
                  "name": dev_name,
                  "ip": ip or "",
                  "mac": mac or "",
                  "type": "wifi" if is_wifi else "lan",
              })

        active_devices.sort(key=lambda d: d["name"].lower())
        return {
            "active_count": len(active_devices),
            "total_count": total_count if total_count > 0 else len(active_devices),
            "active_list": active_devices,
        }
  except Exception as e:
    logger.debug("Fast X_AVM-DE_GetHostListPath lookup failed, trying FritzHosts: %s", e)

  # 2. Fallback to FritzHosts library module
  try:
    from fritzconnection.lib.fritzhosts import FritzHosts

    fh = FritzHosts(fc)
    hosts_info = fh.get_hosts_info()
    active_devices = []
    for h in hosts_info:
      if h.get("status"):
        name = h.get("name") or h.get("ip") or "Unnamed Device"
        ip = h.get("ip") or ""
        mac = h.get("mac") or ""
        itype = str(h.get("interface_type") or "").lower()
        is_wifi = "802.11" in itype or "wlan" in itype or "wifi" in itype
        active_devices.append({
            "name": name,
            "ip": ip,
            "mac": mac,
            "type": "wifi" if is_wifi else "lan",
        })

    active_devices.sort(key=lambda d: d["name"].lower())

    return {
        "active_count": len(active_devices),
        "total_count": len(hosts_info),
        "active_list": active_devices,
    }
  except Exception as e:
    logger.debug("Could not fetch active host list via FritzHosts: %s", e)
    return None
