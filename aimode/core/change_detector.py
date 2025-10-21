from typing import Dict
from loguru import logger
from aimode.core.llms import llm

# In-memory store for the last query per session
LAST_QUERY_CACHE: Dict[str, str] = {}

class QueryChangeDetectorLLM:
    """
    Detects major changes between consecutive queries using LLM reasoning.
    Respects user 'no save' instructions and caches last query per session.
    """

    def should_save_version(self, current_query: str, session_id) -> bool:
        """
        Decide if the current query warrants a new version.
        """
        # Ensure session_id is a string and normalized
        if session_id is None:
            logger.warning("No session_id provided to change detector!")
            session_id = "unknown_session"
        session_id_str = str(session_id).strip().lower()

        logger.info(f"[ChangeDetector] Evaluating query for session {session_id_str}: {current_query[:50]}...")

        # Check if user requested no save
        if self._user_requested_no_save(current_query):
            logger.info("[ChangeDetector] User requested not to save this query. Skipping version creation.")
            LAST_QUERY_CACHE[session_id_str] = current_query
            return False

        # Fetch last query from cache
        last_query = LAST_QUERY_CACHE.get(session_id_str)
        if last_query:
            logger.info(f"[ChangeDetector] Last query (n-1th) for session {session_id_str}: {last_query[:50]}...")
            # Let LLM decide if major change
            is_major = self._llm_decide_major_change(last_query, current_query)
        else:
            logger.info(f"[ChangeDetector] No previous query in memory for session {session_id_str}. Treating as major change.")
            is_major = True

        # Update cache with current query
        LAST_QUERY_CACHE[session_id_str] = current_query
        logger.info(f"[ChangeDetector] Updated LAST_QUERY_CACHE for session {session_id_str}")

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
            logger.info("[ChangeDetector] Detected user instruction to not save query.")
        return result

    def _llm_decide_major_change(self, last_query: str, current_query: str) -> bool:
        """
        Ask the LLM whether the current query differs enough from last query.
        Returns True if major change, False otherwise.
        """
        try:
            from aimode.core.prompts import CHANGE_DETECTION_PROMPT
            prompt = CHANGE_DETECTION_PROMPT.format_messages(
                last_query=last_query,
                current_query=current_query
            )
            response = llm.invoke(prompt)
            answer = response.content.strip().upper()
            is_major = answer.startswith("YES")
            logger.info(f"[ChangeDetector] LLM decision on major change: {answer} -> {is_major}")
            return is_major
        except Exception as e:
            logger.error(f"[ChangeDetector] LLM failed to decide major change: {e}")
            return True  # Default to save if LLM fails



# Global instance
change_detector = QueryChangeDetectorLLM()

def detect_major_changes(current_query: str, session_id: str) -> bool:
    return change_detector.should_save_version(current_query, session_id)
