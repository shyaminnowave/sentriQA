from string import Template
from typing import Dict, List
from loguru import logger
from aimode.core.database import db, conn
from langchain_core.prompts import ChatPromptTemplate


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
            c.table_schema || '.' || c.table_name AS table_name,   -- added schema prefix
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


def build_sql_generation_prompt(conn, user_query) -> str:
    table_names = get_sql_table_names(conn)
    table_descriptions = get_all_table_columns(conn)

    prompt = SQL_QUERY_GENERATION_BASE_PROMPT
    return Template(prompt).substitute(
        table_names=table_names,
        table_descriptions=table_descriptions,
        user_query=user_query
    )


table_columns = ", ".join(
    f"{col} = {dtype.strip('{}')}"
    for col, dtype in get_all_table_columns(conn).items()
)

table_names = ", ".join(name[0] for name in get_sql_table_names(conn))

module_names = db.execute("SELECT DISTINCT cm.name FROM core.core_module AS cm")
module_priorities = db.execute("SELECT DISTINCT ct.priority FROM core.core_testcasemodel AS ct")

AGENT_PROMPT_TEXT = f"""
You are a helpful assistant with access to three tools: `sql_query_generator`, `execute_sql_query`, and `generate_testplan`.

You have access to:
- Table names: {table_names}
- Table columns: {table_columns}

When the user asks to generate a **test plan** or **test case**:
1. **Never** create or execute a SQL query. Instead, use the `generate_testplan` tool.
2. A valid test plan requires these three parameters: `module_name`, `priority`, and `output_counts`.
3. If `module_name` is missing, suggest 3-4 options from: {module_names}.
    **Important:** These values must match **exactly** (case and format) when used for test case generation.
4. **Automatically detect the `priority` from the user query if it mentions classes like Class 1, Class 2, Class 3, or similar terms.**
    - Do not ask the user if the class is already mentioned in the query.
    - Map natural language mentions to exact system format: `Class 1 -> class_1`, `Class 2 -> class_2`, `Class 3 -> class_3` etc.
5. If `priority` is still missing, suggest 3-4 options from: {module_priorities}.
    **Important:** These values must match **exactly** (case and format) when used for test case generation.
6. If `output_counts` is missing, suggest one of [2, 4, 5, 10] (or let the user specify a custom value).
7. If multiple parameters are missing, ask them **one at a time**, without revealing future questions.
8. Automatically generate a `name` and `description` for the test plan.
9. When the user expresses intent to update, modify, or change the test case generation plan — for example by saying things like “Modify parameters or filters and continue,” “Change filters,” “Adjust,” “Yes modify,” “Yes change,” “Update,” “Refine,” “Yes” (after a suggestion) — follow this behavior:
    - Do not assume what the user wants to change. Do not automatically regenerate test cases or re-trigger any tool (including generate_testplan, execute_sql_query, or others). Only respond with explanations, clarifications, or next-step suggestions unless the user explicitly requests a tool execution.
    - Politely ask which parameter(s) they want to modify — for example:
    “Would you like to change the module, priority class, or number of test cases?”
    - Provide contextual suggestions for modules, priority classes, or number of test cases based on the last request.
    - Once the user clarifies, proceed to update only those specified parameters and regenerate the test plan accordingly.
    - If the user input is still unclear, ask again for clarification rather than making assumptions.
10. Under no circumstance should you call or re-trigger any tool (including `generate_testplan`, `execute_sql_query`, or others) when the user says "yes", "okay", "sure", or similar confirmations. 
    **without explicitly naming what they want to modify**.
    Always respond with a clarification question first.
"""

AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", AGENT_PROMPT_TEXT.strip()),
    ("placeholder", "{messages}"),
])


CHANGE_DETECTION_PROMPT_TEXT = f"""
You are an intelligent assistant that understands user queries for generating test plans.
You have access to the following system context:
{AGENT_PROMPT_TEXT}

Your task:
Compare two user queries and determine if the second one is **substantially different** from the first one.

Think based on their meaning, not just words — 
consider the user’s intent, focus, and purpose behind each query.

Return strictly one of these answers:
- "YES" → The second query represents a major change.
- "NO" → The second query is similar or a continuation/refinement.

Queries to compare:
Query 1 (previous): {{last_query}}
Query 2 (current): {{current_query}}
"""

CHANGE_DETECTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", CHANGE_DETECTION_PROMPT_TEXT)
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