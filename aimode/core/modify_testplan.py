import json
from langchain_core.messages import HumanMessage
from loguru import logger
from aimode.core.llms import llm
from apps.core.models import AISessionStore, TestPlanSession
from apps.core.helpers import save_version
from aimode.core.tools import get_last_generated_testplan


def modify_testplan(session_id: str, add_data: bool, tcs_list: list):
    """
    Modify an already-generated test plan by adding or removing testcases.
    Generates an LLM-based coverage impact summary and saves a new version.
    """
    existing_plan = get_last_generated_testplan()
    if not existing_plan:
        return {"status": 400, "message": "No existing test plan found to modify."}

    existing_data = existing_plan.get("data", {})
    existing_testcases = existing_data.get("testcases", [])

    title = "added testcases" if add_data else "deleted testcases"

    dynamic_text = json.dumps(tcs_list, indent=2)
    existing_text = json.dumps(existing_testcases, indent=2)

    PROMPT = f"""
    You are an expert QA architect. Your task is to evaluate changes made to a test plan.

    You will receive:
    1. The existing test plan (list of testcases)
    2. A list of {title}

    Your job:
    - Analyze if added/removed testcases increase or decrease risk coverage.
    - Check if added testcases improve coverage.
    - Check if deleted testcases remove essential coverage.
    - Detect redundancy removal (good) or missing coverage (bad).
    - If added testcases belong to modules that were not part of the original test plan, briefly inform the user. Explain how this impacts the test plan.
        - Explain the impact: whether it expands coverage (positive) or deviates from the intended module scope (potential issue).
    - Provide a clear verdict.
    - DO NOT rewrite or generate testcases.

    Your output:
    - Provide ONLY 1–2 sentences summarizing the coverage impact.
    - No bullet points. No extra commentary.

    Existing Test Plan:
    {existing_text}

    Updated {title}:
    {dynamic_text}
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

    session_obj, _ = AISessionStore.objects.get_or_create(session_id=session_id)
    next_version = TestPlanSession.objects.filter(session=session_obj).count() + 1
    save_data = {
        "session": session_id,
        "context": existing_data.get("description", "AI-modified test plan"),
        "version": str(next_version),
        "name": existing_data.get("name", "Test Plan"),
        "description": existing_data.get("description", ""),
        "modules": existing_data.get("modules", []),
        "output_counts": len(updated_testcases),
        "testcase_data": updated_testcases,
    }
    save_version(save_data)
    content_dict: Dict[str, Any] = {
        "content": str,
        "tcs_data": {},
    }

    content_dict["content"] = coverage_impact
    content_dict[
        "content"
    ] += f" The modified test plan has been saved as version {next_version}."
    content_dict["tcs_data"] = updated_testcases
    return content_dict
