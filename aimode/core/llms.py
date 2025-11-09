from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
import os
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", None)
OPENAI_CHAT_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", None)
OPENAI_EMBEDDING_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", None)

_llm = None
_embeddings = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = AzureChatOpenAI(
            azure_endpoint=OPENAI_ENDPOINT, 
            openai_api_version=OPENAI_API_VERSION,  
            deployment_name=OPENAI_CHAT_DEPLOYMENT_NAME,
            openai_api_key=OPENAI_API_KEY,
            temperature=0.2
        )
        logger.success('LLM Initialized')
    return _llm

def get_embeddings():
    global _embeddings
    if _embeddings is None and OPENAI_EMBEDDING_DEPLOYMENT_NAME:
        try:
            _embeddings = AzureOpenAIEmbeddings(
                azure_endpoint=OPENAI_ENDPOINT,
                openai_api_key=OPENAI_API_KEY,
                azure_deployment=OPENAI_EMBEDDING_DEPLOYMENT_NAME,
                openai_api_version=OPENAI_API_VERSION
            )
            logger.success('Embeddings model initialized')
        except Exception as e:
            logger.warning(f"Could not initialize embeddings model: {e}")
            logger.warning("Falling back to simple similarity methods")
            _embeddings = None
    return _embeddings

llm = get_llm()
embeddings = get_embeddings()
