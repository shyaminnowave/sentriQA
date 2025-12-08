import math
from rest_framework.views import Response
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from collections import OrderedDict
from rest_framework import status
from urllib.parse import quote
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def replace_query_param(url, key, val):
    """
    Given a URL and a key/val pair, set or replace an item in the query
    parameters of the URL, and return the new URL.
    """
    (scheme, netloc, path, params, query, fragment) = urlparse(url)
    query_dict = parse_qs(query, keep_blank_values=True)
    query_dict[key] = [val]
    query = urlencode(sorted(query_dict.items()), doseq=True)
    return urlunparse((scheme, netloc, path, params, query, fragment))


class TestCasePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def remove_last_path_segment(self, url: str) -> str:
        path = str(url)
        us = path.split('?') if '?' in path else [path]
        if 'http://127.0.0.1:8000/api/' in us[0]:
            return "http://127.0.0.1:8000/api/?" + us[-1]
        return "https://sentri-qa-hea4embscubaejaw.eastasia-01.azurewebsites.net/api/?" + us[-1]

    def get_module(self, value):
        if value is None:
            return ""

        module = value.get('module', "")
        print("module:", module, type(module))

        # Correct check
        if isinstance(module, list):
            return ",".join(module)

        return module

    def get_testcase_type(self, value):
        if value is None:
            return ""

        testcase_type = value.get('testcase_type', "")
        print("testcase_type:", testcase_type, type(testcase_type))

        if isinstance(testcase_type, list):
            return ",".join(testcase_type)

        return testcase_type

    def get_priority(self, value):
        if value is None:
            return ""

        priority = value.get('priority', "")
        print("priority:", priority, type(priority))

        # Correct check
        if isinstance(priority, list):
            return ",".join(priority)

        return priority

    def get_next_page(self, value):
        params = {}
        module = self.get_module(value)
        testcase_type = self.get_testcase_type(value)
        priority = self.get_priority(value)
        if module:
            params['feature'] = module
        if testcase_type:
            params['testcase_type'] = testcase_type
        if priority:
            params['priority'] = priority
        return "&".join(f"{k}={v}" for k, v in params.items())


    def get_paginated_response(self, data, filter_value):
        response = super().get_paginated_response(data)
        page_count = math.ceil(response.data.get('count')/self.page_size)
        base_url = f"{self.request.scheme}://{self.request.get_host()}"
        filter_query = self.get_next_page(filter_value)
        get_next = self.get_next_link() if self.get_next_link() else None
        new_url = self.remove_last_path_segment(url=get_next)
        get_prev = self.get_previous_link() if self.get_previous_link() else None
        new_prev = self.remove_last_path_segment(url=get_prev)
        next_page = f"{new_url}&{filter_query}" if get_next else None
        prev_page = f"{new_prev}&{filter_query}" if get_prev else None
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'page_count': page_count,
            'current_page': self.page.number,
            'page_size': self.page_size,
            'status': True,
            'status_code': status.HTTP_200_OK,
            'message': 'Success',
            'data': data
        })

class CustomPagination(PageNumberPagination):
    
    page_size = 10
    page_query_param = 'page'

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        page_count = math.ceil(response.data.get('count') / self.page_size)
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', response.data.get('next')),
            ('previous', response.data.get('previous')),
            ('page_count', page_count),
            ('status', True),
            ('status_code', status.HTTP_200_OK),
            ('message', 'Success'),
            ('data', data)
        ]))


class CustomLimitOffsetPagination(LimitOffsetPagination):

    def get_paginated_response(self, data):
        response = super(CustomLimitOffsetPagination, self).get_paginated_response(data)
        return Response({
            'count': self.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'data': data,
            'status': True,
            'status_code': status.HTTP_200_OK,
            'message': 'Success',
            'page_count': self.get_limit(self.request),
        })
