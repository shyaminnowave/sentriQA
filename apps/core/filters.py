import django_filters
from apps.core.models import TestCaseMetric


class TestcaseFilter(django_filters.rest_framework.FilterSet):

    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    priority = django_filters.CharFilter(field_name='priority', lookup_expr='icontains')
    testcase_type = django_filters.CharFilter(field_name='testcase_type', lookup_expr='icontains')
    module = django_filters.CharFilter(field_name='module__name', lookup_expr='icontains')

    class Meta:
        model = TestCaseMetric
        fields = ['name', 'priority', 'testcase_type', 'module']