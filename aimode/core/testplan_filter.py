import json
import re
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
        "last_testplan": None,
    })


# def parse_json_from_llm(content: str) -> Dict[str, Any]:
#     try:
#         match = re.search(r"\{[\s\S]*\}$", content.strip())
#         if match:
#             json_str = match.group()
#             return json.loads(json_str)
#         else:
#             logger.warning("No JSON block found in LLM output")
#             return {"filters": {}, "suggestions": []}
#     except Exception as e:
#         logger.error(f"Failed to parse JSON:\n{content}\nError: {e}")
#         return {"filters": {}, "suggestions": []}

def parse_json_from_llm(content: str) -> Dict[str, Any]:
    try:
        if "```json" in content:
            json_str = content.split("```json", 1)[1].split("```", 1)[0].strip()
        else:
            match = re.search(r"\{[\s\S]*\}", content)
            if not match:
                return {"filters": {}, "suggestions": []}
            json_str = match.group()
        json_str = (json_str.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'"))
        json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"JSON parse failed: {e}\nRaw:\n{json_str}")
        return {"filters": {}, "suggestions": []}


def extract_clean_text(content: str) -> str:
    """
    Removes the JSON block at the end of the LLM response,
    returning only the natural language message.
    """
    match = re.search(r"\{[\s\S]*\}$", content.strip())
    if match:
        return content[: match.start()].strip()
    return content.strip()


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

    has_new_filters = any(new_filters.values())
    logger.debug(f"Has new filters: {has_new_filters}")

    if has_new_filters:
        state["filters"] = new_filters
        tcs_data = get_filtered_data(new_filters)
        if tcs_data:
            state["last_testplan"] = tcs_data
            filters_summary = "; ".join(
                f"{k}: {', '.join(v) if isinstance(v, list) else v}"
                for k, v in new_filters.items() if v
            )

            user_content = (
                    "Testcases have been filtered as per your requirements."
                    + (f" Applied filters: {filters_summary}." if filters_summary else "")
            )
        else:
            user_content = "No testcases found for the given filters."
    else:
        # greetings = ["hello", "hi", "hey", "helllo", "hii"]
        # if any(word in user_message.lower() for word in greetings):
        #     user_content = (
        #         "Hello! I am your filtering agent. "
        #         "I can help you filter testcases based on module, type, or priority."
        #     )
        # else:
        #     user_content = raw_content
        user_content = extract_clean_text(raw_content)

    logger.debug(f"Last test plan: {state['last_testplan']}")

    result = {
        "session": session_id,
        "content": user_content,
        "filters": state["filters"],
        "tcs_data": state["last_testplan"],
    }

    if suggestions:
        result["suggestions"] = suggestions

    logger.success(result)
    return result