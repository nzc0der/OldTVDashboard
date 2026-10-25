python
import asyncio
import logging
import math
import time
from typing import Any, Dict, Optional

from airtouch4pyapi import AirTouch, AirTouchVersion, AirTouchStatus

logger = logging.getLogger(__name__)


class AirTouchService:
    IP_ADDRESS = "192.168.1.106"
    PORT = 9005

    def __init__(self):
        self.ip_address = self.IP_ADDRESS
        self.port = self.PORT

        self.last_update_time: Optional[float] = None
        self.status = "disconnected"
        self.error_message: Optional[str] = None

        self.cached_data: Dict[str, Any] = {
            "connected": False,
            "stale": True,
            "last_updated": None,
            "rooms": [],
            "ac_units": [],
            "mode": "Unknown",
        }

    @staticmethod
    def _get(obj, *names, default=None):
        """Get the first available non-callable property."""
        for name in names:
            try:
                value = getattr(obj, name)
                if not callable(value) and value is not None:
                    return value
            except (AttributeError, TypeError):
                continue
        return default

    @staticmethod
    def _number(value):
        try:
            number = float(value)
            return number if math.isfinite(number) else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _boolean(value):
        if isinstance(value, str):
            return value.strip().lower() in ("true", "yes", "on", "1")
        return bool(value)

    @staticmethod
    def _get_collection(at, attribute, getter):
        collection = getattr(at, attribute, None)

        if isinstance(collection, dict):
            return collection

        method = getattr(at, getter, None)
        if callable(method):
            result = method()
            if isinstance(result, dict):
                return result

        return {}

    async def _fetch_from_airtouch(self):
        # Explicitly use the known working AirTouch 5 endpoint.
        at = AirTouch(
            "192.168.1.106",
            AirTouchVersion.AIRTOUCH5,
            port=9005,
        )

        await at.UpdateInfo()

        if at.Status != AirTouchStatus.OK:
            errors = [
                str(self._get(message, "Message", default=message))
                for message in getattr(at, "Messages", [])
            ]
            raise RuntimeError(
                "AirTouch connection failed: "
                + ("; ".join(errors) if errors else str(at.Status))
            )

        rooms = []

        groups = self._get_collection(at, "groups", "GetGroups")

        for group_id, group in groups.items():
            temperature = self._number(
                self._get(group, "Temperature", "CurrentTemperature")
            )
            target = self._number(
                self._get(
                    group,
                    "TargetSetpoint",
                    "TargetTemperature",
                    "Setpoint",
                )
            )

            if temperature is not None and not 0 < temperature < 60:
                temperature = None

            if target is not None and not 5 <= target <= 40:
                target = None

            name = self._get(group, "GroupName", "Name", "name")
            power = self._get(
                group, "IsOn", "PowerState", "Enabled", default=False
            )
            opening = self._number(
                self._get(
                    group, "OpenPercent", "DamperPosition", "Position"
                )
            )

            rooms.append({
                "id": group_id,
                "name": str(name or f"Zone {group_id}"),
                "temperature": (
                    round(temperature, 1)
                    if temperature is not None else None
                ),
                "target_temperature": (
                    round(target, 1) if target is not None else None
                ),
                "is_on": self._boolean(power),
                "open_percent": opening,
                "has_sensor": temperature is not None,
            })

        ac_units = []
        main_mode = "Standby"

        acs = self._get_collection(at, "acs", "GetAcs")

        for ac_id, ac in acs.items():
            raw_mode = self._get(ac, "AcMode", "Mode", default="Unknown")
            raw_fan = self._get(
                ac, "AcFanSpeed", "FanSpeed", default="Unknown"
            )

            mode = str(getattr(raw_mode, "name", raw_mode))
            fan_speed = str(getattr(raw_fan, "name", raw_fan))

            power = self._get(
                ac, "IsOn", "PowerState", default=False
            )
            is_on = self._boolean(power)

            target = self._number(
                self._get(
                    ac,
                    "TargetSetpoint",
                    "TargetTemperature",
                    "Setpoint",
                )
            )

            name = self._get(ac, "AcName", "Name", "name")
            actual_id = self._get(ac, "AcNumber", default=ac_id)

            ac_units.append({
                "id": actual_id,
                "name": str(name or f"AC {ac_id}"),
                "is_on": is_on,
                "mode": mode,
                "fan_speed": fan_speed,
                "target_temperature": target,
            })

            if is_on:
                main_mode = (
                    mode if mode.lower() != "unknown" else "On"
                )

        if not ac_units:
            main_mode = "Off"

        now = time.time()

        return {
            "connected": True,
            "stale": False,
            "last_updated": time.strftime(
                "%Y-%m-%dT%H:%M:%S%z", time.localtime(now)
            ),
            "mode": main_mode,
            "rooms": rooms,
            "ac_units": ac_units,
        }

    def get_status(self, force_refresh=False):
        """Return cached status for 15 seconds, or fetch fresh readings."""
        now = time.time()

        if (
            not force_refresh
            and self.last_update_time is not None
            and now - self.last_update_time < 15
        ):
            return self.cached_data

        loop = asyncio.new_event_loop()

        try:
            data = loop.run_until_complete(self._fetch_from_airtouch())

            self.cached_data = data
            self.last_update_time = time.time()
            self.status = "connected"
            self.error_message = None

        except Exception as exc:
            self.status = "error"
            self.error_message = str(exc)

            logger.exception(
                "AirTouch query failed at %s:%s",
                self.ip_address,
                self.port,
            )

            # Never invent live readings when the controller is offline.
            self.cached_data["connected"] = False
            self.cached_data["stale"] = True

        finally:
            loop.close()

        return self.cached_data
