import json, ast
from typing import Dict, Any
from aimode.core.agent import graph
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger

memory = MemorySaver()

def get_llm_response(query: str, session_id: str) -> Dict[str, Any]:
    """
    Get a structured LLM response from the agent.
    """
    logger.info(f"[chatbot.py] get_llm_response called with session_id={session_id}, query={query}")

    config = {"configurable": {"thread_id": session_id}}

    # Pass the user prompt and session_id in the state
    state = {
        "messages": [HumanMessage(content=query)],
        "user_prompt": query,
        "session_id": session_id
    }
    logger.info(f"[chatbot.py] Invoking graph with state keys: {list(state.keys())}")

    messages = graph.invoke(state, config=config)
    msgs = messages["messages"]
    logger.info(f"[chatbot.py] Graph returned {len(msgs)} messages")

    last_human_index = max((i for i, m in enumerate(msgs) if isinstance(m, HumanMessage)), default=-1)
    last_after_human = msgs[last_human_index + 1:] if last_human_index >= 0 else []

    content_dict: Dict[str, Any] = {
        "content": msgs[-1].content,
        "tcs_data": {},
        "suggestions": [],
    }

    for msg in last_after_human:
        if isinstance(msg, ToolMessage) and msg.name == "generate_testplan":
            raw_content = msg.content.strip()
            if "error" not in raw_content.lower():
                try:
                    if raw_content.startswith("{") or raw_content.startswith("["):
                        content_dict["tcs_data"] = json.loads(raw_content)
                    else:
                        content_dict["tcs_data"] = ast.literal_eval(raw_content)
                except Exception as e:
                    logger.error(f"[chatbot.py] Failed to parse tcs_data: {e}")
                    content_dict["tcs_data"] = {}
            else:
                content_dict["tcs_data"] = {}
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

    logger.info(f"[chatbot.py] Final tcs_data: {content_dict['tcs_data']}")

    # Check if a version was saved and append the message to the content
    if content_dict["tcs_data"] and isinstance(content_dict["tcs_data"], dict):
        version_message = content_dict["tcs_data"].get("version_message")
        if version_message:
            content_dict["content"] += f"\n\n{version_message}"

    return content_dict


