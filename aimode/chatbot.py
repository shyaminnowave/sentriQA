import json, ast
from typing import Dict, Any, Optional, List
from aimode.core.agent import graph
from aimode.core.tools import get_last_generated_testplan
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger

memory = MemorySaver()


def get_llm_response(
    query: str,
    session_id: str,
    add_data: bool = False,
    tcs_list: List[Dict[str, Any]] = None,
    modify_extra_suggestions: bool = False,
) -> Dict[str, Any]:
    if tcs_list is not None:
        from aimode.core.modify_testplan import modify_testplan

        result = modify_testplan(
            session_id=session_id, add_data=add_data, tcs_list=tcs_list
        )
        logger.success(result)
        return {
            "content": result["content"],
            "tcs_data": result.get("tcs_data"),
            "suggestions": [
                "Yes, save the updated test plan",
                "No, discard changes",
            ],
            "ask_to_save": True,
        }
    logger.success(modify_extra_suggestions)
    # if modify_extra_suggestions:
    #     return

    if modify_extra_suggestions:
        return {
            "content": "Hey! You have chosen to modify the test plan, What would you like to do next — add some new test cases or remove a few from your test plan?",
            "suggestions": [
                "Add new test cases",
                "Delete testcases",
            ],
        }

    config = {"configurable": {"thread_id": session_id}}
    state = {
        "messages": [HumanMessage(content=query)],
        "user_prompt": query,
        "session_id": session_id,
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
    last_human_index = max(
        (i for i, m in enumerate(msgs) if isinstance(m, HumanMessage)), default=-1
    )
    last_after_human = msgs[last_human_index + 1 :] if last_human_index >= 0 else []

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

            if (
                isinstance(content_dict["tcs_data"], dict)
                and "data" in content_dict["tcs_data"]
            ):
                tcs_info = content_dict["tcs_data"]["data"]
                tcs_list = tcs_info.get("testcases", [])
                requested_count = tcs_info.get("output_counts", 0)
                version_message = tcs_info.get("version_message")
                no_save = tcs_info.get("no_save")
                if len(tcs_list) == 0:
                    content_dict["content"] = (
                        "No matching test cases found. Please refine your parameters."
                    )
                    break
                elif requested_count > len(tcs_list):
                    if version_message:
                        content_dict["content"] = f"\n{version_message}."
                    content_dict["content"] = (
                        f" \nOnly {len(tcs_list)} matching test cases were found based on your criteria. "
                        "Would you like to adjust the parameters and continue?\n"
                    )

                else:
                    content_dict["content"] = (
                        "Test plan generated successfully. You can view all test cases in the left panel.\n"
                    )
                if version_message:
                    content_dict["content"] += f"\n{version_message}."
                if no_save:
                    content_dict["content"] += f" \n {no_save} "
            else:
                content_dict["content"] = "Test plan generated successfully."

            break

        if isinstance(msg, ToolMessage) and msg.name == "filter_testcases_tool":
            logger.debug(f"Handling filter_testcases_tool message: {msg.content}")

            raw_content = (
                msg.content.strip() if isinstance(msg.content, str) else msg.content
            )

            try:
                # Parse tool output (string → json or direct dict)
                tcs_data = (
                    json.loads(raw_content)
                    if isinstance(raw_content, str)
                    else raw_content
                )
                content_dict["tcs_data"] = tcs_data

                # Check for testcases inside the expected structure
                testcases = (
                    tcs_data.get("data", {}).get("testcases")
                    if isinstance(tcs_data, dict)
                    else None
                )

                if testcases:
                    content_dict["content"] = (
                        "Testcases have been filtered as per your requirements."
                    )
                else:
                    content_dict["content"] = (
                        "No testcases found for the given filters."
                    )

            except Exception as e:
                logger.error(f"Failed to parse filter_testcases_tool output: {e}")
                content_dict["content"] = (
                    "An error occurred while filtering the testcases."
                )
                content_dict["tcs_data"] = {}

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
            if isinstance(raw, str):
                raw = raw.strip()
            try:
                parsed = json.loads(raw) if isinstance(raw, str) else raw
                if isinstance(parsed, dict) and parsed.get("all_testcases_data"):
                    return {
                        "content": parsed.get(
                            "content",
                            "Here are all available test cases you can add to the test plan. "
                            "You may select them directly from the list or provide the IDs of the test cases you'd like to include.",
                        ),
                        "is_add_testcase": True,
                        "all_testcases_data": parsed.get("all_testcases_data", []),
                    }
                if isinstance(parsed, dict) and parsed.get("added_ids"):
                    return {
                        "content": parsed.get(
                            "impact",
                            "The selected test cases have been added successfully.",
                        ),
                        "added_ids": parsed.get("added_ids", []),
                        "tcs_data": parsed.get("updated_testcases", []),
                        "suggestions": [
                            "Yes, save the updated test plan",
                            "No, discard changes",
                        ],
                        "ask_to_save": True,
                    }
            except Exception as e:
                logger.error(f"Error parsing add_testcases response: {e}")
                return {
                    "content": "An error occurred while processing the testcases.",
                    "all_testcases_data_raw": raw,
                    "is_add_testcase": True,
                }

        if isinstance(msg, ToolMessage) and msg.name == "delete_testcases":
            raw = msg.content.strip()
            try:
                parsed = json.loads(raw)
                logger.success(parsed)
                if parsed is True or parsed == "True":
                    return {
                        "content": "To proceed with deletion, please select the applicable test cases from the list, or you can provide the IDs of the test cases you want to delete.",
                        "is_delete": True,
                    }
            except Exception:
                logger.error(raw)
                parsed = {"raw": raw}
            return {
                "content": parsed.get(
                    "impact", "Requested test cases deleted successfully."
                ),
                "deleted_ids": parsed.get("deleted_ids", []),
                "tcs_data": parsed.get("updated_testcases", []),
                "suggestions": [
                    "Yes, save the updated test plan",
                    "No, discard changes",
                ],
                "ask_to_save": True,
            }

    structured_dict = getattr(msgs[-1], "additional_kwargs", {}).get("structured", None)
    if structured_dict:
        base_content = structured_dict.get("base_content") or msgs[-1].content
        suggestions = structured_dict.get("suggestions", [])
        if suggestions:
            existing = content_dict.get("suggestions", [])
            merged = list(dict.fromkeys(existing + suggestions))
            content_dict["suggestions"] = merged

    logger.info(f"Final tcs_data: {content_dict['tcs_data']}")
    if not content_dict.get("suggestions"):
        content_dict.pop("suggestions", None)
    if not content_dict.get("tcs_data"):
        content_dict.pop("tcs_data", None)
    tcs_data = content_dict.get("tcs_data") or {}
    data = tcs_data.get("data") if isinstance(tcs_data, dict) else {}
    if data:
        if data and "testcase_data" in data and "testcases" not in data:
            data["testcases"] = data["testcase_data"]
        if not isinstance(data, dict) or not data.get("testcases"):
            content_dict.pop("tcs_data", None)
    return content_dict
