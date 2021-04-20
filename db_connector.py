import mysql.connector as mysql
import configparser

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