"""
Intelligent hybrid test case selector:
1. Fetch all candidate test cases using algorithmic scoring.
2. Let the LLM select the most relevant ones.
"""

import json
from loguru import logger
from rest_framework import status
from django.db.models import Q
from typing import List, Dict
from apps.core.helpers import generate_score
from apps.core.models import Module
from aimode.core.llms import llm


def intelligent_testcase_selector(
    user_query: str,
    module_names: List[str],
    priority: List[str],
    output_counts: int,
    session_id: str,
):
    logger.info(
        f"intelligent_testcase_selector | session={session_id}, modules={module_names}, priority={priority}"
    )

    # Step 1:module IDs
    module_ids = list(
        Module.objects.filter(name__in=module_names).values_list("id", flat=True)
    )
    module_display_names = list(
        Module.objects.filter(id__in=module_ids).values_list("name", flat=True)
    )

    if not module_ids:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "data": {},
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "Invalid or empty module names.",
        }

    # Step 2: Run scoring algorithm
    # payload = {
    #     "name": f"Intelligent Plan: {', '.join(module_names)[:180]}",
    #     "description": f"LLM-assisted selection for: {user_query}",
    #     "output_counts": output_counts,
    #     "module": module_ids,
    #     "priority": priority,
    # }
    max_display = 5
    display_modules = module_names[:max_display]

    if len(module_names) > max_display:
        extra = len(module_names) - max_display
        module_part = f"{', '.join(display_modules)} and {extra} more"
    else:
        module_part = ", ".join(display_modules)

    payload = {
        "name": f"Intelligent Plan: {module_part}",
        "description": f"LLM-assisted selection for: {user_query}",
        "output_counts": output_counts,
        "module": module_ids,
        "priority": priority,
    }

    try:
        logger.info("Fetching candidate testcases from scoring engine...")
        score_data = generate_score(payload)
        testcases = score_data.get("data", {}).get("testcases", [])
        logger.info(f"Retrieved {len(testcases)} candidate testcases.")

        if not testcases:
            return score_data

    except Exception as e:
        logger.exception("generate_score() failed.")
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "data": {},
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Error while fetching testcases. Please retry.",
        }

    # Step 3: LLM selection (choose most relevant testcases)
    try:
        system_prompt = """
        You are an Expert QA Test Plan Manager working with a Risk-Based Test Planning (RBTP) system.
        Your task is to intelligently select the most relevant and high-risk test cases for the given modules/features.

        Selection criteria:
        - Focus on test cases that cover **high-risk or business-critical functionalities**.
        - Prioritize scenarios with **high failure**, strong **module dependencies**, or **system-wide impact**.
        - Prefer test cases that validate **critical paths, edge conditions, or potential failure points**.
        - Consider risk-related signals such as failure rate, defect density, and module sensitivity.

        Respond ONLY with a valid JSON list of selected test cases (no explanation or text).
        """

        user_prompt = f"""
        USER QUERY: {user_query}
        PRIORITY: {priority}
        MODULES: {module_names}

        Below is the list of all candidate test cases:
        {json.dumps(testcases, indent=2)}

        Select **exactly {output_counts}** test cases that best fit the risk-based criteria.
        If fewer than {output_counts} fit, return only those few.
        Output ONLY valid JSON (list of selected testcases).
        """

        llm_response = llm.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )

        content = llm_response.content.strip()
        if "```json" in content:
            content = content.split("```json")[-1].split("```")[0]

        selected_cases = json.loads(content)
        logger.info(f"LLM selected {len(selected_cases)} testcases.")

    except Exception as e:
        logger.error(f"LLM selection failed: {e}")
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "data": {},
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Error during intelligent selection. Please retry.",
        }
    warning = ""
    warning_prompt = f"""
    You are a Senior QA Analyst.

    Evaluate whether the number of test cases requested by the user ({output_counts}) 
    and the selected testcases {selected_cases}
    are sufficient to cover the risks of the selected modules.

    You must generate a warning if:
    - the user-requested test count is too low for meaningful risk coverage, OR
    - the selected testcases miss important risk areas or seem insufficient.

    The warning must:
    - Be a single short sentence suitable as a heading
    - Not mention module names or numbers
    - Convey that the test count or coverage is insufficient
    - Suggest increasing the test count

    If coverage appears adequate, return an empty string.
    Output ONLY the warning or an empty string.
    """

    try:
        warning_response = llm.invoke(warning_prompt)

        warning = getattr(warning_response, "content", str(warning_response)).strip()
        warning = warning.replace("```", "").strip()
        warning = warning.strip('"')
        warning = " ".join(warning.split())
        logger.success(warning)

    except Exception as e:
        logger.error(f"Warning generation failed: {e}")
        warning = ""

    # Step 4: Generate separate reasoning summary
    reasoning = []
    try:
        logger.info("Generating reasoning for selected testcases...")

        reasoning_system_prompt = """
        You are a Senior QA Analyst contributing to Risk-Based Test Planning (RBTP) system.
        Your task is to provide a concise, risk-focused reasoning for why each selected test case was chosen for testing of given modules or features.

        Guidelines:
        - Provide **1-2 clear, specific sentence** per test case.
        - Base your reasoning on testcases and parameters like **failure rate, defect**.
        - Explain how the test case helps cover high-risk areas, critical paths, or potential failure points.
        - Avoid generic or obvious statements; focus on meaningful, risk-aware insights.
        - Ensure each reasoning item is unique and tailored to the test case's purpose.

        Return ONLY a valid JSON array in this format:
        [
        {"id": <testcase_id>, "reason": "<AI-driven risk-based explanation>"},
        ...
        ]
        """

        reasoning_user_prompt = f"""
        MODULES: {module_names}
        PRIORITY: {priority}

        Selected Test Cases:
        {json.dumps(selected_cases, indent=2)}

        Generate risk-based reasoning for each test case.
        """

        reasoning_response = llm.invoke(
            [
                {"role": "system", "content": reasoning_system_prompt},
                {"role": "user", "content": reasoning_user_prompt},
            ]
        )

        reasoning_content = reasoning_response.content.strip()
        if "```json" in reasoning_content:
            reasoning_content = reasoning_content.split("```json")[-1].split("```")[0]

        reasoning = json.loads(reasoning_content)
        logger.info(f"Generated reasoning for {len(reasoning)} testcases.")

    except Exception as e:
        logger.error(f"Reasoning generation failed: {e}")
        reasoning = [{"id": None, "reason": "Reasoning generation failed."}]

    # Merging reasoning in testcases
    for i in range(min(len(selected_cases), len(reasoning))):
        selected_cases[i]["reason"] = reasoning[i].get("reason", "")

    response = {
        "name": payload["name"],
        "description": payload["description"],
        "modules": module_display_names,
        "output_counts": output_counts,
        "priority": priority,
        "project": "default_project",
        "generate_test_count": len(selected_cases),
        "testcase_type": "functional",
        "testcases": selected_cases,
        "version_info": warning,
    }

    final_response = {
        "status": status.HTTP_200_OK,
        "data": response,
        "status_code": status.HTTP_200_OK,
        "message": "success",
    }

    logger.success(
        f"[COMPLETE] Returned {len(selected_cases)} testcases with {len(reasoning)} reasoning items."
    )
    return final_response
