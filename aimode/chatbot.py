import json, ast
from typing import Dict, Any, Optional, List
from aimode.core.agent import graph
from aimode.core.tools import get_last_generated_testplan
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from aimode.core.modify_testplan import modify_testplan
from loguru import logger

memory = MemorySaver()

def get_llm_response(query: str, session_id: str,add_data: bool = False,tcs_list: List[Dict[str, Any]] = None, modify_extra_suggestions: bool = False) -> Dict[str, Any]:
    if modify_extra_suggestions:
        return{
            "content": "How may I assist you? Would you like to add or delete test cases in the test plan?",
            "suggestions": ["Add testcases", "Delete testcases"],
        }

    if tcs_list is not None:
        return modify_testplan(
            session_id=session_id,
            add_data=add_data,
            tcs_list=tcs_list,)
            
    config = {"configurable": {"thread_id": session_id}}
    state = {
        "messages": [HumanMessage(content=query)],
        "user_prompt": query,
        "session_id": session_id
    }

    try:  
        messages = graph.invoke(state, config=config)
    except Exception as e: 
        logger.error(f"LLM or tool execution failed: {e}")
        return {
            "content": "Something went wrong while creating the test plan. Please retry or modify your parameters.",
            "tcs_data": {},
            "suggestions": [],
        }
    msgs = messages["messages"]
    last_human_index = max((i for i, m in enumerate(msgs) if isinstance(m, HumanMessage)), default=-1)
    last_after_human = msgs[last_human_index + 1:] if last_human_index >= 0 else []

    raw_response = msgs[-1].content if hasattr(msgs[-1], "content") else str(msgs[-1])

    content_dict: Dict[str, Any] = {
        "content": raw_response,
        "tcs_data": {},
        "suggestions": [],
        }

    for msg in last_after_human:
        if isinstance(msg, ToolMessage) and msg.name == "generate_testplan":
            raw_content = msg.content.strip()
            # if "error" not in raw_content.lower():
            if "success" in raw_content.lower():
                try:
                    if raw_content.startswith("{") or raw_content.startswith("["):
                        content_dict["tcs_data"] = json.loads(raw_content)
                    else:
                        content_dict["tcs_data"] = ast.literal_eval(raw_content)
                except Exception as e:
                    logger.error(f"Failed to parse tcs_data: {e}")
                    content_dict["tcs_data"] = {}
            else:
                content_dict["tcs_data"] = {}

            if isinstance(content_dict["tcs_data"], dict) and "data" in content_dict["tcs_data"]:
                tcs_info = content_dict["tcs_data"]["data"]
                tcs_list = tcs_info.get("testcases", [])
                requested_count = tcs_info.get("output_counts", 0)
                version_message = tcs_info.get("version_message")
                no_save = tcs_info.get("no_save")
                if len(tcs_list) == 0:
                    content_dict["content"] = "No matching test cases found. Please refine your parameters."
                    break
                elif requested_count > len(tcs_list):
                    if version_message:
                        content_dict["content"] = f"\n{version_message}."
                    content_dict["content"] = (
                        f" \nOnly {len(tcs_list)} matching test cases were found based on your criteria. "
                        "Would you like to adjust the parameters and continue?\n"
                    )
                    
                else:
                    content_dict["content"] = "Test plan generated successfully. You can view all test cases in the left panel.\n"
                if version_message:
                        content_dict["content"] += f"\n{version_message}."
                if no_save:
                    content_dict["content"] += f" \n {no_save} "
            else:
                content_dict["content"] = "Test plan generated successfully."

            break
        if isinstance(msg, ToolMessage) and msg.name == "save_new_testplan_version":

            raw_save_output = msg.content.strip()
            try:
                if raw_save_output.startswith("{") or raw_save_output.startswith("["):
                    content_dict["tcs_data"] = json.loads(raw_save_output)
                else:
                    content_dict["tcs_data"] = ast.literal_eval(raw_save_output)
            except Exception as e:
                logger.error(f"Failed parsing save tool output: {e}")
        if isinstance(msg, ToolMessage) and msg.name == "add_testcases":
            raw = msg.content
            try:
                parsed = json.loads(raw)
                return {
                "content": "I’ve gathered all the test cases you can add to the test plan.",
                "all_testcases_data": parsed.get("all_testcases_data", parsed)
            }
            except Exception:
                return {"all_testcases_data_raw": raw}

    structured_dict = getattr(msgs[-1], "additional_kwargs", {}).get("structured", None)
    if structured_dict:
        base_content = structured_dict.get("base_content") or msgs[-1].content
        suggestions = structured_dict.get("suggestions", [])
        if suggestions:
            existing = content_dict.get("suggestions", [])
            merged = list(dict.fromkeys(existing + suggestions))
            content_dict["suggestions"] = merged
        
    logger.info(f"Final tcs_data: {content_dict['tcs_data']}")
    # content_dict["suggestions"] += ["Add testcases", "Delete testcases"]
    if not content_dict.get("suggestions"):
        content_dict.pop("suggestions", None)
    if not content_dict.get("tcs_data"):
        content_dict.pop("tcs_data", None)
    tcs_data = content_dict.get("tcs_data") or {}
    data = tcs_data.get("data") if isinstance(tcs_data, dict) else {}

    if not isinstance(data, dict) or not data.get("testcases"):
        content_dict.pop("tcs_data", None)
    return content_dict
