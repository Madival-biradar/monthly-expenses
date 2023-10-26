import os
import psycopg2
from psycopg2 import pool
import time
from dotenv import load_dotenv
load_dotenv()
# db_host = os.environ.get('POSTGRES_HOST')
# db_port = os.environ.get('POSTGRES_PORT', 5432)
# db_name = os.environ.get('POSTGRES_DATABASE')
# db_user = os.environ.get('POSTGRES_USER')
# db_password = os.environ.get('POSTGRES_PASSWORD')
pool_size_config = int(os.environ.get('max_pool_connection'))
pool_conn_timeout_config = int(os.environ.get('pool_connection_timeout'))


class PostgreSQLConnectionPool():
    def __init__(self, db_host, db_port, db_name, db_user, db_password, pool_size=pool_size_config,
                 connection_timeout=pool_conn_timeout_config):
        self._pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=pool_size,
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        self.connection_timeout = connection_timeout

    def get_connection(self):
        # return self._pool.getconn()
        start_time = time.time()
        while True:
            conn = self._pool.getconn()
            if time.time() - start_time > self.connection_timeout:
                raise TimeoutError("Connection timeout")
            if conn:
                return conn

    def put_connection(self, conn):
        self._pool.putconn(conn)

    def close_all_connections(self):
        self._pool.closeall()