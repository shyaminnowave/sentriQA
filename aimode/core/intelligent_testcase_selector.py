import json
from loguru import logger
from rest_framework import status
from django.db.models import Q
from typing import List, Optional, Dict, Any
from apps.core.helpers import generate_score
from apps.core.models import Module, TestCaseMetric
from aimode.core.llms import llm

def intelligent_testcase_selector(user_query: str, module_names: list[str], priority: List[str], output_counts: int, session_id: str):
    """
    Intelligent hybrid test case selector:
    1. Fetch all candidate test cases using algorithmic scoring.
    2. Let the LLM select the most relevant ones.
    3. Return structured output.
    """
    logger.info(f"[INTELLIGENT_SELECTOR] Started for session={session_id}, modules={module_names}, priority={priority}")

    # Step 1: Resolve module IDs
    module_ids = list(Module.objects.filter(name__in=module_names).values_list('id', flat=True))
    module_display_names = list(Module.objects.filter(id__in=module_ids).values_list('name', flat=True))

    if not module_ids:
        logger.warning("[INTELLIGENT_SELECTOR] No valid module IDs found — skipping to fallback.")
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "data": {},
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "Invalid or empty module names",
        }

    # Step 2: Run scoring algorithm to get all candidate testcases
    payload = {
        "name": f"Intelligent Plan for: {', '.join(module_names)}",
        "description": f"LLM-assisted selection for: {user_query}",
        "output_counts": output_counts,
        "module": module_ids,
        "priority": priority,
    }

    try:
        logger.info("[INTELLIGENT_SELECTOR] Calling generate_score() to fetch all testcases")
        score_data = generate_score(payload)
        testcases = score_data.get("data", {}).get("testcases", [])
        logger.info(f"[INTELLIGENT_SELECTOR] Retrieved {len(testcases)} testcases from scoring engine")
        # logger.info(f"Raw output: {testcases}")

        if not testcases:
            logger.warning("[INTELLIGENT_SELECTOR] No testcases found — returning empty result.")
            return score_data

    except Exception as e:
        logger.exception(f"[INTELLIGENT_SELECTOR] generate_score failed: {e}")
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "data": {},
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Something went wrong while creating the test plan. Please retry or modify your parameters.",
        }

    # Step 3: LLM selection
    try:
        logger.info("[INTELLIGENT_SELECTOR] Preparing LLM prompt for intelligent filtering")

        # --- System Prompt ---
        system_prompt = """
        You are an expert QA test planner.
        Your job is to intelligently select the most relevant test cases based on testcases, user input, priority, and module relevance.
        Always respond ONLY with a valid JSON list of selected test cases — no explanation or extra text.
        """

        # --- User Prompt ---
        user_prompt = f"""
        USER QUERY: {user_query}
        PRIORITY: {priority}
        MODULES: {module_names}

        Below is the list of all candidate test cases in JSON:
        {json.dumps(testcases, indent=2)}

        Select {output_counts} test cases that are **most relevant** to the requested user input.
        Return ONLY a valid JSON array of selected test cases.
        """

        # --- LLM Call ---
        llm_response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])

        content = llm_response.content.strip()

        # --- Clean up fenced code blocks (if any) ---
        if "```json" in content:
            content = content.split("```json")[-1].split("```")[0]

        selected_cases = json.loads(content)
        logger.info(f"[INTELLIGENT_SELECTOR] LLM selected {len(selected_cases)} testcases")

    except Exception as e:
        logger.error(f"[INTELLIGENT_SELECTOR] LLM selection failed: {e}")
        # Graceful fallback response
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "data": {},
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Something went wrong while creating the test plan. Please retry or modify your parameters.",
        }

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
    }

    response_format = {
        "status": status.HTTP_200_OK,
        "data": response,
        "status_code": status.HTTP_200_OK,
        "message": "success",
    }

    logger.success(f"[INTELLIGENT_SELECTOR] Completed successfully — returning {len(selected_cases)} testcases")
    return response_format