import django_filters
from django.db.models import Q
from apps.core.models import TestCaseMetric, TestCaseModel, Module


class TestcaseFilter(django_filters.rest_framework.FilterSet):

    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    priority = django_filters.CharFilter(method='filter_priority')
    testcase_type = django_filters.CharFilter(method='filter_testcase_type')
    feature = django_filters.CharFilter(method='filter_feature')

    class Meta:
        model = TestCaseModel
        fields = ['name', 'priority', 'testcase_type', 'feature']

    def filter_priority(self, queryset, name, value):
        print('value', value)
        if ',' in value:
            priorities = value.split(',')
            return queryset.filter(priority__in=priorities)
        return queryset.filter(priority__iexact=value)
    
    def filter_testcase_type(self, queryset, name, value):
        if ',' in value:
            types = value.split(',')
            return queryset.filter(testcase_type__in=types)
        return queryset.filter(testcase_type__icontains=value)
    
    def filter_feature(self, queryset, name, value):
        print('value_feature', value)
        names = []
        ids = []
        if ',' in value:
            features = value.split(',')
            for item in features:
                if item.isdigit():
                    ids.append(int(item))
                else:
                    names.append(item)
            if names:
                return queryset.filter(module__name__in=names)
            if ids:
                return queryset.filter(module__name__in=ids)
        else:
            if names:
                return queryset.filter(module__name__icontains=value)
            if ids:
                return queryset.filter(module__name__icontains=value)
        return queryset.filter(module__name__icontains=value)