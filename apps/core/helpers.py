import uuid
from datetime import datetime
from jsonschema import ValidationError
from rest_framework.generics import get_object_or_404
from django.http import Http404
from apps.core.models import TestCaseModel, Module, TestCaseMetric, Project, AISessionStore, TestPlanSession, TestScore, \
    TestCaseScoreModel
from django.db.models import Q
from django.utils.crypto import get_random_string
from apps.core.testscore import TestCaseScore
from rest_framework import status
from .datacls import Session


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
    def get_project_by_id(name: str):
        instance, created = Project.objects.get_or_create(name='nature')
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
            return instance if instance else False
        except Http404 as err:
            return False
        except Exception as e:
            return False
        
    @staticmethod
    def get_project_inst(name):
        try:
            instance = get_object_or_404(
                Project, name=name
            )
            return instance
        except Http404 as err:
            return False
        except Exception as e:
            return False
        

def generate_session_id():
    try:
        instance = AISessionStore.objects.create()
        return instance.session_id
    except Exception as e:
        print(str(e))
        return False
    
def format_datetime(dt_string):
    return dt_string.strftime('%B %d, %Y')


def get_priority_repr(obj):
    parts = obj.split('_')
    return parts[0].capitalize() + " " + parts[1]


def save_score(data=None):
    testcase_lst = []
    print('inside')
    if data is None:
        print('ud')
        queryset = TestCaseMetric.objects.all()
        for testcase in queryset:
            if not TestCaseScoreModel.objects.filter(testcase__id=testcase.id).exists():
                testcase_lst.append(testcase)
        if testcase_lst:
            score_obj = TestCaseScore()
            score = score_obj.calculate_scores(testcase_lst)
            for sc in score:
                print(sc)
    else:
        testcase_ids = [tc.id for tc in data]
        queryset = TestCaseMetric.objects.filter(testcase__id__in=testcase_ids)
        print('inside')
        score = score_obj.calculate_scores(queryset)
        for sc in score:
            "testing"
            print(sc)
    return True


def generate_score(data):
    queryset = TestCaseMetric.objects.filter(
                Q(testcase__module__id__in=data.get('module'))  &
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
            "project": data.get('project'),
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


def get_prev_version(session):
    try:
        instance = TestPlanSession.objects.filter(session=session).order_by('-created').first()
        if instance:
            setattr(instance, 'status', 'draft')
            instance.save()
        return None
    except Exception as e:
        return None


def save_version(data):
    try:
        session_data = Session(**data)
        data = session_data.model_dump()
    except Exception as e:
        print(str(e))
    session = data.pop('session')
    modules = data.pop('modules')
    status = data.pop('status') if data.pop('status') else 'saved'
    get_modules = Module.objects.filter(name__in=modules)
    try:
        get_session = AISessionStore.objects.get(session_id=session)
    except AISessionStore.DoesNotExist:
        return False
    if get_session:
        get_prev_version(get_session)
        instance = TestPlanSession.objects.create(session=get_session, status=status, **data)
        instance.modules.set(get_modules)
        return instance
    return False
