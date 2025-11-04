from typing import List, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from loguru import logger


class ClarificationQuestionInput(BaseModel):
    question: str = Field(..., description="The clarifying question to ask the user")
    options: Optional[List[str]] = Field(None, description="List of possible options for the user to choose from")
    reason: Optional[str] = Field(None, description="Reason for asking this question")


@tool(args_schema=ClarificationQuestionInput, description="Ask the user a clarifying question when information is missing or ambiguous")
def ask_clarification_question(
    question: str,
    options: Optional[List[str]] = None,
    reason: Optional[str] = None
) -> str:
    """
    Ask the user a clarifying question when information is missing or ambiguous.
    
    This tool allows the LLM to dynamically ask questions to the user instead of 
    relying on hardcoded parameter checking logic.
    
    Args:
        question: The clarifying question to ask the user
        options: List of possible options for the user to choose from
        reason: Reason for asking this question (for internal logging)
        
    Returns:
        A formatted string that will be processed by the frontend to display 
        the question to the user
    """
    logger.info(f"[CLARIFICATION_TOOL] Asking question: {question}")
    if reason:
        logger.info(f"[CLARIFICATION_TOOL] Reason: {reason}")
    
    # Format the response for the frontend
    response = {
        "type": "clarification",
        "question": question,
        "options": options or [],
        "reason": reason
    }
    
    # Convert to string representation that can be parsed by frontend
    return f"CLARIFICATION_NEEDED: {question}" + (f" Options: {', '.join(options)}" if options else "")