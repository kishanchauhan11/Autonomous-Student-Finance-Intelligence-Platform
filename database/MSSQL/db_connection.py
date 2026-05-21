import os
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("DBConnection")

# Read database connection parameters from environment variables
DB_SERVER = os.getenv("DB_SERVER", "")
DB_DATABASE = os.getenv("DB_DATABASE", "StudentFinanceDB")
DB_USERNAME = os.getenv("DB_USERNAME", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

USE_MSSQL = False
conn = None

if DB_SERVER:
    try:
        import pyodbc
        connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_DATABASE};"
            f"UID={DB_USERNAME};"
            f"PWD={DB_PASSWORD};"
            "Connection Timeout=5;"
        )
        conn = pyodbc.connect(connection_string, autocommit=True)
        USE_MSSQL = True
        logger.info("Successfully connected to MSSQL Server.")
    except Exception as e:
        logger.warning(f"MSSQL connection failed: {e}. Falling back to DatabaseMock.")
else:
    logger.info("No MSSQL configuration found. Using default DatabaseMock fallback.")


class DBConnection:
    @staticmethod
    def is_mssql_active() -> bool:
        return USE_MSSQL

    @staticmethod
    def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Executes a SELECT query on MSSQL and returns dictionary rows.
        """
        if not USE_MSSQL or not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"SQL SELECT Error: {e}")
            return []

    @staticmethod
    def execute_non_query(query: str, params: tuple = ()) -> bool:
        """
        Executes an INSERT, UPDATE, or DELETE statement on MSSQL.
        """
        if not USE_MSSQL or not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"SQL Execution Error: {e}")
            return False
