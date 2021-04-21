import base64
import math


class Utils:

    def string_to_base_64_string(self, string: str) -> str:
        return base64.b64encode(string.encode('ascii')).decode('ascii')

    def calc_insta_values(self, instantaneous_data: list) -> tuple:
        time_delta = instantaneous_data[-1][0] - instantaneous_data[0][0]
        time_delta_numeric = time_delta.seconds + time_delta.microseconds / 1000000.0
        wheel_diameter = 27
        wheel_circ_inches = math.pi * wheel_diameter
        Hz = time_delta_numeric / (len(instantaneous_data) - 1)
        rpm = 60 / Hz
        inch_per_hour = wheel_circ_inches * rpm * 60
        mph = inch_per_hour / (12 * 5280)
        seconds_per_500m = (1 / mph) / 1600 * 500 * 3600

        return mph, seconds_per_500m
