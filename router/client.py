"""FRITZ!Box TR-064 client connection manager and fallback SOAP executor."""

import threading
import xml.etree.ElementTree as ET
import requests
from requests.auth import HTTPDigestAuth

from config import (
    ROUTER_IP,
    ROUTER_PASSWORD,
    ROUTER_PORT,
    ROUTER_PROTOCOL,
    ROUTER_TIMEOUT,
    ROUTER_USERNAME,
    ROUTER_VERIFY_SSL,
    logger,
)

# Optional but recommended fritzconnection library for complete TR-064 compliance
try:
  from fritzconnection import FritzConnection
  from fritzconnection.core.exceptions import (
      FritzActionError,
      FritzConnectionException,
      FritzSecurityError,
  )

  HAS_FRITZCONNECTION = True
except ImportError:
  HAS_FRITZCONNECTION = False

# Shared FritzConnection singleton and thread-safety lock
_fc_instance = None
_fc_lock = threading.Lock()

# Persistent session for raw requests and asset downloads
session = requests.Session()


def get_fritz_connection():
  """Initializes or reuses the thread-safe persistent FritzConnection client."""
  global _fc_instance
  with _fc_lock:
    if _fc_instance is None:
      logger.info(
          "Initializing FritzConnection to %s:%d (user=%s)...",
          ROUTER_IP,
          ROUTER_PORT,
          ROUTER_USERNAME,
      )
      _fc_instance = FritzConnection(
          address=ROUTER_IP,
          port=ROUTER_PORT,
          user=ROUTER_USERNAME,
          password=ROUTER_PASSWORD,
          use_tls=(ROUTER_PROTOCOL == "https"),
          timeout=ROUTER_TIMEOUT,
      )
    return _fc_instance


def reset_fritz_connection():
  """Resets the persistent connection instance so it reconnects on next request."""
  global _fc_instance
  with _fc_lock:
    _fc_instance = None


def execute_raw_soap(control_path: str, service_urn: str, action: str) -> dict:
  """Executes a raw TR-064 SOAP request with HTTP Digest Auth (fallback if fritzconnection is missing)."""
  url = f"{ROUTER_PROTOCOL}://{ROUTER_IP}:{ROUTER_PORT}{control_path}"
  envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:{action} xmlns:u="{service_urn}" />
  </s:Body>
</s:Envelope>"""

  headers = {
      "Content-Type": 'text/xml; charset="utf-8"',
      "SOAPAction": f'"{service_urn}#{action}"',
  }

  auth = (
      HTTPDigestAuth(ROUTER_USERNAME, ROUTER_PASSWORD)
      if (ROUTER_USERNAME and ROUTER_PASSWORD)
      else None
  )

  response = session.post(
      url,
      data=envelope.encode("utf-8"),
      headers=headers,
      auth=auth,
      timeout=ROUTER_TIMEOUT,
      verify=ROUTER_VERIFY_SSL,
  )

  if response.status_code == 401:
    raise PermissionError(
        "HTTP 401 Unauthorized: Invalid username or password for FRITZ!Box user."
    )

  response.raise_for_status()

  root = ET.fromstring(response.content)
  result = {}
  for elem in root.iter():
    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
    if elem.text and elem.text.strip():
      result[tag] = elem.text.strip()
  return result
