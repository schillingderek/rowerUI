from kivy.config import Config
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty

Config.set('kivy', 'keyboard_mode', 'systemanddock')

from kivy.core.window import Window
Window.fullscreen = True

from kivy.clock import Clock
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.app import App

from db_connector import DbConnector
from utils import Utils
import datetime
import pytz
import math


class LoginWindow(Screen):
    time = NumericProperty()
    selected_distance = "0"
    selected_user = StringProperty()

    def __init__(self, **kwargs):
        super(LoginWindow, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_spinner, 1)

    def update_spinner(self, _):
        self.spinner_label.values = self.get_users()

    def get_users(self) -> list:
        return DbConnector.get_users(self)

    def update_distance_select(self, user: str, distance: str):
        self.selected_distance = distance
        self.selected_user = user
        if self.selected_distance.isnumeric() and int(self.selected_distance) > 0:
            self.go_distance_button.disabled = False
        else:
            self.selected_distance = "0"
            self.go_distance_button.disabled = True

    def check_password(self, user: str, passw: str) -> bool:
        if user == "Select from Dropdown":
            return False
        correct_password = DbConnector.get_password(self, user)
        provided_passw_encoded = Utils.string_to_base_64_string(self, passw)
        return True if (provided_passw_encoded == correct_password) else False


class CustomPopup(Popup):
    def changeText(self, *args):
        self.ids.popup_label.text = args[0][0]


def best_run_popup(self, current_run_s, previous_best_time_s, target_distance):
    minutes = math.floor(current_run_s / 60.0)
    seconds = math.floor(current_run_s - 60 * minutes)
    hundredths = round(current_run_s - 60 * minutes - seconds, 2)
    time_string = str(minutes) + " minutes " + str(seconds + hundredths) + " seconds"

    if current_run_s < previous_best_time_s:
        text = "New best time @ " + str(
            round(target_distance)) + "m\n" + time_string
    else:
        text = "Run Complete @ " + str(
            round(target_distance)) + "m\n" + time_string
    App.get_running_app().root.popup.changeText([text])
    App.get_running_app().root.popup.open()


class MainPage(Screen):
    total_time = StringProperty()
    insta_time_per_500m = StringProperty()
    total_distance_m = NumericProperty()
    spm = NumericProperty()
    avg_time_per_500m = NumericProperty()
    run_saved = BooleanProperty(defaultvalue=False)
    best_run = []

    def __init__(self, **kwargs):
        super(MainPage, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_workout_data, 0.5)

    def reset_run(self):
        print("resetting data")
        DbConnector.reset_raw_data(self)
        self.run_saved = False
        self.total_distance_bar.value = 0.00
        self.avg_time_per_500m_label.text = "0:00:00"
        self.best_run_bar.value = 0.00
        self.insta_spm_label.text = "0.00"
        self.total_distance_m_label.text = "0"

    def update_workout_data(self, _):
        selected_distance = App.get_running_app().root.screens[0].selected_distance
        selected_user = App.get_running_app().root.screens[0].selected_user
        if selected_distance == "0":
            self.main_screen_carousel_index.index = 1
        else:
            self.main_screen_carousel_index.index = 0
        target_distance = float(selected_distance)
        all_data = sorted(DbConnector.get_all_raw_data(self))
        if len(all_data) > 0:
            tz = pytz.timezone('UTC')
            workout_start = datetime.datetime.strptime(all_data[0][0], '%Y-%m-%dT%H:%M:%S.%f+00:00').replace(
                tzinfo=pytz.UTC)
            workout_seconds = (datetime.datetime.now(tz) - workout_start).seconds
            h_m_s = str(datetime.timedelta(seconds=workout_seconds))
            self.total_time = h_m_s
            self.total_distance_m = Utils.calc_total_distance_m(self, len(all_data))

            if not target_distance == 0:
                self.best_run_label.text = "Best Run to " + str(round(target_distance)) + "m"

            closest_point_meters = 0
            if workout_seconds > 0 and not target_distance == 0 and not selected_user == "" and not selected_user == "Select from Dropdown":
                self.best_run = DbConnector.get_user_runs_at_distance(self, target_distance, selected_user, 1)
                if self.best_run:
                    best_run_id = self.best_run[0][0]
                    closest_point = DbConnector.get_closest_point(self, best_run_id, workout_seconds)
                    closest_point_meters = closest_point[2]

            if self.total_distance_m >= target_distance and not self.run_saved and not target_distance == 0 and not selected_user == "" and not selected_user == "Select from Dropdown":
                self.run_saved = True
                best_run_popup(workout_seconds, self.best_run[0][1], target_distance)
                DbConnector.save_user_run(self, target_distance, selected_user, all_data)

            self.total_distance_bar.value = target_distance if self.total_distance_m >= target_distance else self.total_distance_m / target_distance
            self.best_run_bar.value = target_distance if closest_point_meters >= target_distance else closest_point_meters / target_distance

            self.spm = round(Utils.calc_stroke_rate(self, all_data) or 0.00, 2)
            self.insta_spm_label.text = str(self.spm)

            self.avg_time_per_500m = workout_seconds / self.total_distance_m * 500
            self.avg_time_per_500m_label.text = str(datetime.timedelta(seconds=self.avg_time_per_500m)).split(".")[0]
        else:
            self.total_time = "0:00:00"
            self.total_distance_m = 0
        self.total_time_label.text = self.total_time
        self.progress_bar_label.text = "Current run to " + str(round(target_distance)) + "m\nTotal Distance: " + str(
            round(self.total_distance_m)) + "m"
        self.total_distance_m_label.text = str(round(self.total_distance_m, 0))

        instantaneous_data = DbConnector.get_insta_data(self)
        if len(instantaneous_data) > 1:
            seconds_per_500m = Utils.calc_insta_values(self, instantaneous_data)
            self.insta_time_per_500m = str(datetime.timedelta(seconds=seconds_per_500m)).split(".")[0]
        else:
            self.insta_time_per_500m = "0:00:00"

        self.insta_time_per_500m_label.text = self.insta_time_per_500m


class NewUser(Screen):

    def save_user(self, user: str, passw: str) -> bool:
        if DbConnector.user_exists(self, user):
            return False

        return DbConnector.insert_user(self, user, passw)

    def user_exists_error(self):
        self.user_exists_label.text = "User already exists"


class WindowManager(ScreenManager):
    popup = ObjectProperty()

    def __init__(self, **kwargs):
        super(WindowManager, self).__init__(**kwargs)
        self.popup = CustomPopup()


kv = Builder.load_file("my.kv")


class MyMainApp(App):

    def build(self):
        return kv


if __name__ == "__main__":
    MyMainApp().run()
