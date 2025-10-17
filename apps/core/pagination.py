import math
from rest_framework.views import Response
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from collections import OrderedDict
from rest_framework import status


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
