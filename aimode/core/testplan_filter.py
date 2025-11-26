import json
from typing import Any, Dict, List
from loguru import logger
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from aimode.core.llms import llm
from apps.core.ai_filter import get_filtered_data
from aimode.core.prompts import AGENT_FILTER_PROMPT_TEXT


session_states: Dict[str, Dict[str, Any]] = {}

def get_session_state(session_id: str) -> Dict[str, Any]:
    return session_states.setdefault(session_id, {
        "filters": {},
        "conversation_history": [],
    })


def parse_json_from_llm(content: str) -> Dict[str, Any]:
    try:
        if "```json" in content:
            content = content.split("```json", 1)[1].split("```", 1)[0].strip()
        return json.loads(content)
    except Exception:
        logger.error(f"Failed to parse JSON:\n{content}")
        return {"filters": {}, "suggestions": []}


class FilterArgs(BaseModel):
    filters: Dict[str, List[str]]

@tool(description="filter_testcases_tool", args_schema=FilterArgs)
def filter_testcases_tool(filters: Dict[str, List[str]]):
    logger.debug(f"filtering with: {filters}")
    return get_filtered_data(filters)



def run_filter_flow(user_message: str, session_id: str) -> Dict[str, Any]:
    state = get_session_state(session_id)

    state["conversation_history"].append(HumanMessage(content=user_message))

    messages = [
        SystemMessage(content=AGENT_FILTER_PROMPT_TEXT),
        *state["conversation_history"]
    ]

    response = llm.bind_tools([filter_testcases_tool]).invoke(messages)

    raw_content = (getattr(response, "content", None) or str(response)).strip()
    logger.info(f"[LLM] {raw_content}")

    state["conversation_history"].append(SystemMessage(content=raw_content))

    parsed = parse_json_from_llm(raw_content)
    new_filters = parsed.get("filters", {})
    suggestions = parsed.get("suggestions", [])

    has_new = any(new_filters.values())
    logger.debug(has_new)
    if has_new:
        state["filters"] = new_filters
        user_content = "Testcases have been filtered as per your requirements."
    else:
        if suggestions:
            user_content = "Hi, I can help you with filtering the testcases. Please select one of the suggested options."
        else:
            user_content = raw_content

    logger.info(f"[Session {session_id}] Filters -> {state['filters']}")

    result = {
        "session": session_id,
        "content": user_content,
        "filters": state["filters"],
        "tcs_data": get_filtered_data(state["filters"]) if has_new else None,
        "suggestions": suggestions,
        }

    logger.success(result)
    return result
