from string import Template
import json
from typing import Dict, List
from loguru import logger
from aimode.core.database import db, conn
from aimode.core.helpers import get_active_projects, get_modules_by_project, get_sql_table_names, get_all_table_columns
from langchain_core.prompts import ChatPromptTemplate

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
active_projects = get_active_projects(conn)
logger.info(f"Active Projects :{active_projects}")
modules_by_project = get_modules_by_project(conn, active_projects)
logger.info(f"Modules by project: {modules_by_project}")
moduleProjects = json.dumps(modules_by_project, indent=2)
moduleProjects_escaped = moduleProjects.replace("{", "{{").replace("}", "}}")

module_names = db.execute("SELECT DISTINCT cm.name FROM core.core_module AS cm")
module_priorities = db.execute("SELECT DISTINCT ct.priority FROM core.core_testcasemodel AS ct")
logger.info(f"module priorities : {module_priorities}")

AGENT_PROMPT_TEXT = f"""
You are a helpful assistant with access to four tools: `sql_query_generator`, `execute_sql_query`, `generate_testplan` and 'save_new_testplan_version'.

You have access to:
- Table names: {table_names}
- Table columns: {table_columns}
- Active projects: {active_projects}
- Modules by projects: {moduleProjects_escaped}

*Test Plan Generation*
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
9. Analyze the number of testcases generated with the expected output count.
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
You are a Test Plan Structuring Assistant. Your goal is to structure responses **strictly using the given context**.

Context (use ONLY these):
- Active projects: {{active_projects}}
- Modules by projects (use ONLY these module names, no others): {{moduleProjects_escaped}}
- Available priority classes: {{module_priorities}}

Task:
Given an LLM response, extract and structure the information as follows:
1. Extract the main summary as 'base_content' (shortened or cleaned if needed).
2. Identify possible next actions, options, or recommendations as a list under 'suggestions'.

Guidelines:
1. 'base_content' must reflect the key intent of the LLM response, summarized clearly.
2. 'suggestions' must be realistic and actionable — **never invent module or class names**.
3. Never suggest anything if the test plan was successfully generated with expected output count and
   The total number of test cases meets or exceeds the requested output_count,
   leave 'suggestions' as an empty list [].  

Always ensure all suggestions strictly use:
   - Module names from {{moduleProjects_escaped}} only.
   - Priority classes from {{module_priorities}} only.
   - No other identifiers, words, or numbering variations (e.g., never "class_4" or "high_priority" if not listed).

**Important – When to Suggest**
a. When fewer test cases are generated than requested or none were found:
   - Identify any missing priority class(es) from the user’s query. If there are priority classes (from {{module_priorities}}) that were not mentioned, 
      suggest regenerating the same test plan including those missing class(es) also. Otherwise, do not suggest regenerating the same plan.
   - Map priority classes consistently as "Class 1" -> class_1, "Class 2" -> class_2, and "Class 3" -> class_3
   - Suggest 1–2 *distinct, complete queries* adding different module and class strictly from {{moduleProjects_escaped}} and {{module_priorities}}.
        - suggest modules **different from those already in the user’s query**, 
          but they can be **related or from the same project group** if relevant.
          Always select priority classes that provide broader or complementary coverage.
        - Examples:
            a. "Add modules Accessibility, Launcher and class Class_2 for additional coverage."
        - Always **quote module names exactly as listed** — never paraphrase or abbreviate.
        - Never suggest anything unrelated to generating test cases.
b. If no plan was saved -> suggest saving the test plan.
c. If execution failed -> suggest refining query, adjusting parameters, or retrying.
d. If the test plan is successfully generated with expected number of test cases,
   **do not suggest anything further.**

Never repeat ideas or mix invalid module names.
Keep tone concise, helpful, and action-oriented.
"""


SUGGESTION_LLM_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SUGGESTION_LLM_PROMPT_TEXT),
        ("human", "Structure the following LLM response:\n\n{content}"),
    ]
)