"""A very simple wrapper for the OpenWeather API.

This module provides a simple wrapper for the OpenWeather API. It allows for
testing the connection to the API, and getting the current weather and temperature.
Temperature and weather data are cached until they are expired.

@Author: HCui91
@Repo: https://github.com/HCui91/pico_tfl_departure_board
"""
import urequests
import ujson
import time


class OpenWeatherWrapper:
    last_update = None
    last_status = None
    weather = "Error"
    temperature = float("nan")
    update_interval = 600

    def __init__(self, api_key, lat, lon):
        self.url = f"https://api.openweathermap.org/data/2.5/weather?lat={
            lat}&lon={lon}&appid={api_key}&units=metric"

    def test_connection(self):
        """
        Test the connection to the OpenWeather API
        """
        response = urequests.get(self.url)
        response.close()

        if response.status_code == 200:
            return True
        else:
            return response.status_code

    def _fetch_weather(self):
        """
        Fetch the weather data from the OpenWeather API
        """
        response = urequests.get(self.url)
        self.data = response.json()
        response.close()
        self.last_update = time.time()
        self.last_status = response.status_code
        try:
            self.weather = self.data['weather'][0]['description']
        except:
            self.weather = "Error"
        try:
            self.temperature = float(self.data['main']['temp'])
        except:
            self.temperature = float("nan")
        return

    def get_weather(self):
        """
        Get the weather data from the OpenWeather API
        """
        if self.last_update is None or time.time() - self.last_update > self.update_interval:
            self._fetch_weather()

        return self.weather

    def get_temperature(self):
        """
        Get the temperature from the OpenWeather API
        """
        if self.last_update is None or time.time() - self.last_update > self.update_interval:
            self._fetch_weather()

        return self.temperature
