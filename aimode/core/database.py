import os
import psycopg2
from psycopg2 import OperationalError
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

class SQLDatabaseConnection:
    """
    Singleton-style PostgreSQL connection manager.
    Ensures only one active connection is maintained and reused.
    """
    _instance = None
    _pg_conn = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SQLDatabaseConnection, cls).__new__(cls)
        return cls._instance

    def connect_postgresql(self, user: str = "default"):
        """
        Establishes or reuses a connection to PostgreSQL.
        """
        if self._pg_conn and not self._pg_conn.closed:
            return self._pg_conn  # Reuse existing connection

        if user == "llm_user":
            db_user = os.getenv("PGSQL_DATABASE_LLM_USER")
            password = os.getenv("PGSQL_DATABASE_LLM_PASS")
        else:
            db_user = os.getenv("PGSQL_DATABASE_USER")
            password = os.getenv("PGSQL_DATABASE_PASS")

        try:
            self._pg_conn = psycopg2.connect(
                host=os.getenv("PGSQL_DATABASE_HOST"),
                database=os.getenv("PGSQL_DATABASE_NAME"),
                user=db_user,
                password=password,
                port=os.getenv("PGSQL_DATABASE_PORT"),
                sslmode=os.getenv("PGSQL_DATABASE_SSLMODE"),
            )
            logger.success("PostgreSQL Connected")
            return self._pg_conn
        except OperationalError as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def execute(self, query: str):
        """
        Executes a SQL query on the connected database.
        Returns a flat list of results.
        """
        if not self._pg_conn or self._pg_conn.closed:
            self.connect_postgresql()  # Auto-reconnect if needed

        with self._pg_conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
        return [row[0] for row in results]

    def close_connections(self):
        """
        Closes the PostgreSQL connection.
        """
        if self._pg_conn and not self._pg_conn.closed:
            self._pg_conn.close()
            logger.info("PostgreSQL connection closed")


# Single global instance
db = SQLDatabaseConnection()
conn = db.connect_postgresql()