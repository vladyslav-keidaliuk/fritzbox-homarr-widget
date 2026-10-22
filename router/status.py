"""FRITZ!Box connection status, external IP, Wi-Fi, and thread-safe metadata cache."""

import threading
import time

from config import META_CACHE_TTL, logger
from router.hosts import fetch_hosts_summary


def get_external_ip(fc) -> str | None:
  """Discovers and retrieves the router's external public IP address.

  Supports PPPoE (DSL), Fiber, and Cable connection services.
  """
  for service in [
      "WANPPPConn1",
      "WANPPPConnection1",
      "WANIPConn1",
      "WANIPConnection1",
  ]:
    try:
      res = fc.call_action(service, "GetExternalIPAddress")
      ip = res.get("NewExternalIPAddress", "").strip()
      if ip and ip != "0.0.0.0":
        return ip
    except Exception:
      pass

  # Fallback to FritzStatus
  try:
    from fritzconnection.lib.fritzstatus import FritzStatus

    fs = FritzStatus(fc)
    ip = fs.external_ip
    if ip and ip != "0.0.0.0":
      return ip
  except Exception:
    pass

  return None


def get_wifi_bands(fc) -> str | None:
  """Checks which wireless frequency bands (2.4G / 5G) are currently enabled."""
  wifi_bands = []
  try:
    w1 = fc.call_action("WLANConfiguration1", "GetInfo")
    if w1.get("NewEnable") in (True, 1, "1"):
      wifi_bands.append("2.4G")
  except Exception:
    pass

  try:
    w2 = fc.call_action("WLANConfiguration2", "GetInfo")
    if w2.get("NewEnable") in (True, 1, "1"):
      wifi_bands.append("5G")
  except Exception:
    pass

  return " + ".join(wifi_bands) if wifi_bands else None


class MetadataCacheManager:
  """Thread-safe background metadata cache manager for slower-changing router properties."""

  def __init__(self):
    self._lock = threading.Lock()
    self._is_updating = False
    self.data = {
        "external_ip": None,
        "wifi_bands": None,
        "is_connected": True,
        "devices_summary": None,
        "timestamp": 0.0,
    }

  def is_stale(self) -> bool:
    """Returns True if cache timestamp exceeds META_CACHE_TTL."""
    return (time.time() - self.data["timestamp"]) > META_CACHE_TTL

  def refresh_async(self, fc):
    """Launches an asynchronous background worker to update metadata without blocking the API."""
    with self._lock:
      if self._is_updating:
        return
      self._is_updating = True

    thread = threading.Thread(
        target=self._worker, args=(fc,), daemon=True, name="MetaCacheWorker"
    )
    thread.start()

  def _worker(self, fc):
    try:
      ext_ip = get_external_ip(fc)
      devs_summary = fetch_hosts_summary(fc)
      wifi_str = get_wifi_bands(fc)

      is_conn = True
      try:
        from fritzconnection.lib.fritzstatus import FritzStatus

        fs = FritzStatus(fc)
        is_conn = fs.is_connected
      except Exception as fe:
        logger.debug("Could not query FritzStatus connection state: %s", fe)

      with self._lock:
        self.data["external_ip"] = ext_ip
        if devs_summary:
          self.data["devices_summary"] = devs_summary
        self.data["is_connected"] = is_conn
        self.data["wifi_bands"] = wifi_str
        self.data["timestamp"] = time.time()
    except Exception as e:
      logger.debug("Metadata background update failed: %s", e)
    finally:
      with self._lock:
        self._is_updating = False


# Shared metadata cache singleton
meta_cache = MetadataCacheManager()
