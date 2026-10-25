import unittest
import datetime
from app import app
from weather_service import WeatherService
from sun_service import SunService
from airtouch_service import AirTouchService


class BackendTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_api_config_endpoint(self):
        response = self.app.get('/api/config')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("location", data)
        self.assertIn("Ormond", data["location"])
        self.assertIn("pixel_shift_interval_minutes", data)

    def test_api_data_endpoint(self):
        response = self.app.get('/api/data')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("airtouch", data)
        self.assertIn("weather", data)
        self.assertIn("sun", data)
        self.assertEqual(data["timezone"], "Australia/Melbourne")

    def test_weather_service_structure(self):
        ws = WeatherService()
        weather = ws.get_weather()
        self.assertIn("current", weather)
        self.assertIn("hourly", weather)
        self.assertIn("daily", weather)
        self.assertIn("temperature", weather["current"])
        self.assertIn("feels_like", weather["current"])
        self.assertGreaterEqual(len(weather["daily"]), 5)

    def test_sun_service_calculation(self):
        ss = SunService()
        times = ss.get_sun_times()
        self.assertIn("sunrise", times)
        self.assertIn("sunset", times)
        self.assertIn("sunrise_hour", times)
        self.assertIn("sunset_hour", times)
        self.assertLess(times["sunrise_hour"], times["sunset_hour"])

    def test_airtouch_service_fallback(self):
        at = AirTouchService()
        status = at.get_status()
        self.assertIn("rooms", status)
        self.assertIn("ac_units", status)
        self.assertGreater(len(status["rooms"]), 0)
        # Check structure of first room
        first_room = status["rooms"][0]
        self.assertIn("name", first_room)
        self.assertIn("temperature", first_room)


if __name__ == '__main__':
    unittest.main()
