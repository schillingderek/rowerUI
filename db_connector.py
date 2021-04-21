import mysql.connector as mysql
from kivy.config import Config
from pypika import functions as fn

from utils import Utils

Config.set('kivy', 'keyboard_mode', 'systemanddock')
from pypika import MySQLQuery, Table, Field, Interval
import configparser

config = configparser.RawConfigParser()
config.read('props.properties')

db_name = 'kivy_test_db'
users_table = Table('users', schema=db_name)
raw_data_table = Table('raw_data', schema=db_name)


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
        q = MySQLQuery.from_(users_table).select(
            users_table.password
        ).where(
            users_table.name == user
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
        q = MySQLQuery.from_(raw_data_table).delete()
        cur.execute(q.get_sql())

    @db_connector
    def get_insta_data(cnn, self):
        cur = cnn.cursor(buffered=True)
        data_query = MySQLQuery.from_(raw_data_table).select(
            raw_data_table.timestamp
        ).where(
            raw_data_table.timestamp[fn.Now() - Interval(seconds=5):fn.Now()]
        )
        cur.execute(data_query.get_sql())
        res = cur.fetchall()
        return res

    @db_connector
    def get_all_workout_data(cnn, self):
        cur = cnn.cursor(buffered=True)
        data_query = MySQLQuery.from_(raw_data_table).select(
            raw_data_table.timestamp
        )
        cur.execute(data_query.get_sql())
        res = cur.fetchall()
        return res

    @db_connector
    def user_exists(cnn, self, user: str) -> bool:
        cur = cnn.cursor(buffered=True)
        user_query = MySQLQuery.from_(users_table).select(
            users_table.star
        ).where(
            users_table.name == user
        )
        cur.execute(user_query.get_sql())
        res = cur.fetchall()
        if len(res) > 0:
            return True

        return False

    @db_connector
    def insert_user(cnn, self, user: str, passw: str) -> bool:
        cur = cnn.cursor(buffered=True)
        insert_query = MySQLQuery.into(users_table) \
            .columns('name', 'password') \
            .insert(user, Utils.string_to_base_64_string(self, passw))
        cur.execute(insert_query.get_sql())

        return True

    @db_connector
    def get_users(cnn, self) -> list:
        cur = cnn.cursor(buffered=True)
        q = MySQLQuery.from_(users_table).select(users_table.name)
        cur.execute(q.get_sql())
        users = cur.fetchall()

        return [x[0] for x in users]
