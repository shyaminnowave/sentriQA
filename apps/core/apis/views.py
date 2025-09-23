import openpyxl
from django.http import HttpResponse
from rest_framework import generics, viewsets
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.core.models import TestCaseMetric, TestCaseModel, Module, TestPlan, PriorityChoice
from apps.core.utils import TestcaseImportExcel
from apps.core.apis.serializers import TestcaseListSerializer, TestCaseSerializer, FileUploadSerializer, \
    TestMetrixSerializer, TestSerializer, ModuleSerializer, TestPlanSerializer, TestScoreSerializer, \
    TestCaseNameSerializer, CreateTestPlanSerializer, TestPlanningSerializer, PlanSerializer
from apps.core.utils import QueryHelpers
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from apps.core.apis.serializers import AITestPlanSerializer
from aimode.chatbot import get_llm_response

@extend_schema(tags=["Modules List API"])
class ModuleAPIView(generics.ListAPIView):

    serializer_class = ModuleSerializer
    queryset = Module.objects.all()


@extend_schema(tags=["Testcase List API"])
class TestCaseList(generics.ListAPIView):

    queryset = TestCaseModel.objects.all()
    serializer_class = TestcaseListSerializer


@extend_schema(tags=["Testcase Create API"])
class TestCaseView(generics.CreateAPIView):

    serializer_class = TestCaseSerializer

