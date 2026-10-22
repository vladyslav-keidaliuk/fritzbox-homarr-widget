"""Metric conversion and string formatting helpers."""


def format_uptime(total_seconds: int) -> dict:
  """Formats total seconds into days, hours, minutes, and formatted string."""
  days = total_seconds // 86400
  hours = (total_seconds % 86400) // 3600
  minutes = (total_seconds % 3600) // 60
  secs = total_seconds % 60

  parts = []
  if days > 0:
    parts.append(f"{days}d")
  if hours > 0 or days > 0:
    parts.append(f"{hours}h")
  parts.append(f"{minutes}m")

  formatted = " ".join(parts) if parts else f"{secs}s"

  return {
      "total_seconds": total_seconds,
      "days": days,
      "hours": hours,
      "minutes": minutes,
      "seconds": secs,
      "formatted": formatted,
  }


def format_traffic_rate(bytes_per_sec: int) -> dict:
  """Calculates both Mbps and MB/s from bytes per second and returns formatted dictionary."""
  bits_per_sec = bytes_per_sec * 8
  mbps = round(bits_per_sec / 1_000_000.0, 2)
  mbyte_s = round(bytes_per_sec / (1024.0 * 1024.0), 2)
  kbps = round(bits_per_sec / 1_000.0, 1)
  kbyte_s = round(bytes_per_sec / 1024.0, 1)

  if mbps >= 1.0:
    formatted_mbps = f"{mbps:.2f} Mbps"
  elif kbps >= 1.0:
    formatted_mbps = f"{kbps:.1f} Kbps"
  else:
    formatted_mbps = f"{bits_per_sec} bps"

  if mbyte_s >= 1.0:
    formatted_mbytes = f"{mbyte_s:.2f} MB/s"
  elif kbyte_s >= 1.0:
    formatted_mbytes = f"{kbyte_s:.1f} KB/s"
  else:
    formatted_mbytes = f"{bytes_per_sec} B/s"

  return {
      "bytes_per_sec": bytes_per_sec,
      "bits_per_sec": bits_per_sec,
      "mbps": mbps,
      "mbyte_s": mbyte_s,
      "kbps": kbps,
      "kbyte_s": kbyte_s,
      "formatted": formatted_mbps,
      "formatted_mbps": formatted_mbps,
      "formatted_mbytes": formatted_mbytes,
  }


def format_bytes_human(num_bytes: int) -> str:
  """Converts integer bytes to human-readable format (MB, GB, TB)."""
  val = float(num_bytes)
  for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
    if val < 1024.0 or unit == "PB":
      return f"{val:.2f} {unit}"
    val /= 1024.0
  return f"{val:.2f} B"
