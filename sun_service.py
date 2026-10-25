import datetime
import zoneinfo
from suntime import Sun

class SunService:
    # Ormond, Melbourne coordinates
    ORMOND_LAT = -37.8992
    ORMOND_LON = 145.0392
    TIMEZONE_NAME = "Australia/Melbourne"

    def __init__(self):
        self.sun = Sun(self.ORMOND_LAT, self.ORMOND_LON)
        self.tz = zoneinfo.ZoneInfo(self.TIMEZONE_NAME)

    def get_sun_times(self, dt: datetime.date = None) -> dict:
        if dt is None:
            dt = datetime.datetime.now(self.tz).date()

        try:
            # calculate sunrise and sunset in UTC then convert to Melbourne
            sunrise_utc = self.sun.get_sunrise_time(dt)
            sunset_utc = self.sun.get_sunset_time(dt)

            sunrise_local = sunrise_utc.astimezone(self.tz)
            sunset_local = sunset_utc.astimezone(self.tz)

            return {
                "sunrise": sunrise_local.strftime("%H:%M"),
                "sunset": sunset_local.strftime("%H:%M"),
                "sunrise_iso": sunrise_local.isoformat(),
                "sunset_iso": sunset_local.isoformat(),
                "sunrise_hour": sunrise_local.hour + (sunrise_local.minute / 60.0),
                "sunset_hour": sunset_local.hour + (sunset_local.minute / 60.0),
            }
        except Exception:
            # Sensible Melbourne defaults if calculation fails
            return {
                "sunrise": "06:30",
                "sunset": "20:00",
                "sunrise_hour": 6.5,
                "sunset_hour": 20.0,
            }