@extend_schema(tags=["Testcase Detail API"])
class TestCaseDetail(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = TestCaseSerializer

    def get_object(self):
        queryset = TestCaseModel.objects.get(slug=self.kwargs['slug']).select_related('testcase')
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Testcase Excel Upload API"])
class FileUploadView(APIView):

    serializer_class = FileUploadSerializer

    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            instance = TestcaseImportExcel(self.request.data['file'])
            out = instance.import_data()
            if instance:
                return Response(True)
            else:
                return Response(False)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Testcase Plan Creation API"])
class TestPlanningView(generics.GenericAPIView):
    serializer_class = TestPlanSerializer

    def post(self, request, *args, **kwargs):
        serializer = TestPlanSerializer(data=request.data)
        if serializer.is_valid():
            queryset = TestCaseMetric.objects.filter(
                Q(testcase__module__in=request.data['module'])  &
                Q(testcase__priority=request.data['priority']) &
                Q(testcase__testcase_type='functional')
            )[0:request.data['output_counts']]
            testcases = TestScoreSerializer(queryset, many=True)
            if queryset:
                response_format = {
                    "status": status.HTTP_200_OK,
                    "data": {
                        "name": serializer.data['name'] if serializer.data.get('name') else "",
                        "description": serializer.data['description'] if serializer.data.get('description') else "",
                        "module": serializer.data['module'],
                        "output_counts": request.data['output_counts'],
                        "priority": request.data['priority'],
                        "testcase_type": request.data["testcase_type"] if request.data.get('testcase_type') else 'functional',
                        "testcases": testcases.data if testcases.data else "No testcases Matching this Criteria",
                    },
                    "status_code": status.HTTP_200_OK,
                    "message": "success",
                }
                return Response(response_format, status=status.HTTP_200_OK)
            response_format = {
                "status": status.HTTP_200_OK,
                "data": {
                    "name": serializer.data['name'] if serializer.data.get('name') else "",
                    "description": serializer.data['description'] if serializer.data.get('description') else "",
                    "module": serializer.data['module'],
                    "output_counts": request.data['output_counts'],
                    "priority": request.data['priority'],
                    "testcase_type": request.data["testcase_type"] if request.data.get('testcase_type') else 'functional',
                    "testcases": "No testcases Found Matching this Criteria",
                },
                "status_code": status.HTTP_200_OK,
                "message": "success",
            }
            return Response(response_format, status=status.HTTP_200_OK)
        response_format = {
            "status": status.HTTP_400_BAD_REQUEST,
            "data": None,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": serializer.errors,
        }
        return Response(response_format, status=status.HTTP_400_BAD_REQUEST)



class CreateTestPlanView(generics.GenericAPIView):
    serializer_class = CreateTestPlanSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = CreateTestPlanSerializer(data=request.data)
            if serializer.is_valid():
                data = serializer.save()
                if data:
                    queryset = TestPlan.objects.get(id=data)
                    serializer = PlanSerializer(queryset)
                    response_format = {
                        "status": status.HTTP_200_OK,
                        "data": serializer.data,
                        "status_code": status.HTTP_200_OK,
                        "message": "success",
                    }
                    return Response(response_format, status=status.HTTP_201_CREATED)
                response_format = {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "data": None,
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": serializer.errors,
                }
                return Response(response_format, status=status.HTTP_400_BAD_REQUEST)
            response_format = {
                "status": status.HTTP_400_BAD_REQUEST,
                "data": None,
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "Error While Saving the TestPlan"
            }
            return Response(response_format, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response_format = {
                "status": status.HTTP_400_BAD_REQUEST,
                "data": None,
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": str(e),
            }
            return Response(response_format, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Classic Options API"])
class ClassicOptionAPI(APIView):

    def get(self, request, *args, **kwargs):
        # get_functionality = TestCaseModel.objects.values('testcase_type').distinct('testcase_type')
        get_priority = [{"id": value, "name": label} for value, label in PriorityChoice.choices]
        response_format = {
            "status": status.HTTP_200_OK,
            "data": {
                'testcase_type': [{
                    "id": "functional",
                    "name": "Functional",
                }],
                'priority': get_priority,
            },
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "Success",
        }
        return Response(response_format, status=status.HTTP_200_OK)


@extend_schema(tags=["AI Testcase Plan Creation API"])
class AITestPlanningView(generics.GenericAPIView):
    serializer_class = AITestPlanSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user_msg = serializer.validated_data['user_msg']
            session_id = serializer.validated_data['session_id']

            response_dict = get_llm_response(user_msg, session_id)


            return Response(response_dict, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


@extend_schema(tags=["Testcase Plan List API"])
class TestPlanView(APIView):

    serializer_class = TestMetrixSerializer

    def post(self, request, *args, **kwargs):
        modules = request.data.get('module')

        if not modules:
            return Response(
                {'error': 'module parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convert single module to list
        if not isinstance(modules, list):
            modules = [modules]

        queryset = TestCaseModel.objects.filter(module__name__in=modules)
        sub_query = TestCaseMetric.objects.filter(testcase__in=queryset)
        serializer = TestMetrixSerializer(sub_query, many=True)
        return Response(serializer.data)


@extend_schema(tags=["Testcase Score List API"])
class TestScores(APIView):

    def get(self, request, *args, **kwargs):
        queryset = TestCaseMetric.objects.all()
        serializer = TestMetrixSerializer(queryset, many=True)
        return Response(serializer.data)

@extend_schema(tags=["GetExcel API"])
class TestScoreExcel(APIView):

    def get(self, request, *args, **kwargs):
        wb = openpyxl.load_workbook('templates/Book_Test.xlsx')
        sheet = wb['Sheet1']
        row_num = 2
        for row in sheet.iter_rows(
            min_row=2, values_only=True,
        ):
            testcase_instance = QueryHelpers.get_test_case_instance(
                value=row[1]
            )
            try:
                _instance = TestCaseMetric.objects.get(testcase=testcase_instance)
                sheet.cell(row_num, column=17).value = round(_instance.get_test_scores())
                row_num += 1
            except Exception as e:
                print(e)
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="test_score.xlsx"'
        wb.save(response)
        return response


class GetScoreViewAPIView(generics.GenericAPIView):
    serializer_class = TestCaseNameSerializer

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            queryset = TestCaseMetric.objects.filter(testcase__name__in=request.data['testcase'])
            serializer = TestScoreSerializer(data=request.data)
            if serializer.is_valid():
                return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TestPlanView(generics.GenericAPIView):

    serializer_class = TestPlanningSerializer
    queryset = TestPlan.objects.all()

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            self.get_queryset(),
            many=True
        )
        if serializer.data:
            response_format = {
                "status": status.HTTP_200_OK,
                "data": serializer.data,
                "status_code": status.HTTP_200_OK,
                "message": "success",
            }
            return Response(response_format, status=status.HTTP_200_OK)
        else:
            response_format = {
                "status": status.HTTP_400_BAD_REQUEST,
                "data": None,
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": serializer.errors if serializer.errors else 'No data Found',
            }
            return Response(response_format, status=status.HTTP_400_BAD_REQUEST)


class PlanDetailsView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = PlanSerializer

    def get_object(self):
        queryset = TestPlan.objects.get(id=self.kwargs['id'])
        return queryset
