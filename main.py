from kivy.clock import Clock
from kivy.config import Config
from kivy.properties import NumericProperty

Config.set('kivy', 'keyboard_mode', 'systemanddock')
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from functools import partial
import mysql.connector as mysql
from kivy.core.window import Window
from pypika import MySQLQuery, Table, Field
import configparser
import base64
from kivy.core.text import LabelBase
from math import ceil

config = configparser.RawConfigParser()
config.read('props.properties')


class MainWindow(Screen):
    time = NumericProperty()

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_spinner, 1)

    def update_spinner(self, interval):
        self.spinner_label.values = self.get_users()
        self.spinner_label.text = self.get_users()[0]

    def db_connector(self):
        def with_connection_(*args, **kwargs):
            host = config.get('DatabaseSection', 'database.host')
            user = config.get('DatabaseSection', 'database.user')
            password = config.get('DatabaseSection', 'database.password')
            auth = config.get('DatabaseSection', 'database.authPlugin')

            cnn = mysql.connect(host=host, user=user, passwd=password,
                                auth_plugin=auth)
            try:
                rv = self(cnn, *args, **kwargs)
            except Exception:
                cnn.rollback()
                raise
            else:
                cnn.commit()
            finally:
                cnn.close()
            return rv

        return with_connection_

    @db_connector
    def get_users(cnn, self) -> list:
        cur = cnn.cursor(buffered=True)
        users = Table('users', schema='kivy_test_db')
        q = MySQLQuery.from_(users).select(users.name)
        cur.execute(q.get_sql())
        users = cur.fetchall()

        return [x[0] for x in users]


    @db_connector
    def check_password(cnn, self, user: str, passw: str) -> str:
        cur = cnn.cursor(buffered=True)
        users = Table('users', schema='kivy_test_db')
        q = MySQLQuery.from_(users).select(
            users.password
        ).where(
            users.name == user
        )
        cur.execute(q.get_sql())
        res = cur.fetchone()[0]
        provided_passw_encoded = base64.b64encode(passw.encode('ascii')).decode('ascii')
        return "second" if (provided_passw_encoded == res) else "main"


class SecondWindow(Screen):

    time = NumericProperty()

    def __init__(self, **kwargs):
        super(SecondWindow, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_stats, 0.1)


    def update_stats(self, interval):
        self.time += 0.1
        self.counter_label.text = str(round(self.time))


class ThirdWindow(Screen):
    def db_connector(self):
        def with_connection_(*args, **kwargs):
            host = config.get('DatabaseSection', 'database.host')
            user = config.get('DatabaseSection', 'database.user')
            password = config.get('DatabaseSection', 'database.password')
            auth = config.get('DatabaseSection', 'database.authPlugin')

            cnn = mysql.connect(host=host, user=user, passwd=password,
                                auth_plugin=auth)
            try:
                rv = self(cnn, *args, **kwargs)
            except Exception:
                cnn.rollback()
                raise
            else:
                cnn.commit()
            finally:
                cnn.close()
            return rv

        return with_connection_

    @db_connector
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

    def do_login(self, passw: str) -> str:
        return "second" if passw == "hello" else "main"


if __name__ == "__main__":
    MyMainApp().run()
