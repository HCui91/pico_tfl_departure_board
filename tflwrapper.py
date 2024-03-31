"""A very simple wrapper for the TFL API.

This module provides a simple wrapper for the TFL API. It allows for testing 
the connection to the API, getting the status of a given line, and getting 
arrival predictions for a given line and station.

@Author: HCui91
@Repo: https://github.com/HCui91/pico_tfl_departure_board
"""

import urequests
import ujson


class TFLWrapper:
    def __init__(self, app_key: str) -> None:
        """
        Initialize the TFLWrapper class with the provided app_key.

        Args:
            app_key (str): The TFL API app key.
        """
        self.app_key = app_key

    def test_connection(self) -> bool | int:
        """
        Test the connection to the TFL API.

        Returns:
            bool or int: True if the connection is successful, otherwise the HTTP status code.
        """
        url = f"https://api.tfl.gov.uk/Line/Meta/Modes?app_key={self.app_key}"
        response = urequests.get(url)
        response.close()
        if response.status_code == 200:
            return True
        else:
            return response.status_code

    def _fetch_status(self, line: str, short: bool = True) -> str:
        """
        Get the status of a given line.

        Args:
            line (str): The line ID.
            short (bool, optional): Whether to return the status in a short form. Defaults to True.

        Returns:
            str: The status of the line.
        """
        url = f"https://api.tfl.gov.uk/Line/{
            line}/Status?app_key={self.app_key}"
        response = urequests.get(url)
        data = response.json()
        response.close()
        status = str(data[0]['lineStatuses'][0]['statusSeverityDescription'])

        if short:
            if status == "Good Service":
                return "Good"
            else:
                return status
        else:
            return status

    def _fetch_arrivals(self, line: str, stationId: str, direction: str = "all", sort: bool = True) -> tuple[list[str], list[int], list[str]]:
        """
        Get arrival predictions for a given line and station.

        Args:
            line (str): The line ID.
            stationId (str): The station ID.
            direction (str, optional): The direction of the arrivals (first word of the platform name). Defaults to "all".
            sort (bool, optional): Whether to sort the predictions by time_to_station. Defaults to True.

        Returns:
            tuple: A tuple containing lists of platform numbers, time to station, and destination.
        """
        url = f"https://api.tfl.gov.uk/Line/{line}/Arrivals/{
            stationId}?direction=all&app_key={self.app_key}"
        response = urequests.get(url)
        data = response.json()
        response.close()

        platform_number = []
        time_to_station = []
        destinations = []
        for arrival in data:
            platform_name = arrival['platformName'].split()
            if direction is not "all":
                if platform_name[0] != direction:
                    continue
            platform_number.append(str(platform_name[-1]))
            time_to_station.append(int(arrival['timeToStation']))
            destinations.append(str(arrival['towards']))

        if sort:
            time_to_station, platform_number, destinations = zip(
                *sorted(zip(time_to_station, platform_number, destinations)))

        return platform_number, time_to_station, destinations

    def line_status(self, lines: list[str], short: bool = True) -> list[str]:
        """
        Get the status of multiple lines.

        Args:
            lines (List[str]): A list of line IDs.
            short (bool, optional): Whether to return the status in a short form. Defaults to True.

        Returns:
            List[str]: A list of the status of the lines.
        """
        status = []
        for line in lines:
            status.append(self._fetch_status(line, short=short))
        return status

    def arrival_predict(self, lines: list[str], stationId: str, direction: str = "all", sort: bool = True) -> tuple[list[str], list[int], list[str]]:
        """
        Get arrival predictions for multiple lines at a given station. Useful for station platforms that serve multiple lines.

        Args:
            lines (List[str]): A list of line IDs.
            stationId (str): The station ID.
            direction (str, optional): The direction of the arrivals. Defaults to None.
            sort (bool, optional): Whether to sort the predictions by time_to_station. Defaults to True.

        Returns:
            tuple: A tuple containing lists of platform numbers, time to station, and towards.
        """
        platform_number = []
        time_to_station = []
        towards = []

        for line in lines:
            line_platform_number, line_time_to_station, line_towards = self._fetch_arrivals(
                line, stationId, direction=direction, sort=False)
            platform_number += line_platform_number
            time_to_station += line_time_to_station
            towards += line_towards

        if sort:
            time_to_station, platform_number, towards = zip(
                *sorted(zip(time_to_station, platform_number, towards)))

        return platform_number, time_to_station, towards
