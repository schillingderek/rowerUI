import base64
import datetime
import math
import pytz


distance_multiplier = 1.0
wheel_diameter = 27
wheel_circ_inches = math.pi * wheel_diameter * distance_multiplier
tz = pytz.timezone('UTC')

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
        

    def calc_stroke_rate(self, all_data: list) -> float:
        previous_diff = 1000.0
        previous_time = datetime.datetime.strptime(all_data[0][0], '%Y-%m-%dT%H:%M:%S.%f+00:00').replace(tzinfo=pytz.UTC)
        stroke_count = 0
        accelerating = 0
        bounce_time_s = 0.25
        now_time = datetime.datetime.now(tz)
        min_time = now_time
        last_change_time = now_time - datetime.timedelta(seconds=15)
        for i, point in enumerate(all_data):
            point_time = datetime.datetime.strptime(point[0], '%Y-%m-%dT%H:%M:%S.%f+00:00').replace(tzinfo=pytz.UTC)
            # Only consider the last 15 seconds when calculating average SPM
            if (now_time - point_time).seconds > 15:
                continue
            # Can't do anything with just the first data point
            if i == 0:
                continue
            # If there are no strokes yet
            if stroke_count == 0:
                min_time = point_time
            
            time_delta = point_time - previous_time
            current_diff = time_delta.seconds + time_delta.microseconds / 1000000.0
            time_since_last_change = (now_time - last_change_time).seconds + (now_time - last_change_time).microseconds / 1000000.0
            if current_diff < previous_diff and time_since_last_change > bounce_time_s:
                if not accelerating:
                    stroke_count += 1
                    last_change_time = now_time
                accelerating = 1
            
            previous_diff = current_diff
        total_time = now_time - min_time
        total_time_m = (total_time.seconds + total_time.microseconds / 1000000.0) / 60.0
        if (total_time_m > 0.0):
            spm = stroke_count / total_time_m
            print(stroke_count)
