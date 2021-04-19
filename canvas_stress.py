'''
Canvas stress
=============

This example tests the performance of our Graphics engine by drawing large
numbers of small squares. You should see a black canvas with buttons and a
label at the bottom. Pressing the buttons adds small colored squares to the
canvas.

'''
from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'systemanddock')
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


# Window.fullscreen = True

config = configparser.RawConfigParser()
config.read('props.properties')

class StressCanvasApp(App):

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
    def add_rects(cnn, self, label, wid, count, *largs):
        cur = cnn.cursor(buffered=True)
        t1 = Table('raw_data', schema='kivy_test_db')
        q = MySQLQuery.from_(t1).select(t1.distance_m)
        cur.execute(q.get_sql())
        res = cur.fetchone()
        val = res[0]

        label.text = str(val)

    @db_connector
    def double_rects(cnn, self, label, wid, *largs):
        cur = cnn.cursor(buffered=True)
        t1 = Table('raw_data', schema='kivy_test_db')
        q = MySQLQuery.from_(t1).select(t1.distance_m)
        cur.execute(q.get_sql())
        res = cur.fetchone()
        val = res[0]

        label.text = str(val)

    def reset_rects(self, label, wid, *largs):
        label.text = '0'
        wid.canvas.clear()

    def build(self):
        wid = Widget()

        label = Label(text='0')

        btn_add100 = Button(text='+ 100 rects',
                            on_press=partial(self.add_rects, label, wid, 100))

        btn_add500 = Button(text='+ 500 rects',
                            on_press=partial(self.add_rects, label, wid, 500))

        btn_reset = Button(text='Reset',
                           on_press=partial(self.reset_rects, label, wid))

        layout = BoxLayout(size_hint=(1, None), height=25)
        layout.add_widget(btn_add100)
        layout.add_widget(btn_add500)
        layout.add_widget(btn_reset)
        layout.add_widget(label)

        root = BoxLayout(orientation='vertical')
        root.add_widget(wid)
        root.add_widget(layout)

        return root


if __name__ == '__main__':
    StressCanvasApp().run()
