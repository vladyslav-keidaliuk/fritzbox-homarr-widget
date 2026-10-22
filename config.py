"""Configuration settings and environment variable definitions for FRITZ!Box Homarr Widget."""

import logging
import os
import urllib3
from dotenv import load_dotenv

# Suppress insecure HTTPS connection warnings (common for router internal self-signed certs)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables from .env file if present
load_dotenv()

# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("fritzbox-widget")

# ---------------------------------------------------------------------------
# Router Connection Settings
# ---------------------------------------------------------------------------
ROUTER_IP = os.getenv("ROUTER_IP", "192.168.178.1").strip()
ROUTER_PORT = int(os.getenv("ROUTER_PORT", "49000"))
ROUTER_PROTOCOL = os.getenv("ROUTER_PROTOCOL", "http").strip().lower()
ROUTER_USERNAME = os.getenv("ROUTER_USERNAME", "").strip()
ROUTER_PASSWORD = os.getenv("ROUTER_PASSWORD", "").strip()
ROUTER_TIMEOUT = float(os.getenv("ROUTER_TIMEOUT", "4.0"))
ROUTER_VERIFY_SSL = os.getenv("ROUTER_VERIFY_SSL", "false").strip().lower() in (
    "true",
    "1",
    "yes",
)

# ---------------------------------------------------------------------------
# Application Server Settings
# ---------------------------------------------------------------------------
PORT = int(os.getenv("PORT", "5050"))
MOCK_MODE = os.getenv("MOCK_MODE", "false").strip().lower() in (
    "true",
    "1",
    "yes",
)

# ---------------------------------------------------------------------------
# Cache TTL Configuration
# ---------------------------------------------------------------------------
METRICS_CACHE_TTL = 1.5   # Fast-changing metrics (bandwidth rates, totals) cached for 1.5s
META_CACHE_TTL = 20.0     # Slower-changing metadata (external IP, Wi-Fi, host list) cached for 20s

# ---------------------------------------------------------------------------
# TR-064 Service & Action Constants
# ---------------------------------------------------------------------------
SERVICE_WAN = "urn:dslforum-org:service:WANCommonInterfaceConfig:1"
ACTION_GET_ADDON_INFOS = "GetAddonInfos"
CONTROL_URL_WAN = "/upnp/control/wancommonifconfig1"
CONTROL_URL_WAN_FALLBACK = "/igdupnp/control/WANCommonIFC1"
SERVICE_WAN_FALLBACK = "urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1"

SERVICE_DEVICE = "urn:dslforum-org:service:DeviceInfo:1"
ACTION_GET_INFO = "GetInfo"
CONTROL_URL_DEVICE = "/upnp/control/deviceinfo"
