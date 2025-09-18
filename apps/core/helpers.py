from rest_framework.generics import get_object_or_404
from django.http import Http404
from apps.core.models import TestCaseModel, Module
from django.db.models import Q


class QueryHelpers:

    @staticmethod
    def get_module_instance(name):
        instance, created = Module.objects.get_or_create(name=name)
        return instance

    @staticmethod
    def get_test_case_instance(value):
        try:
            instance = get_object_or_404(TestCaseModel, Q(name=value))
            return instance
        except Http404 as err:
            print(err)
            return False
        except Exception as e:
            print(e)
            return False