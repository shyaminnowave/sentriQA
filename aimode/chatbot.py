import json
from typing import Dict, Any
from aimode.core.agent import graph
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

def get_llm_response(query: str, session_id: str) -> Dict[str, Any]:
    """
    Get a structured LLM response from the agent.

    Args:
        query (str): User input query.
        session_id (str): Unique session/thread ID.

    Returns:
        Dict[str, Any]: Dictionary with response content, test case data, and suggestions.
    """
    config = {"configurable": {"thread_id": session_id}}

    messages = graph.invoke(
        {"messages": [HumanMessage(content=query)]},
        config=config,
    )

    msgs = messages["messages"]

    last_human_index = max(
        (i for i, m in enumerate(msgs) if isinstance(m, HumanMessage)), default=-1
    )
    last_after_human = msgs[last_human_index + 1 :] if last_human_index >= 0 else []

    content_dict: Dict[str, Any] = {
        "content": msgs[-1].content,
        "tcs_data": {},
        "suggestions": [],
    }

    for msg in last_after_human:
        if isinstance(msg, ToolMessage) and msg.name == "generate_testplan":
            if msg:
                try:
                    content_dict["tcs_data"] = json.loads(msg.content)
                except Exception:
                    content_dict["tcs_data"] = {}
            else:
                print("msg_error")
                content_dict["tcs_data"] = {}
            break

    if not content_dict["tcs_data"]:
        structured_dict = msgs[-1].additional_kwargs.get("structured")

        if structured_dict:
            base_content = structured_dict.get("base_content", msgs[-1].content)
            suggestions = structured_dict.get("suggestions", [])
            content_dict = {
                "content": base_content,
                "tcs_data": {},
                "suggestions": suggestions,
            }

    return content_dict


if __name__ == "__main__":
    response = get_llm_response("hi", "123")
    response = get_llm_response("Hii, Generate testplan  for module Player and Launcher with 5 outputs.", "123")
    print(response)
