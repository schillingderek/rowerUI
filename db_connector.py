import mysql.connector as mysql
import configparser
from kivy.clock import Clock
from kivy.config import Config

Config.set('kivy', 'keyboard_mode', 'systemanddock')
from pypika import MySQLQuery, Table, Field, Interval
import configparser
import base64

config = configparser.RawConfigParser()
config.read('props.properties')


class DbConnector:

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
    def get_password(cnn, self, user: str) -> (str, None):
        cur = cnn.cursor(buffered=True)
        users = Table('users', schema='kivy_test_db')
        q = MySQLQuery.from_(users).select(
            users.password
        ).where(
            users.name == user
        )
        cur.execute(q.get_sql())
        password = cur.fetchone()
        if len(password) > 0:
            return password[0]
        else:
            return None

    @db_connector
    def reset_raw_data(cnn, self):
        cur = cnn.cursor(buffered=True)
        raw_data = Table('raw_data', schema='kivy_test_db')
        q = MySQLQuery.from_(raw_data).delete()
        cur.execute(q.get_sql())
