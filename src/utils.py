import base64
import datetime
import math

wheel_diameter = 27
wheel_circ_inches = math.pi * wheel_diameter

class Utils:

    def string_to_base_64_string(self, string: str) -> str:
        return base64.b64encode(string.encode('ascii')).decode('ascii')

    def calc_insta_values(self, instantaneous_data: list) -> float:
        start_time = datetime.datetime.strptime(instantaneous_data[0][0], '%Y-%m-%dT%H:%M:%S.%f+00:00')
        end_time = datetime.datetime.strptime(instantaneous_data[-1][0], '%Y-%m-%dT%H:%M:%S.%f+00:00')
        time_delta = end_time - start_time
        time_delta_numeric = time_delta.seconds + time_delta.microseconds / 1000000.0
        Hz = time_delta_numeric / (len(instantaneous_data) - 1)
        rpm = 60 / Hz
        inch_per_hour = wheel_circ_inches * rpm * 60
        mph = inch_per_hour / (12 * 5280)
        seconds_per_500m = (1 / mph) / 1600 * 500 * 3600

        return seconds_per_500m
        
    def calc_total_distance_m(self, num_rev):
        total_inches = wheel_circ_inches * num_rev
        total_meters = total_inches * 0.0254
        return total_meters

