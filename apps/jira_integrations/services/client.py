import time
import hashlib
import requests
from enum import Enum
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, TypeVar, Generic
from dataclasses import dataclass, field
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from abc import ABCMeta, abstractmethod


class AuthType(Enum):
    """Supported authentication types"""
    BEARER_TOKEN = "bearer"
    API_KEY = "api_key"
    BASIC_AUTH = "basic"
    OAUTH2 = "oauth2"
    CUSTOM_HEADER = "custom_header"


@dataclass
class APIClientConfig:

    name: str
    base_url: str
    auth_config: str
    timeout: int


class ApiHTTPClient:

    """
    Universal client for interacting with JIRA, Confluence, X-Ray
    """

    def __init__(self, config: APIClientConfig):
        self.config = config

    def headers(self):
        return {
            "Content-Type": "application/json",
        }

    def request(self, method, endpoint, params, data, headers, json_data) -> requests.Response:
        pass

    def get(self, endpoint, params, data, headers, json_data) -> requests.Response:
        pass

    def post(self, endpoint, params, data, headers, json_data) -> requests.Response:
        pass

    def put(self, endpoint, params, data, headers, json_data) -> requests.Response:
        pass

    def patch(self, endpoint, params, data, headers, json_data) -> requests.Response:
        pass

    def delete(self, endpoint, params, data, headers, json_data) -> requests.Response:
        pass