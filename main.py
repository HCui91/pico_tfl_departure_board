from writer import Writer
from waveshare_pico_oled_1p3inch import PICO_OLED_1P3INCH
import font
from wlan import WiFi
from synctime import sync_time, localtime
from tflwrapper import TFLWrapper
from weather import OpenWeatherWrapper
from configs import TFL_APP_KEY, WIFI_SSID, WIFI_PASSWORD, WEATHER_API_KEY, WEATHER_LAT, WEATHER_LON

import time
import gc


class TFLDisplay:
    def __init__(self):
        self.screen = PICO_OLED_1P3INCH(rotate=180)
        self.writer = Writer(self.screen, font)
        Writer.set_textpos(self.screen, 0, 0)
        self.wifi = WiFi()
        self.tfl = TFLWrapper(TFL_APP_KEY)
        self.weather = OpenWeatherWrapper(
            WEATHER_API_KEY, WEATHER_LAT, WEATHER_LON)
        self.key_select = self.screen.key0
        self.key_menu = self.screen.key1

    def initialise(self):
        self.screen.init_display()
        self.screen.clear()
        self.writer.mytext("Initialising...", 0)
        self.screen.show()

        # Connect to WiFi
        self.wifi_connected = self.wifi.connect(
            WIFI_SSID, WIFI_PASSWORD, timeout=30)
        if self.wifi_connected:
            self.writer.mytext(f"{self.wifi.status[0]}", 1)
            self.screen.show()
        else:
            self.writer.mytext("Timeout, exiting", 1)
            self.screen.show()
            return False

        # Sync time
        sync_time(max_try=2)  # max_try=2 to avoid long wait
        time_now = localtime() # use user wrapper to get the time with timezone offset
        self.writer.mytext(
            f"{time_now[0]}-{time_now[1]:02d}-{time_now[2]:02d} {time_now[3]:02d}:{time_now[4]:02d}", 2)
        self.screen.show()

        # Test TFL API connection
        tfl_connected = self.tfl.test_connection()
        if tfl_connected:
            self.writer.mytext("TFL API OK", 3)
            self.screen.show()
        else:
            self.writer.mytext(f"TFL API: {tfl_connected}", 3)
            self.screen.show()
            return False

        # Test OpenWeather API connection
        weather_connected = self.weather.test_connection()
        if weather_connected:
            self.writer.mytext("Weather API OK", 4)
            self.screen.show()
        else:
            self.writer.mytext(f"Weather API: {weather_connected}", 4)
            self.screen.show()
            return False

        time.sleep(1)
        gc.collect()
        return True

    def main(self):
        menu = ["Line status",
                "Wood Lane Westbound",
                "Wood Lane Eastbound",
                "White City Westbound",
                "White City Eastbound",
                "System info",
                "Reboot"]
        choice = 0

        self.screen.clear()
        self._show_main_menu(menu, choice)

        idle_time = 0.

        while True:

            if self.key_select.value() == 0 or idle_time > 10.:
                idle_time = 0.
                if choice == 0:
                    self._line_status_board(
                        ["hammersmith-city", "circle", "central"], ["H&C", "Circle", "Central"])
                elif choice == 1:
                    self._departure_board(
                        "Wood Lane Westbound", ["circle", "hammersmith-city"], ["Circle", "H&C"], "940GZZLUWLA", direction="Westbound")
                elif choice == 2:
                    self._departure_board(
                        "Wood Lane Eastbound", ["circle", "hammersmith-city"], ["Circle", "H&C"], "940GZZLUWLA", direction="Eastbound")
                elif choice == 3:
                    self._departure_board(
                        "White City Westbound", ["central"], ["Central"], "940GZZLUWCY", direction="Westbound")
                elif choice == 4:
                    self._departure_board(
                        "White City Eastbound", ["central"], ["Central"], "940GZZLUWCY", direction="Eastbound")
                elif choice == 5:
                    self._system_info()
                    pass
                elif choice == 6:
                    self.screen.clear()
                    self.writer.mytext("Reboot in 5s", 0)
                    self.screen.show()
                    return  # this go back to the power-on loop
                else:
                    print(f"Invalid choice = {choice}")

                gc.collect()
                time.sleep(0.25)  # wait avoid double click
                # show the main menu again
                self._show_main_menu(menu, choice)

            if self.key_menu.value() == 0:
                idle_time = 0.
                choice = (choice+1) % len(menu)

                self._show_main_menu(menu, choice, update=True)

            idle_time += 0.1
            time.sleep(0.1)

    def _show_main_menu(self, menu, choice, update=False):
        if not update:
            self.writer.clear_line(0)
            self.writer.mytext("Main menu", 0)
        self.writer.clear_line(1)
        self.writer.clear_line(2)
        self.writer.clear_line(3)
        self.writer.clear_line(4)
        self.writer.mytext(menu[int(choice+len(menu)-1) % len(menu)], 1)
        self.writer.mytext(f"x {menu[choice]}", 2)
        self.writer.mytext(menu[(choice+1) % len(menu)], 3)
        self.writer.mytext(menu[(choice+2) % len(menu)], 4)
        self.screen.show()

    def _line_status_board(self, lines: list[str], line_titles: list[str]):
        auto_refresh = 600.  # Refresh every 10 minutes

        self.screen.clear()
        self.writer.mytext_both_side("Loading...", f"{localtime()[3]:02d}:{
                                     localtime()[4]:02d}", self.writer.get_num_lines()-1)
        self.screen.show()

        # only display the first N lines fit to the screen
        num_lines = min(self.writer.get_num_lines()-2, len(lines))

        if num_lines < len(lines):
            print(f"Warning: too many lines to display, only the first {
                  num_lines} will be shown")

        lines = lines[:num_lines]
        line_titles = line_titles[:num_lines]

        while True:
            line_status = self.tfl.line_status(lines, short=True)

            self.screen.clear()
            self.writer.mytext_both_side(self.weather.get_weather(), f'{
                                         self.weather.get_temperature():.0f}"C', 0)
            for i in range(num_lines):
                self.writer.mytext_both_side(
                    line_titles[i], line_status[i], i+1)
            self.writer.mytext_both_side("", f"{localtime()[3]:02d}:{
                                         localtime()[4]:02d}", self.writer.get_num_lines()-1)
            last_minute = localtime()[4]
            self.screen.show()

            idle_time = 0.
            for _ in range(int(auto_refresh/.1)):
                if self.key_select.value() == 0:
                    break  # refresh now
                if self.key_menu.value() == 0:
                    return  # go to the main screen
                time.sleep(0.1)
                idle_time += 0.1
                if idle_time > 5.:  # update time every 5 seconds
                    if last_minute != localtime()[4]:
                        # update time only
                        self.writer.clear_line(4)
                        self.writer.mytext_both_side("", f"{localtime()[3]:02d}:{
                            localtime()[4]:02d}", 4)
                        last_minute = localtime()[4]
                        self.screen.show()
                    idle_time = 0.

            # clear screen and refresh
            self.writer.clear_line(4)
            self.writer.mytext_both_side("Updating...", f"{localtime()[3]:02d}:{
                                         localtime()[4]:02d}", 4)
            last_minute = localtime()[4]
            self.screen.show()

    def _departure_board(self, title: str, lines: list[str], line_titles: list[str], stationId: str, direction="all") -> None:
        """Internal function to display departure board for a single station.

        the screen will be updated every 2 * len(lines) seconds with every 2 seconds showing each line's status. 

        Args:
            title (str): Title of the screen
            lines (list[str]): List of line IDs
            line_titles (list[str]): List of line titles
            stationId (str): Station ID
            direction (str, optional): First word of the platform names, e.g. Westbound. Defaults to "all".
        """
        auto_refresh = 2.  # Refresh every 2 * len(lines) seconds

        self.screen.clear()
        self.writer.mytext(title, 0)
        self.screen.show()

        if len(lines) != len(line_titles):
            print("Error: line and line title sizes mismatch")
            return  # back to the main menu

        num_departures = self.writer.get_num_lines() - 1

        while True:
            platform_number, time_to_station, dest = self.tfl.arrival_predict(
                lines, stationId, direction=direction)

            line_status = self.tfl.line_status(lines, short=True)

            self.screen.clear()
            self.writer.mytext(title, 0)

            # if all platforms are the same, only display time
            same_platform = all(
                x == platform_number[0] for x in platform_number)

            for i in range(min(num_departures, len(platform_number))):
                if same_platform:
                    self.writer.mytext_both_side(
                        dest[i], f"{time_to_station[i]//60}", i+1)
                else:
                    self.writer.mytext_both_side(dest[i], f"Pl.{platform_number[i]} {
                        time_to_station[i]//60}", i+1)
            self.screen.show()

            idle_time = 0.
            line_status_to_display = 0
            while line_status_to_display <= len(lines):
                if self.key_select.value() == 0:
                    break  # refresh now
                if self.key_menu.value() == 0:
                    return  # go to the main screen

                if idle_time > auto_refresh:
                    if line_status_to_display == len(lines):
                        break  # all line status displayed, time to refresh
                    self.writer.clear_line(0)
                    self.writer.mytext_both_side(
                        line_titles[line_status_to_display], line_status[line_status_to_display], 0)
                    self.screen.show()
                    line_status_to_display += 1
                    idle_time = 0.
                else:
                    idle_time += 0.1
                    time.sleep(0.1)

            # change the title to "updating"
            self.writer.clear_line(0)
            self.writer.mytext("Updating...", 0)
            self.screen.show()

    def _print_departure_times(self, lines: int, platform_number: list[str], time_to_station: list[int], destinations: list[str]) -> None:
        """Internal function to print departure times on the screen.

        Args:
            lines (int): max number of lines to display
            platform_number (list[str]): list of platform numbers
            time_to_station (list[int]): list of time to station in seconds
            destinations (list[str]): list of destinations
        """
        # if all platforms are the same, only display time
        same_platform = all(
            x == platform_number[0] for x in platform_number)
        for i in range(min(lines, len(platform_number))):
            if same_platform:
                self.writer.mytext_both_side(
                    destinations[i], f"{time_to_station[i]//60}", i+1)
            else:
                self.writer.mytext_both_side(destinations[i], f"Pl.{platform_number[i]} {
                    time_to_station[i]//60}", i+1)

    def _system_info(self):
        while True:
            self.screen.clear()

            mac = ''.join(self.wifi.mac.split(':'))
            self.writer.mytext(f"mac:{mac}", 0)
            self.writer.mytext(f"{self.wifi.status[0]}", 1)

            tfl_connected = self.tfl.test_connection()
            if tfl_connected:
                self.writer.mytext("TFL API OK", 2)
            else:
                self.writer.mytext(f"TFL API: {tfl_connected}", 2)

            weather_connected = self.weather.test_connection()
            if weather_connected:
                self.writer.mytext("Weather API OK", 3)
            else:
                self.writer.mytext(f"Weather API: {weather_connected}", 3)

            time_now = localtime()
            self.writer.mytext(
                f"{time_now[0]}-{time_now[1]:02d}-{time_now[2]:02d} {time_now[3]:02d}:{time_now[4]:02d}", 4)
            self.screen.show()

            for _ in range(10000//100):
                if self.key_select.value() == 0:
                    break
                if self.key_menu.value() == 0:
                    return
                time.sleep(0.1)


# the main loop
while True:
    try:
        app = TFLDisplay()
        if app.initialise():
            app.main()
            print("Exit from the main menu")
        else:
            print("Initialisation failed")
    except Exception as e:
        print(f"Exception: {e}")

    print("Restart in 5 seconds")
    gc.collect()
    time.sleep(5)  # Wait 5 seconds before restarting the loop
