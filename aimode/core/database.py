import os
import psycopg2
from psycopg2 import OperationalError, InterfaceError
from loguru import logger
from dotenv import load_dotenv

load_dotenv()


class SQLDatabaseConnection:
    """
    Robust PostgreSQL connection manager.
    Keeps one active connection alive and automatically reconnects if idle, broken, or closed.
    """
    _instance = None
    _pg_conn = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SQLDatabaseConnection, cls).__new__(cls)
        return cls._instance

    def _get_db_credentials(self, user: str):
        if user == "llm_user":
            return (
                os.getenv("PGSQL_DATABASE_LLM_USER"),
                os.getenv("PGSQL_DATABASE_LLM_PASS"),
            )
        return (
            os.getenv("PGSQL_DATABASE_USER"),
            os.getenv("PGSQL_DATABASE_PASS"),
        )

    def connect_postgresql(self, user: str = "default"):
        """
        Establish or reuse a PostgreSQL connection. Reconnect automatically if the existing one is invalid.
        """
        if self._pg_conn and not self._pg_conn.closed:
            return self._pg_conn

        db_user, db_pass = self._get_db_credentials(user)
        try:
            self._pg_conn = psycopg2.connect(
                host=os.getenv("PGSQL_DATABASE_HOST"),
                database=os.getenv("PGSQL_DATABASE_NAME"),
                user=db_user,
                password=db_pass,
                port=os.getenv("PGSQL_DATABASE_PORT"),
                connect_timeout=10, 
            )
            self._pg_conn.autocommit = True
            logger.success("PostgreSQL connection established.")
            return self._pg_conn
        except OperationalError as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected PostgreSQL connection error: {e}")
            raise

    def ensure_connection_alive(self):
        try:
            if not self._pg_conn or self._pg_conn.closed:
                logger.warning("PostgreSQL connection was closed. Reconnecting...")
                return self.connect_postgresql()

            with self._pg_conn.cursor() as cur:
                cur.execute("SELECT 1;") 
            return self._pg_conn

        except (InterfaceError, OperationalError):
            logger.warning("Lost PostgreSQL connection. Reinitializing...")
            return self.connect_postgresql()
        except Exception as e:
            logger.error(f"Unexpected DB error during health check: {e}")
            return self.connect_postgresql()

    def execute(self, query: str):
        self._pg_conn = self.ensure_connection_alive()
        try:
            with self._pg_conn.cursor() as cur:
                cur.execute(query)
                if cur.description:
                    results = cur.fetchall()
                    if len(cur.description) == 1:
                        return [row[0] for row in results]
                    return results
                return []
        except (InterfaceError, OperationalError):
            logger.warning("Lost connection during query execution. Reconnecting and retrying...")
            self._pg_conn = self.connect_postgresql()
            try:
                with self._pg_conn.cursor() as cur:
                    cur.execute(query)
                    if cur.description:
                        results = cur.fetchall()
                        if len(cur.description) == 1:
                            return [row[0] for row in results]
                        return results
                    return []
            except Exception as e:
                logger.error(f"Query failed even after reconnect: {e}\nQuery: {query}")
                return []
        except Exception as e:
            logger.error(f"Unexpected SQL error: {e}\nQuery: {query}")
            return []

    def close_connections(self):
        if self._pg_conn and not self._pg_conn.closed:
            self._pg_conn.close()
            logger.info("PostgreSQL connection closed cleanly.")

db = SQLDatabaseConnection()
conn = db.connect_postgresql()
