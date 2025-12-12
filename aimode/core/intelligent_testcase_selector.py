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
    output_counts: int,
    session_id: str,
):
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
        You are an expert QA Test Planner working in a risk-based testing system.
        Use your knowledge of risk-based testing to evaluate and identify the highest-risk testcases for modules.
        You do NOT rely only on testscore.
        Respond only with valid JSON.
        """
        user_prompt = f"""
        USER QUERY: {user_query}
        MODULES: {module_names}
        REQUESTED NUMBER OF TESTCASES: {output_counts}

        Below are the candidate test cases in JSON format:
        {json.dumps(testcases, indent=2)}

        SELECTION RULES:
        - Analyze risk based on ALL attributes, not only testscore.
        - Use domain knowledge and risk-based testing principles.
        - Do NOT create or imagine new testcases.
        - Only choose from the list provided above.
        - Only include testcases belonging to the requested modules.
        - Output must be a pure JSON array of ONLY the selected testcase objects.

        No extra text, explanations, comments, or metadata.
        Output MUST be a valid JSON array.
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
    You are a Senior QA Analyst who is working with a Risk-Based Testing system.

    Evaluate whether the selected testcases {selected_cases} are sufficient for risk based testing of the selected modules {module_names}.
    if not then explain what is missing to test the selected modules and how it can be improved.

    The warning must:
    - Not mention module names or numbers

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
