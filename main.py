from kivy.clock import Clock
from kivy.config import Config
from kivy.properties import NumericProperty
from db_connector import DbConnector
Config.set('kivy', 'keyboard_mode', 'systemanddock')
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.app import App
from pypika import MySQLQuery, Table, Field
import configparser
import base64

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

    @DbConnector.db_connector
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
        return True if (provided_passw_encoded == res) else False


class MainPage(Screen):
    time = NumericProperty()

    def __init__(self, **kwargs):
        super(MainPage, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_stats, 0.1)

    def update_stats(self, interval):
        self.time += 0.1
        self.counter_label.text = str(round(self.time))


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

    def do_login(self, passw: str) -> str:
        return "second" if passw == "hello" else "main"


if __name__ == "__main__":
    MyMainApp().run()
