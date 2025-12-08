from typing import Dict, List
from loguru import logger
from aimode.core.database import db, conn

# from database import db, conn
from functools import lru_cache
from apps.core.models import TestCaseModel
from apps.core.apis.serializers import TestcaseSearchSerializer


def get_active_projects(conn):
    query = """
        SELECT name
        FROM core.core_project
        WHERE is_active = TRUE
        ORDER BY name;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            projects = [r[0] for r in results]
            return projects
    except Exception as e:
        logger.error(f"Error fetching active projects: {e}")
        return []


def get_modules_by_project(conn, active_projects: list) -> Dict[str, list]:
    project_modules = {}
    query_template = """
        SELECT m.name
        FROM core.core_module AS m
        JOIN core.core_testcasemodel AS tcm ON m.id = tcm.module_id
        JOIN core.core_project AS p ON tcm.project_id = p.id
        WHERE p.name = %s
        GROUP BY m.name;
    """

    try:
        with conn.cursor() as cur:
            for project in active_projects:
                cur.execute(query_template, (project,))
                modules = [row[0] for row in cur.fetchall()]
                project_modules[project] = modules
    except Exception as e:
        logger.error(f"Error fetching modules for projects: {e}")

    return project_modules


def get_sql_table_names(conn):
    query = """
        SELECT schemaname || '.' || tablename AS tablename
        FROM pg_catalog.pg_tables
        WHERE schemaname='core';
    """
    logger.info(f"Connection type: {type(conn)}")
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            return results
    except Exception as e:
        logger.error(f"Error in executing the query: {e}")
        return None


def get_all_table_columns(conn) -> Dict[str, List[str]]:
    query = """
        SELECT
            c.table_schema || '.' || c.table_name AS table_name,
            array_agg(c.column_name ORDER BY c.ordinal_position) AS columns
        FROM
            information_schema.tables t
        JOIN
            information_schema.columns c
              ON t.table_name = c.table_name
             AND t.table_schema = c.table_schema
        WHERE
            t.table_schema = 'core'
            AND t.table_type   = 'BASE TABLE'
        GROUP BY
            c.table_schema, c.table_name;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    return {table: cols for table, cols in rows}


def get_id_module_mapping():
    try:
        rows = db.execute("SELECT DISTINCT cm.name, cm.id FROM core.core_module AS cm")
        return sorted([{"id": r[1], "name": r[0]} for r in rows], key=lambda x: x["id"])
    except Exception as e:
        logger.error(f"Error fetching module mapping: {e}")
        return []


def get_ids_by_module_names(module_names: list[str]) -> list[int]:
    mapping = {
        m["name"]: m["id"] for m in get_id_module_mapping() if isinstance(m, dict)
    }
    return [mapping.get(name) for name in module_names if name in mapping]


@lru_cache()
def get_testcases():
    logger.info(f"inside get_testcases")
    queryset = (
        TestCaseModel.objects.select_related("module")
        .prefetch_related("metrics")
        .only("id", "name", "priority", "module__name", "testcase_type")
    )
    serializer = TestcaseSearchSerializer(queryset, many=True)
    return {"testcases": serializer.data}
