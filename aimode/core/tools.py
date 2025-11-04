import os
import hashlib
import json
from loguru import logger
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv
from langchain_core.tools import tool

from aimode.core.database import db, conn
from aimode.core.prompts import build_sql_generation_prompt, get_sql_table_names
from aimode.core.intelligent_testcase_selector import intelligent_testcase_selector
from aimode.core.llms import llm
from apps.core.helpers import generate_score

load_dotenv()

# Global session ID helper
_current_session_id: Optional[str] = None
_current_user_prompt: Optional[str] = None

def set_current_session_id(session_id: str, user_prompt: Optional[str] = None):
    """Set the session_id from agent.py"""
    global _current_session_id, _current_user_prompt
    _current_session_id = session_id
    _current_user_prompt = user_prompt
    logger.info(f"[tools.py] session_id set: {session_id}")
    logger.info(f"[tools.py] user_prompt set: {user_prompt[:100]}")

def get_current_session_id() -> Optional[str]:
    """Return the current session_id for tools"""
    return _current_session_id

def get_current_user_prompt() -> Optional[str]:
    """Return the current user_prompt for tools."""
    return _current_user_prompt

# SQL QUERY GENERATOR
class SQLQueryGeneratorInput(BaseModel):
    user_query: str

@tool(args_schema=SQLQueryGeneratorInput, description="Generates an SQL query from natural language user query")
def sql_query_generator(user_query) -> str:
    try:
        logger.info(f"SQL Query Requested: {user_query}")
        # tables = get_sql_table_names(db)
        pg_conn = db.ensure_connection_alive()  #refresh connection
        tables = get_sql_table_names(pg_conn)
        # sql_prompt = build_sql_generation_prompt(conn=db, user_query=user_query)
        sql_prompt = build_sql_generation_prompt(conn=pg_conn, user_query=user_query)
        response = llm.invoke(sql_prompt)
        sql_query = response.content
        logger.info(f"SQL Query Generated: {sql_query}")
        return sql_query
    except Exception as e:
        logger.error(f"SQL generation error: {e}")
        return f"SELECT 'Error: {e}' AS error;"

# SQL QUERY EXECUTION
class SQLQueryExecutionInput(BaseModel):
    sql_query: str

@tool(args_schema=SQLQueryExecutionInput, description="Executes a SQL query and returns results")
def execute_sql_query(sql_query) -> list:
    try:
        results = db.execute(sql_query)
        logger.info("SQL Query Executed Successfully")
        return results
    except Exception as e:
        logger.error(f"Error executing SQL query: {e}")
        return []

# MODULE HELPERS
def get_id_module_mapping():
    try:
        rows = db.execute("SELECT DISTINCT cm.name, cm.id FROM core.core_module AS cm")
        return sorted([{"id": r[1], "name": r[0]} for r in rows], key=lambda x: x["id"])
    except Exception as e:
        logger.error(f"Error fetching module mapping: {e}")
        return []

def get_ids_by_module_names(module_names: list[str]) -> list[int]:
    mapping = {m["name"]: m["id"] for m in get_id_module_mapping() if isinstance(m, dict)}
    return [mapping.get(name) for name in module_names if name in mapping]

# TEST PLAN GENERATOR
class TestPlanGeneratorInput(BaseModel):
    name: Optional[str] = Field(None, description="Name of the test plan")
    description: Optional[str] = Field(None, description="Description of the test plan")
    output_counts: Optional[int] = Field(None, description="Number of test cases to generate")
    module_names: Optional[List[str]] = Field(None, description="List of module names to include")
    priority: Optional[List[str]] = Field(None, description="Priority level for test cases")
    user_prompt: Optional[str] = Field(None, description="Original user prompt for change detection")
    session_id: Optional[str] = Field(None, description="Session ID passed from the front end")


@tool(args_schema=TestPlanGeneratorInput, description="Generates structured test plans using intelligent LLM-assisted selection")
def generate_testplan(
    name: str = None,
    description: str = None,
    output_counts: int = None,
    module_names: list[str] = None,
    priority: List[str] = None,
    user_prompt: str = None,
    session_id: str = None,
):
    """
     Generates a structured test plan based on the given parameters and optionally saves it to the database.    
     Steps:
     1. Accepts test plan details including name, description, number of test cases to generate, 
        relevant modules, priority, and optional user prompt.
     2. Converts module names to module IDs for internal processing.
     3. Validates required parameters (output_counts, module_names, and priority); logs a warning and returns None if missing.
     4. Constructs a payload and calls `intelligent_testcase_selector` to generate test cases for the test plan. Generates a structured test plan using the intelligent test case selector (algorithm + LLM).
     5. If test cases are returned, optionally saves the test plan version:
        - Uses a session ID to track the AI session.
        - Checks with `change_detector` if a new version should be saved based on LLM reasoning and user instructions.
        - Saves the new version using `save_version()` if required.
     6. Returns the generated test cases data.
    """

    # if not session_id:
    #     session_id = get_current_session_id() or "89023860-5bd5-48fa-adca-7f6bdab52c02"
    #     logger.info(f"[generate_testplan] Using session_id: {session_id}")
    session_id = get_current_session_id()
    user_prompt = get_current_user_prompt()

    # Validate required parameters
    if not (module_names and priority):
        logger.warning("Missing required parameters for test plan generation")
        return None

    # Call the intelligent selector instead of generate_score
    logger.info(f"[generate_testplan] Calling intelligent_testcase_selector for modules={module_names}, priority={priority}")
    tcs_data = intelligent_testcase_selector(
        user_query=user_prompt or "",
        module_names=module_names,
        priority=priority,
        output_counts=output_counts or 10,
        session_id=session_id
    )

    if not tcs_data or tcs_data.get("status") != 200:
        logger.error("Intelligent selector returned no testcases or error")
        return None

    # Step 3: Save version if needed
    try:
        from apps.core.helpers import save_version
        from apps.core.models import AISessionStore, TestPlanSession
        from aimode.core.change_detector import change_detector

        session_obj, _ = AISessionStore.objects.get_or_create(session_id=session_id)
        should_save = True
        save_reason = "New test plan generated"
        logger.info(f"user_prompt: {user_prompt}")
        if user_prompt:
            should_save = change_detector.should_save_version(user_prompt, session_id)
            save_reason = "Major changes detected" if should_save else "Minor changes detected"
        if should_save:
            testcases = tcs_data.get("data", {}).get("testcases", [])
            if not testcases:
                logger.warning("[generate_testplan] No testcases generated — skipping version save.")
                should_save = False
            else:
                next_version = TestPlanSession.objects.filter(session=session_obj).count() + 1
                save_data = {
                    "session": session_id,
                    "context": user_prompt or "No context provided",
                    "version": str(next_version),
                    "name": name or "Test Plan",
                    "description": description or "Auto-generated test plan",
                    "modules": module_names,
                    "output_counts": output_counts,
                    "testcase_data": testcases,
                }
                save_version(save_data)
                tcs_data["data"]["version_saved"] = next_version
                tcs_data["data"]["version_message"] = f"This has been saved as version {next_version}"
                logger.success(f"Saved test plan version {next_version} to database - {save_reason}")
        else:
            logger.info(f"Skipped saving test plan to database - {save_reason}")
            if user_prompt and change_detector._user_requested_no_save(user_prompt):
                tcs_data["data"]["no_save"] = " This test plan is not saved. "


    except Exception as e:
        logger.error(f"Error handling test plan version: {e}")

    return tcs_data