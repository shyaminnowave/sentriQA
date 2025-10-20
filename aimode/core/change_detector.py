# from typing import List, Dict
# from loguru import logger
# from aimode.core.llms import embeddings

# # In-memory store for the last query per session
# LAST_QUERY_CACHE: Dict[str, str] = {}

# class QueryChangeDetector:
#     """
#     Detects major changes between consecutive queries using embeddings.
#     Supports in-memory last-query cache and user 'no save' instructions.
#     """

#     def __init__(self, similarity_threshold: float = 0.7):
#         self.similarity_threshold = similarity_threshold

#     def should_save_version(self, current_query: str, session_id: str) -> bool:
#         """
#         Determine if the current query should create a new version.
#         """
#         logger.info(f"Evaluating query for session {session_id}: {current_query}...")

#         # Check if user explicitly requested no save
#         user_no_save = self._user_requested_no_save(current_query)
#         if user_no_save:
#             logger.info("User requested not to save this query. Skipping version creation.")
#             LAST_QUERY_CACHE[session_id] = current_query  # Update cache anyway
#             return False

#         # Compare with last query in memory
#         last_query = LAST_QUERY_CACHE.get(session_id)
#         if last_query:
#             logger.info(f"Last query (n-1th) for session {session_id}: {last_query}...")
#             sim_score = self._calculate_similarity(current_query, last_query)
#             logger.info(f"Similarity with last query: {sim_score:.3f} (threshold {self.similarity_threshold})")
#             is_major = sim_score < self.similarity_threshold
#             if is_major:
#                 logger.info("Major change detected.")
#             else:
#                 logger.info("Minor change detected.")
#         else:
#             logger.info("No previous query in memory. Treating as major change.")
#             is_major = True

#         # Update last query cache
#         LAST_QUERY_CACHE[session_id] = current_query

#         return is_major

#     def _user_requested_no_save(self, query: str) -> bool:
#         """
#         Detect phrases indicating user does not want this query saved.
#         """
#         no_save_phrases = [
#             "don't save", "do not save", "dont save",
#             "no save", "don't store", "do not store",
#             "dont store", "no store", "don't record",
#             "do not record", "dont record", "no record"
#         ]
#         result = any(phrase in query.lower() for phrase in no_save_phrases)
#         if result:
#             logger.info("Detected user instruction to not save query.")
#         return result

#     def _calculate_similarity(self, query1: str, query2: str) -> float:
#         """
#         Calculate cosine similarity between two queries using embeddings.
#         """
#         try:
#             emb1 = embeddings.embed_query(query1)
#             emb2 = embeddings.embed_query(query2)
#             sim = self._cosine_similarity(emb1, emb2)
#             logger.debug(f"Embedding similarity: {sim:.3f}")
#             return sim
#         except Exception as e:
#             logger.error(f"Embedding similarity failed: {e}")
#             return 0.0  # Treat as fully different if embeddings fail

#     @staticmethod
#     def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
#         dot = sum(a * b for a, b in zip(vec1, vec2))
#         mag1 = sum(a * a for a in vec1) ** 0.5
#         mag2 = sum(b * b for b in vec2) ** 0.5
#         if mag1 == 0 or mag2 == 0:
#             return 0.0
#         return dot / (mag1 * mag2)

# change_detector = QueryChangeDetector()

# def detect_major_changes(current_query: str, session_id: str) -> bool:
#     """
#     Convenience function for external use.
#     Returns True if major change detected.
#     """
#     return change_detector.should_save_version(current_query, session_id)

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

    def should_save_version(self, current_query: str, session_id: str) -> bool:
        """
        Decide if the current query warrants a new version.
        """
        logger.info(f"Evaluating query for session {session_id}: {current_query[:50]}...")

        # Check if user requested no save
        if self._user_requested_no_save(current_query):
            logger.info("User requested not to save this query. Skipping version creation.")
            LAST_QUERY_CACHE[session_id] = current_query
            return False

        # Fetch last query
        last_query = LAST_QUERY_CACHE.get(session_id)
        if last_query:
            logger.info(f"Last query (n-1th) for session {session_id}: {last_query[:50]}...")

            # Let LLM decide if major change
            is_major = self._llm_decide_major_change(last_query, current_query)
        else:
            logger.info("No previous query in memory. Treating as major change.")
            is_major = True

        # Update cache
        LAST_QUERY_CACHE[session_id] = current_query
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
            logger.info(f"LLM decision on major change: {answer} -> {is_major}")
            return is_major
        except Exception as e:
            logger.error(f"LLM failed to decide major change: {e}")
            return True  # Default to save if LLM fails


# Global instance
change_detector = QueryChangeDetectorLLM()

def detect_major_changes(current_query: str, session_id: str) -> bool:
    return change_detector.should_save_version(current_query, session_id)