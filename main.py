from kivy.config import Config

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


config = configparser.RawConfigParser()
config.read('props.properties')

class MainWindow(Screen):
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
    def get_users(cnn):
        cur = cnn.cursor(buffered=True)
        users = Table('users', schema='kivy_test_db')
        q = MySQLQuery.from_(users).select(users.name)
        cur.execute(q.get_sql())
        res = cur.fetchall()

        return res

    @db_connector
    def check_password(cnn, self, user, passw):
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

    users = get_users()
    users_formatted = [x[0] for x in users]


class SecondWindow(Screen):
    pass

class ThirdWindow(Screen):
    pass


class WindowManager(ScreenManager):
    pass

kv = Builder.load_file("my.kv")


class MyMainApp(App):
    LabelBase.register(name='Retro',
                       fn_regular='fonts/retro_computer_personal_use.ttf')

    def build(self):
        return kv

    def do_login(self, passw):
        return "second" if passw == "hello" else "main"

if __name__ == "__main__":
    MyMainApp().run()
