import json
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from loguru import logger
from aimode.core.llms import llm
from apps.core.models import AISessionStore, TestPlanSession
from apps.core.helpers import save_version
from aimode.core.tools import set_last_generated_testplan, get_last_generated_testplan


def modify_testplan(
    session_id: str,
    add_data: bool,
    tcs_list: list,
    existing_plan: Dict[str, Any] = None,
):
    """
    Modify an already-generated test plan by adding or removing testcases.
    Generates an LLM-based coverage impact summary and then ASKS USER
    whether to save the modified test plan version.
    """
    logger.success(session_id)
    logger.success("Inside modify testplan")
    if existing_plan is None:
        existing_plan = get_last_generated_testplan(session_id)

    if not existing_plan:
        return {"status": 400, "message": "No existing test plan found to modify."}

    existing_data = existing_plan.get("data", {})
    existing_testcases = existing_data.get("testcases", [])

    title = "added testcases" if add_data else "deleted testcases"

    # if not add_data:
    #     tcs_ids = set(str(x) for x in tcs_list)
    #     matched_testcases = [
    #         tc for tc in existing_testcases if str(tc["id"]) in tcs_ids
    #     ]
    #     tcs_list = matched_testcases
    #     logger.info(f"Matched testcases for deletion: {tcs_list}")
    if not add_data:
        tcs_ids = set()
        for item in tcs_list:
            if isinstance(item, dict) and "id" in item:
                tcs_ids.add(str(item["id"]))
            else:
                tcs_ids.add(str(item))
        matched_testcases = [
            tc for tc in existing_testcases if str(tc["id"]) in tcs_ids
        ]
        tcs_list = matched_testcases
        logger.info(f"Matched testcases for deletion: {tcs_list}")

    chosen_testcases_json = json.dumps(tcs_list, indent=2)
    existing_testcases_json = json.dumps(existing_testcases, indent=2)

    PROMPT = f"""
    You are an expert QA architect. Your task is to evaluate changes made to a test plan.

    You will receive:
    1. The existing test plan (list of testcases)
    2. A list of {title}

    Your job:
    - Analyze whether the changes increase or decrease risk coverage.
    - Evaluate if deleted testcases remove essential coverage.
    - Evaluate if added testcases improve or expand coverage.
    - Detect redundancy removal (good) or missing coverage (bad).
    - If added testcases belong to new modules, explain their impact briefly.

    Your output:
    - Provide ONLY 1–2 sentences summarizing the coverage impact.
    - No bullet points. No long explanations.

    Existing Test Plan:
    {existing_testcases_json}

    Updated {title}:
    {chosen_testcases_json}
    """

    llm_response = llm.invoke([HumanMessage(content=PROMPT)])
    coverage_impact = llm_response.content.strip()

    if add_data:
        for tc in tcs_list:
            tc["mode"] = "classic"
            tc["generated"] = True

        updated_testcases = existing_testcases + tcs_list

    else:
        remove_ids = {tc["id"] for tc in tcs_list}
        updated_testcases = [
            tc for tc in existing_testcases if tc["id"] not in remove_ids
        ]
    set_last_generated_testplan(
        session_id, {"data": {**existing_data, "testcases": updated_testcases}}
    )
    return {
        "status": "pending_user_confirmation",
        "content": (
            f"{coverage_impact}\n\n"
            "Would you like to save this updated test plan as a new version?\n\n"
        ),
        "tcs_data": updated_testcases,
        "ask_to_save": True,
    }
