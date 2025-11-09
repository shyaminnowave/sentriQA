import json, ast
from typing import Dict, Any
from aimode.core.agent import graph
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger

memory = MemorySaver()

def get_llm_response(query: str, session_id: str) -> Dict[str, Any]:
    logger.info(f"get_llm_response called with session_id={session_id}, query={query}")

    config = {"configurable": {"thread_id": session_id}}
    state = {
        "messages": [HumanMessage(content=query)],
        "user_prompt": query,
        "session_id": session_id
    }

    logger.info(f"Invoking graph with state keys: {list(state.keys())}")

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
    logger.info(f"Raw assistant content before filtering: {raw_response[:250]}")

    if any(kw in raw_response for kw in [
        "Test Plan Name:", "Generated Test Cases:", "Modules:", "Priority:", "Description:"
    ]):
        logger.info("Detected verbose inline testplan response — trimming for user.")
        display_text = (
            "Test plan has been updated successfully. "
            "You can view all test cases in the left panel."
        )
    else:
        display_text = raw_response

    content_dict: Dict[str, Any] = {
        "content": display_text,
        "tcs_data": {},
        "suggestions": [],
        }

    for msg in last_after_human:
        if isinstance(msg, ToolMessage) and msg.name == "generate_testplan":
            logger.info("Received tool output from generate_testplan (hidden from user).")
            raw_content = msg.content.strip()
            if "error" not in raw_content.lower():
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
                logger.info(f"version message : {version_message}")
                if len(tcs_list) == 0:
                    content_dict["content"] = "No matching test cases found. Please refine your parameters."
                    break
                elif requested_count > len(tcs_list):
                    if version_message:
                        content_dict["content"] = f"\n{version_message}."
                    content_dict["content"] += (
                        f" \nOnly {len(tcs_list)} matching test cases were found based on your criteria. "
                        "Would you like to adjust the parameters and continue?\n"
                    )
                    
                else:
                    content_dict["content"] = "Test plan generated successfully. You can view all test cases in the left panel.\n"
                    if version_message:
                        content_dict["content"] += f"\n{version_message}"
                if no_save:
                    content_dict["content"] += f" \n {no_save} "
                    content_dict["suggestions"] += ["Save it as new version?"]
            else:
                content_dict["content"] = "Test plan generated successfully."

            break

    if not content_dict["tcs_data"]:
        structured_dict = msgs[-1].additional_kwargs.get("structured") if hasattr(msgs[-1], 'additional_kwargs') else None
        if structured_dict:
            base_content = structured_dict.get("base_content", msgs[-1].content)
            suggestions = structured_dict.get("suggestions", [])
            content_dict = {
                "content": base_content,
                "tcs_data": {},
                "suggestions": suggestions,
            }
        

    logger.info(f"Final tcs_data: {content_dict['tcs_data']}")
    if not content_dict.get("suggestions"):
        content_dict.pop("suggestions", None)
    if not content_dict.get("tcs_data"):
        content_dict.pop("tcs_data", None)
    tcs_data = content_dict.get("tcs_data") or {}
    data = tcs_data.get("data") if isinstance(tcs_data, dict) else {}

    if not isinstance(data, dict) or not data.get("testcases"):
        content_dict.pop("tcs_data", None)

    return content_dict