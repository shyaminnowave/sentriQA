import json
from typing import Any, Dict
# from langchain.schema import HumanMessage, SystemMessage
from langchain_core.messages import HumanMessage, SystemMessage
from aimode.core.llms import llm
from apps.core.ai_filter import get_filtered_data
from aimode.core.prompts import AGENT_FILTER_PROMPT_TEXT
from loguru import logger

session_states: Dict[str, Dict[str, Any]] = {}


def get_session_state(session_id: str) -> Dict[str, Any]:
    if session_id not in session_states:
        session_states[session_id] = {
            "filters": {},
            "conversation_history": []
        }
    return session_states[session_id]


def parse_json_from_llm(content: str) -> Dict[str, Any]:
    try:
        if "```json" in content:
            content = content.split("```json")[-1].split("```")[0].strip()
        return json.loads(content)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON from LLM: {content}")
        return {}


def merge_filters(existing: Dict[str, Any], new_filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge filters detected by LLM into session state dynamically. Converts strings to lists and deduplicates.
    """
    for key, values in new_filters.items():
        if values:
            if isinstance(values, str):
                values = [values]
            existing[key] = list(set(existing.get(key, []) + values))
    return existing


def run_filter_flow(user_message: str, session_id: str) -> Dict[str, Any]:
    state = get_session_state(session_id)
    filters = state["filters"]

    logger.info(f"[Session {session_id}] User message: {user_message}")
    state["conversation_history"].append(HumanMessage(content=user_message))

    messages = [SystemMessage(content=AGENT_FILTER_PROMPT_TEXT)] + state["conversation_history"]

    response = llm(messages)
    raw_content = getattr(response, "content", str(response)).strip()
    logger.info(raw_content)
    state["conversation_history"].append(SystemMessage(content=raw_content))

    parsed_data = parse_json_from_llm(raw_content)
    llm_filters = parsed_data.get("filters", {})
    suggestions = parsed_data.get("suggestions", [])
    has_new_filters = any(v for v in llm_filters.values())
    if has_new_filters:
        filters = merge_filters(filters, llm_filters)
        state["filters"] = filters

    logger.info(f"[Session {session_id}] Accumulated filters: {filters}")

    content_dict: Dict[str, Any] = {
        "content": raw_content,
        "tcs_data": None,
        "suggestions": suggestions,
        "filters": llm_filters,
    }
    logger.info(f"PAST")
    if has_new_filters:
        results = get_filtered_data(filters)
        results.pop('test_repo') if results.get('test_repo') else None
        content_dict["tcs_data"] = results
        content_dict["content"] = "Testcases have been filtered as per your requirements."
        content_dict["filters"] = llm_filters
    else:
        # No new filters -> conversational response only
        content_dict["content"] = "Please provide testtype, module or priority classes"

    content_dict["suggestions"] = suggestions
    logger.success(content_dict)
    return content_dict