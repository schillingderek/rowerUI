import sqlite3
from pypika import MySQLQuery, Table, Parameter
from utils import Utils
import datetime
import pytz
import os

db_location = os.getcwd() + "/rower.db"
db_name = db_location
users_table = Table('users')
raw_data_table = Table('raw_data')
runs_table = Table('runs')
run_data_table = Table('run_data')

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

    @db_connector
    def save_user_run(cnn, self, target_distance, user_name, all_data):
        user_id = DbConnector.get_user_id(self, user_name)
        cur = cnn.cursor()
        insert_query = MySQLQuery.into(runs_table).columns(
            'user_id', 'target_distance_m', 'start_time', 'end_time'
        ).insert(
            [user_id, int(target_distance), all_data[0][0], all_data[-1][0]]
        )
        cur.execute(insert_query.get_sql())
        cnn.commit()
        run_id = cur.lastrowid

        insert_query2 = MySQLQuery.into(run_data_table).columns(
            'run_id', 'distance_m', 'elapsed_time_s'
        ).insert(
            [Parameter('?'), Parameter('?'), Parameter('?')]
        )
        start_time = datetime.datetime.strptime(all_data[0][0], '%Y-%m-%dT%H:%M:%S.%f+00:00').replace(
                tzinfo=pytz.UTC)
        for i, row in enumerate(all_data):
            data_point_time = datetime.datetime.strptime(row[0], '%Y-%m-%dT%H:%M:%S.%f+00:00').replace(
                tzinfo=pytz.UTC)
            time_diff = data_point_time - start_time
            elapsed_time_s = time_diff.seconds + time_diff.microseconds / 1000000.0
            params = [run_id, Utils.calc_total_distance_m(self, i), elapsed_time_s]
            q = insert_query2.get_sql()
            cur.execute(q, params)

    @db_connector
    def get_best_user_run(cnn, self, target_distance, user_name):
        user_id = DbConnector.get_user_id(self, user_name)
        cur = cnn.cursor()
        q = """SELECT id, round((julianday(end_time) - julianday(start_time))*86400.0, 2) as elapsed_seconds
        FROM runs
        WHERE user_id = %d AND target_distance_m = %d
        AND start_time IS NOT NULL
        ORDER BY elapsed_seconds ASC
        """

        query = q % (user_id[0], target_distance)
        cur.execute(query)
        best_run = cur.fetchone()
        print(best_run)

    @db_connector
    def get_user_runs_at_distance(cnn, self, target_distance, user_name, limit=999999):
        user_id = DbConnector.get_user_id(self, user_name)
        cur = cnn.cursor()
        q = """SELECT id, round((julianday(end_time) - julianday(start_time))*86400.0, 2) as elapsed_seconds
        FROM runs
        WHERE user_id = %d AND target_distance_m = %d
        AND start_time IS NOT NULL
        ORDER BY elapsed_seconds ASC
        LIMIT %d
        """

        query = q % (user_id[0], target_distance, limit)
        cur.execute(query)
        runs = cur.fetchall()
        return runs

    @db_connector
    def get_user_id(cnn, self, user_name):
        cur = cnn.cursor()
        q = MySQLQuery.from_(users_table).select(users_table.id).where(
            users_table.name == user_name
        )
        cur.execute(q.get_sql())
        user_id = cur.fetchone()

        return user_id

    @db_connector
    def get_closest_point(cnn, self, best_run_id, workout_seconds):
        cur = cnn.cursor()
        q = """SELECT * FROM run_data WHERE run_id = %d ORDER BY ABS(elapsed_time_s - %f) ASC LIMIT 1;"""
        query = q % (best_run_id, workout_seconds)
        cur.execute(query)
        return cur.fetchone()
