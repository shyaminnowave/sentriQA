from rest_framework.generics import get_object_or_404
from django.http import Http404
from apps.core.models import TestCaseModel, Module, TestCaseMetric
from django.db.models import Q
from apps.core.testscore import TestCaseScore
from rest_framework import status


class QueryHelpers:

    @staticmethod
    def get_module_by_id(id: int):
        obj = get_object_or_404(
            Module,
            id=id
        )
        return obj.name if obj is not None else None

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
            return False
        except Exception as e:
            return False
        
    @staticmethod
    def check_testcase_exists(name):
        try:
            if name == "":
                return False
            instance = get_object_or_404(TestCaseModel, Q(name=name))
            return True if instance else False
        except Http404 as err:
            return False
        except Exception as e:
            return False
        
    @staticmethod
    def check_matrix_id(testcase):
        try:
            instance = get_object_or_404(
                TestCaseMetric,
                Q(testcase__name=testcase)
            )
            return True if instance else False
        except Http404 as err:
            return False
        except Exception as e:
            return False


def generate_score(data):
    queryset = TestCaseMetric.objects.filter(
                Q(testcase__module__in=data.get('module'))  &
                Q(testcase__testcase_type='functional')
            )
    module__name = Module.objects.filter(
        id__in=data.get('module')
    ).values_list('name', flat=True)
    results = []
    if queryset is not None:
        score_obj = TestCaseScore()
        score = score_obj.calculate_scores(queryset)
        output_counts = data.get('output_counts', 0)
        if len(score) > output_counts:
            score = score[:output_counts]
        for match in score:
            # Convert to appropriate data types
            result = {
                "id": match.testcase_id,
                "testcase": str(match.testcase_name),
                "modules": str(match.module),
                "mode": "ai",
                "generated": True,
                "priority": str(match.priority),
                "testscore": float(match.total_score),
            }
            results.append(result)
    response = {
            "name": data.get('name', ""),
            "description": data.get('description', ""),
            "modules": list(module__name),
            "output_counts": data.get('output_counts'),
            "priority": data.get('priority', 0),
            "generate_test_count": len(results) if results else "No testcase found for this Criteria",
            "testcase_type": data.get('testcase_type', "functional"),
            "testcases": results,
        }
    response_format = {
        "status": status.HTTP_200_OK,
        "data": response,
        "status_code": status.HTTP_200_OK,
        "message": "success",
    }
    return response_format
