from kivy.clock import Clock
from kivy.config import Config
from kivy.properties import NumericProperty, StringProperty

from db_connector import DbConnector

Config.set('kivy', 'keyboard_mode', 'systemanddock')
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.app import App
from pypika import MySQLQuery, Table, Field, Interval
from pypika import functions as fn
import configparser
import base64
import math
import datetime

config = configparser.RawConfigParser()
config.read('props.properties')


class LoginWindow(Screen):
    time = NumericProperty()

    def __init__(self, **kwargs):
        super(LoginWindow, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_spinner, 1)

    def update_spinner(self, interval):
        self.spinner_label.values = self.get_users()

    @DbConnector.db_connector
    def get_users(cnn, self) -> list:
        cur = cnn.cursor(buffered=True)
        users = Table('users', schema='kivy_test_db')
        q = MySQLQuery.from_(users).select(users.name)
        cur.execute(q.get_sql())
        users = cur.fetchall()

        return [x[0] for x in users]

    def check_password(self, user: str, passw: str) -> bool:
        if user == "Select from Dropdown":
            return False
        correct_password = DbConnector.get_password(self, user)
        provided_passw_encoded = base64.b64encode(passw.encode('ascii')).decode('ascii')
        return True if (provided_passw_encoded == correct_password) else False

class MainPage(Screen):
    insta_speed = NumericProperty()
    total_time = StringProperty()
    insta_min_per_500m = StringProperty()

    def __init__(self, **kwargs):
        super(MainPage, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_workout_data, 0.1)

    def reset_run(self):
        DbConnector.reset_raw_data(self)

    @DbConnector.db_connector
    def get_insta_data(cnn, self):
        cur = cnn.cursor(buffered=True)
        raw_data = Table('raw_data', schema='kivy_test_db')
        data_query = MySQLQuery.from_(raw_data).select(
            raw_data.timestamp
        ).where(
            raw_data.timestamp[fn.Now() - Interval(seconds=5):fn.Now()]
        )
        cur.execute(data_query.get_sql())
        res = cur.fetchall()
        return res

    @DbConnector.db_connector
    def get_all_workout_data(cnn, self):
        cur = cnn.cursor(buffered=True)
        raw_data = Table('raw_data', schema='kivy_test_db')
        data_query = MySQLQuery.from_(raw_data).select(
            raw_data.timestamp
        )
        cur.execute(data_query.get_sql())
        res = cur.fetchall()
        return res

    def update_workout_data(self, interval):
        all_data = sorted(self.get_all_workout_data())
        if (len(all_data) > 0):
            workout_seconds = (datetime.datetime.now() - all_data[0][0]).seconds
            hms = str(datetime.timedelta(seconds=workout_seconds))
            self.total_time = hms
        else:
            self.total_time = "0"
        self.total_time_label.text = self.total_time

        instantaneous_data = self.get_insta_data()
        num_data_points = len(instantaneous_data)
        if num_data_points > 1:
            time_delta = instantaneous_data[-1][0] - instantaneous_data[0][0]
            time_delta_numeric = time_delta.seconds + time_delta.microseconds / 1000000.0
            wheel_diameter = 27
            wheel_circ_inches = math.pi * wheel_diameter
            Hz = time_delta_numeric / (num_data_points - 1)
            rpm = 60 / Hz
            inch_per_hour = wheel_circ_inches * rpm * 60
            mph = inch_per_hour / (12 * 5280)
            seconds_per_500m = (1 / mph) / 1600 * 500 * 3600
            self.insta_min_per_500m = str(datetime.timedelta(seconds=seconds_per_500m)).split(".")[0]
            self.insta_speed = mph
            self.insta_speed_label.text = str(round(self.insta_speed, 2))
        else:
            self.insta_speed = 0.00

        self.insta_speed_label.text = str(round(self.insta_speed, 2))


class NewUser(Screen):

    @DbConnector.db_connector
    def save_user(cnn, self, user: str, passw: str) -> bool:
        cur = cnn.cursor(buffered=True)
        users = Table('users', schema='kivy_test_db')
        user_query = MySQLQuery.from_(users).select(
            users.star
        ).where(
            users.name == user
        )
        cur.execute(user_query.get_sql())
        res = cur.fetchall()
        if len(res) == 1:
            return False

        insert_query = MySQLQuery.into(users) \
            .columns('name', 'password') \
            .insert(user, self.string_to_base_64_string(passw))
        cur.execute(insert_query.get_sql())

        return True

    def string_to_base_64_string(self, string) -> str:
        return base64.b64encode(string.encode('ascii')).decode('ascii')

    def user_exists_error(self):
        self.user_exists_label.text = "User already exists"


class WindowManager(ScreenManager):
    pass


kv = Builder.load_file("my.kv")


class MyMainApp(App):

    def build(self):
        return kv


if __name__ == "__main__":
    MyMainApp().run()
