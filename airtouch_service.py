import asyncio
import os
import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Try importing airtouch4pyapi
try:
    from airtouch4pyapi import AirTouch, AirTouchVersion, AirTouchStatus
    HAS_AIRTOUCH_LIB = True
except ImportError:
    HAS_AIRTOUCH_LIB = False


class AirTouchService:
    def __init__(self, ip_address: Optional[str] = None):
        self.ip_address = ip_address or os.environ.get("AIRTOUCH_IP")
        self.last_update_time: Optional[float] = None
        self.status: str = "disconnected"
        self.error_message: Optional[str] = None
        self.cached_data: Dict[str, Any] = {
            "connected": False,
            "stale": True,
            "last_updated": None,
            "rooms": [],
            "ac_units": [],
            "mode": "Off"
        }

    def _get_mock_data(self) -> Dict[str, Any]:
        """Provides realistic fallback/mock readings for testing or offline demonstration."""
        return {
            "connected": False,
            "stale": True,
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "mode": "Cool",
            "rooms": [
                {
                    "id": 1,
                    "name": "Living Room",
                    "temperature": 22.5,
                    "target_temperature": 22.0,
                    "is_on": True,
                    "open_percent": 100,
                    "has_sensor": True
                },
                {
                    "id": 2,
                    "name": "Master Bedroom",
                    "temperature": 20.8,
                    "target_temperature": 21.0,
                    "is_on": True,
                    "open_percent": 80,
                    "has_sensor": True
                },
                {
                    "id": 3,
                    "name": "Study / Home Office",
                    "temperature": 21.4,
                    "target_temperature": 22.0,
                    "is_on": True,
                    "open_percent": 60,
                    "has_sensor": True
                },
                {
                    "id": 4,
                    "name": "Guest Bedroom",
                    "temperature": 23.1,
                    "target_temperature": 22.0,
                    "is_on": False,
                    "open_percent": 0,
                    "has_sensor": True
                },
                {
                    "id": 5,
                    "name": "Kitchen & Dining",
                    "temperature": 22.8,
                    "target_temperature": 22.0,
                    "is_on": True,
                    "open_percent": 100,
                    "has_sensor": True
                }
            ],
            "ac_units": [
                {
                    "id": 0,
                    "name": "Main AC",
                    "is_on": True,
                    "mode": "Cool",
                    "fan_speed": "Auto",
                    "target_temperature": 22.0
                }
            ]
        }

    async def _fetch_from_airtouch(self) -> Dict[str, Any]:
        if not HAS_AIRTOUCH_LIB or not self.ip_address:
            raise ValueError("AirTouch IP address not configured or library missing")

        at = AirTouch(self.ip_address, AirTouchVersion.AIRTOUCH5)
        await at.UpdateInfo()

        if at.Status != AirTouchStatus.OK:
            errs = [msg.Message for msg in getattr(at, "Messages", [])]
            raise RuntimeError(f"AirTouch communication failed: {', '.join(errs) or 'Unknown error'}")

        rooms = []
        for group_num, group in at.GetGroups().items():
            temp = getattr(group, "Temperature", 0.0)
            target = getattr(group, "TargetSetpoint", 0.0)
            has_sensor = temp > 0 and temp < 60  # Valid sensor range in Celsius

            rooms.append({
                "id": group_num,
                "name": getattr(group, "GroupName", f"Zone {group_num}"),
                "temperature": round(temp, 1) if has_sensor else None,
                "target_temperature": round(target, 1) if target > 0 else None,
                "is_on": getattr(group, "IsOn", False) or getattr(group, "PowerState", False),
                "open_percent": getattr(group, "OpenPercent", 0),
                "has_sensor": has_sensor
            })

        ac_units = []
        main_mode = "Unknown"
        for ac_num, ac in at.GetAcs().items():
            mode = str(getattr(ac, "AcMode", getattr(ac, "Mode", "Auto")))
            fan = str(getattr(ac, "FanSpeed", "Auto"))
            is_on = getattr(ac, "IsOn", False) or getattr(ac, "PowerState", False)
            if is_on:
                main_mode = mode
            ac_units.append({
                "id": ac_num,
                "name": getattr(ac, "AcName", f"AC {ac_num}"),
                "is_on": is_on,
                "mode": mode,
                "fan_speed": fan,
                "target_temperature": getattr(ac, "TargetSetpoint", None)
            })

        if not ac_units:
            main_mode = "Off"

        return {
            "connected": True,
            "stale": False,
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "mode": main_mode,
            "rooms": rooms,
            "ac_units": ac_units
        }

    def get_status(self) -> Dict[str, Any]:
        """Fetches status, updating cache if older than 15s or on demand."""
        now = time.time()
        # If cache is valid (< 15 seconds), return it
        if self.last_update_time and (now - self.last_update_time < 15):
            return self.cached_data

        if self.ip_address and HAS_AIRTOUCH_LIB:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                data = loop.run_until_complete(self._fetch_from_airtouch())
                self.cached_data = data
                self.last_update_time = now
                self.status = "connected"
                self.error_message = None
                return self.cached_data
            except Exception as e:
                logger.warning(f"Failed to query AirTouch at {self.ip_address}: {e}")
                self.status = "error"
                self.error_message = str(e)
                # Keep last successful rooms/ac_units if available, but mark stale
                if self.cached_data and self.cached_data.get("rooms"):
                    self.cached_data["connected"] = False
                    self.cached_data["stale"] = True
                    return self.cached_data
            finally:
                loop.close()

        # Fallback to mock data if no IP or connection failed and no previous cache
        mock = self._get_mock_data()
        self.cached_data = mock
        self.last_update_time = now
        return self.cached_data
