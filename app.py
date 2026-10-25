import os
import logging
from flask import Flask, jsonify, render_template, send_from_directory
from airtouch_service import AirTouchService
from weather_service import WeatherService
from sun_service import SunService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", template_folder="static")

airtouch_service = AirTouchService()
weather_service = WeatherService()
sun_service = SunService()


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/data")
def get_data():
    airtouch_data = airtouch_service.get_status()
    weather_data = weather_service.get_weather()
    sun_data = sun_service.get_sun_times()

    return jsonify({
        "airtouch": airtouch_data,
        "weather": weather_data,
        "sun": sun_data,
        "timezone": "Australia/Melbourne"
    })


@app.route("/api/config")
def get_config():
    return jsonify({
        "location": "Ormond, Melbourne, Victoria, Australia",
        "pixel_shift_interval_minutes": 3,
        "night_dimming": True,
        "overnight_blanking": {
            "enabled": False,
            "start_hour": 23,
            "end_hour": 6
        }
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
