from string import Template
from typing import Dict, List
from loguru import logger
from aimode.core.database import db, conn
from langchain_core.prompts import ChatPromptTemplate


def get_sql_table_names(conn):
    query = """
        SELECT tablename
        FROM pg_catalog.pg_tables
        WHERE schemaname='public';
    """
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
            c.table_name,
            array_agg(c.column_name ORDER BY c.ordinal_position) AS columns
        FROM
            information_schema.tables t
        JOIN
            information_schema.columns c
              ON t.table_name = c.table_name
             AND t.table_schema = c.table_schema
        WHERE
            t.table_schema = 'public'
            AND t.table_type   = 'BASE TABLE'
        GROUP BY
            c.table_name;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        # Returns List[(table_name, [col1, col2, …]), …]
        rows = cur.fetchall()

    # Convert to dict: { 'table1': ['colA','colB'], … }
    return {table: cols for table, cols in rows}



SQL_QUERY_GENERATION_BASE_PROMPT = """You are an expert who can create efficient SQL Query. 
            IMPORTANT: You must ONLY use the tables and columns listed below. Do not assume or guess table names.
            
            Available SQL Tables:
            $table_names
            
            ---------
            SQL table descriptions (including all available columns):
            $table_descriptions

            --------
            Now create a SQL query based on the user question:
            $user_query

            Important Notes: 
            1. Only provide the SQL Query, do not provide other texts
            2. ONLY use tables and columns that are listed above
            3. If you need to query about sellers, look for a table that might contain seller information
            4. If you're unsure about which table to use, ask for clarification
    """

def build_sql_generation_prompt(conn,user_query) -> str:
    """Builds a SQL Query generation prompt by injecting database tables and their descriptions into a template.

    Args:
        conn: Database Connection Object.
    Returns:
        A string containing the formatted SQL Query generation prompt.
    """

    table_names=get_sql_table_names(conn)
    table_descriptions=get_all_table_columns(conn)

    prompt=SQL_QUERY_GENERATION_BASE_PROMPT
    return Template(prompt).substitute(table_names=table_names, table_descriptions=table_descriptions, user_query=user_query)




table_columns = ", ".join(
    f"{col} = {dtype.strip('{}')}"
    for col, dtype in get_all_table_columns(conn).items()
)

table_names = ", ".join(name[0] for name in get_sql_table_names(conn))

module_names = db.execute("SELECT DISTINCT cm.name FROM core_module AS cm")
module_priorities = db.execute("SELECT DISTINCT ct.priority FROM core_testcasemodel AS ct")

AGENT_PROMPT_TEXT = f"""
You are a helpful assistant with access to three tools: `sql_query_generator`, `execute_sql_query` and `generate_testplan`.

You have access to:
- Table names: {table_names}
- Table columns: {table_columns}

When the user asks to generate a **test plan** or **test case**:
1. **Never** create or execute a SQL query. Instead, use the `generate_testplan` tool.
2. A valid test plan requires these three parameters: `module_name`, `priority`, and `output_counts`.
3. If `module_name` is missing, suggest 3-4 options from: {module_names}.
    **Important:** These values must match **exactly** (case and format) when used for test case generation.
4. If `priority` is missing, suggest 3-4 options from: {module_priorities}.
    **Important:** These values must match **exactly** (case and format) when used for test case generation.
5. If `output_counts` is missing, suggest one of [2, 4, 5, 10] (or let the user specify a custom value).
6. If multiple parameters are missing, ask them **one at a time**, without revealing future questions.
7. Automatically generate a `name` and `description` for the test plan.
"""

AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", AGENT_PROMPT_TEXT.strip()),
    ("placeholder", "{messages}"),
])


SUGGESTION_LLM_PROMPT_TEXT = """\
You are an expert in Structuring Data. \
Given an LLM response, extract and structure the information as follows:
1. Extract the main content as 'base_content'
2. Identify any suggestions, options, or recommendations as a list in 'suggestions'
Don't make up information, use only existing info from the input. \
Required fields are case sensitive.
"""

SUGGESTION_LLM_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SUGGESTION_LLM_PROMPT_TEXT),
        ("human", "Structure the following LLM response:\n\n{content}"),
    ]
)