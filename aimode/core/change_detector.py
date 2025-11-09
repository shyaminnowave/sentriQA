"""
Detects major changes between consecutive queries using LLM reasoning, 'no save' instructions and caches last query per session.
"""
from typing import Dict
from loguru import logger
from aimode.core.llms import llm

# In-memory store for the last query per session
LAST_QUERY_CACHE: Dict[str, str] = {}

class QueryChangeDetectorLLM:
    def should_save_version(self, current_query: str, session_id) -> bool:
        if session_id is None:
            logger.warning("No session_id provided to change detector!")
            session_id = "unknown_session"
        session_id_str = str(session_id).strip().lower()

        logger.info(f"Evaluating query for session {session_id_str}: {current_query[:50]}...")

        if self._user_requested_no_save(current_query):
            logger.info("User requested not to save this query. Skipping version creation.")
            LAST_QUERY_CACHE[session_id_str] = current_query
            return False

        last_query = LAST_QUERY_CACHE.get(session_id_str)
        if last_query:
            logger.info(f"Last query (n-1th) for session {session_id_str}: {last_query[:50]}...")
            is_major = self._llm_decide_major_change(last_query, current_query)
        else:
            logger.info(f"No previous query in memory for session {session_id_str}. Treating as major change.")
            is_major = True

        LAST_QUERY_CACHE[session_id_str] = current_query
        logger.info(f"Updated LAST_QUERY_CACHE for session {session_id_str}")

        return is_major

    def _user_requested_no_save(self, query: str) -> bool:
        no_save_phrases = [
            "don't save", "do not save", "dont save",
            "no save", "don't store", "do not store",
            "dont store", "no store", "don't record",
            "do not record", "dont record", "no record"
        ]
        result = any(phrase in query.lower() for phrase in no_save_phrases)
        if result:
            logger.info("Detected user instruction to not save query.")
        return result

    def _llm_decide_major_change(self, last_query: str, current_query: str) -> bool:
        try:
            from aimode.core.prompts import CHANGE_DETECTION_PROMPT
            prompt = CHANGE_DETECTION_PROMPT.format_messages(
                last_query=last_query,
                current_query=current_query
            )
            response = llm.invoke(prompt)
            answer = response.content.strip().upper()
            is_major = answer.startswith("YES")
            logger.info(f"LLM decision on major change: {answer} -> {is_major}")
            return is_major
        except Exception as e:
            logger.error(f"LLM failed to decide major change: {e}")
            return False 

# Global instance
change_detector = QueryChangeDetectorLLM()

def detect_major_changes(current_query: str, session_id: str) -> bool:
    return change_detector.should_save_version(current_query, session_id)