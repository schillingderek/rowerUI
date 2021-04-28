import sqlite3
from pypika import functions as fn
from pypika import MySQLQuery, Table, Field, Interval
from utils import Utils
import configparser
import datetime
import pytz

db_name = '/home/pi/rowerUI/rower.db'
users_table = Table('users')
raw_data_table = Table('raw_data')


class DbConnector:

    def db_connector(self):
        def with_connection_(*args, **kwargs):
            cnn = sqlite3.connect(db_name)
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
        cur = cnn.cursor()
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
        cur = cnn.cursor()
        q = MySQLQuery.from_(raw_data_table).delete()
        cur.execute(q.get_sql())

    @db_connector
    def get_insta_data(cnn, self):
        cur = cnn.cursor()
        data_query = MySQLQuery.from_(raw_data_table).select(
            raw_data_table.timestamp
        )
        
        raw_query = data_query.get_sql() + " WHERE strftime('%s', 'now') - cast(strftime('%s', timestamp) as integer) < 4"
        cur.execute(raw_query)
        res = cur.fetchall()
        return res

    @db_connector
    def get_all_raw_data(cnn, self):
        cur = cnn.cursor()
        data_query = MySQLQuery.from_(raw_data_table).select(
            raw_data_table.timestamp
        )
        cur.execute(data_query.get_sql())
        res = cur.fetchall()
        return res

    @db_connector
    def user_exists(cnn, self, user: str) -> bool:
        cur = cnn.cursor()
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
        cur = cnn.cursor()
        insert_query = MySQLQuery.into(users_table) \
            .columns('name', 'password') \
            .insert(user, Utils.string_to_base_64_string(self, passw))
        cur.execute(insert_query.get_sql())

        return True

    @db_connector
    def get_users(cnn, self) -> list:
        cur = cnn.cursor()
        q = MySQLQuery.from_(users_table).select(users_table.name)
        cur.execute(q.get_sql())
        users = cur.fetchall()

        return [x[0] for x in users]
        
    @db_connector
    def record_wheel_rotation(cnn, self) -> bool:
        cur = cnn.cursor()
        tz = pytz.timezone('UTC')
        insert_query = MySQLQuery.into(raw_data_table) \
            .columns('timestamp') \
            .insert(datetime.datetime.now(tz))
        cur.execute(insert_query.get_sql())
        
        return True
