import openpyxl
from django.http import HttpResponse
from rest_framework import generics, viewsets
from rest_framework.generics import CreateAPIView, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.core.models import TestCaseMetric, TestCaseModel, Module, TestPlan, PriorityChoice, HistoryTestPlan
from apps.core.utils import TestcaseImportExcel, DemoExcelFileFactory
from apps.core.apis.serializers import TestcaseListSerializer, TestCaseSerializer, FileUploadSerializer, \
    TestMetrixSerializer, TestSerializer, ModuleSerializer, TestPlanSerializer, TestScoreSerializer, \
    TestCaseNameSerializer, CreateTestPlanSerializer, TestPlanningSerializer, PlanSerializer, TestCaseOptionSerializer, \
    TestCaseScoreSerializer, SearchSerializer, PlanHistorySerializer, MetrixSerializer, HistroryPlanDetailsSerializer
from sentriQA.helpers.custom_generics import CustomGenericsAPIView as cgenerics
from apps.core.utils import QueryHelpers
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from apps.core.pagination import CustomPagination, CustomPageNumberPagination
from apps.core.apis.serializers import AITestPlanSerializer
from sentriQA.helpers.renders import ResponseInfo
from aimode.chatbot import get_llm_response
from apps.core.helpers import generate_score


@extend_schema(tags=["Modules List API"])
class ModuleAPIView(generics.ListAPIView):

    serializer_class = ModuleSerializer
    queryset = Module.objects.all()


@extend_schema(tags=["Testcase List API"])
class TestCaseList(generics.ListAPIView):

    pagination_class = CustomPagination
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


@extend_schema(tags=["Testcase Excel Upload API"])
class FileUploadView(APIView):

    def __init__(self, **kwargs):
        self.response_format = ResponseInfo().response
        super().__init__(**kwargs)  

    serializer_class = FileUploadSerializer

    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            instance = TestcaseImportExcel(self.request.data['file'])
            upload_status = instance.import_data()
            if instance and upload_status:
                self.response_format['status'] = True
                self.response_format['status_code'] = status.HTTP_200_OK
                self.response_format['message'] = "File Uploaded Successfully"
                self.response_format['data'] = upload_status
                return Response(self.response_format, status=status.HTTP_200_OK)
            else:
                self.response_format['status'] = False
                self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
                self.response_format['message'] = "Error While Uploading the File"
                self.response_format['data'] = upload_status
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.response_format['status'] = False
        self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
        self.response_format['message'] = serializer.errors
        self.response_format['data'] = None
        return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Testcase Plan Creation API"])
class TestPlanningView(generics.GenericAPIView):
    serializer_class = TestPlanSerializer

    def post(self, request, *args, **kwargs):
        serializer = TestPlanSerializer(data=request.data)
        if serializer.is_valid():
            score = generate_score(request.data)
            if score:
                return Response(score, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "data": None,
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "No Testcase Found for this Criteria"
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateTestPlanView(generics.GenericAPIView):
    serializer_class = CreateTestPlanSerializer

    def post(self, request, *args, **kwargs):
        # try:
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
                "message": serializer.errors
            }
            return Response(response_format, status=status.HTTP_400_BAD_REQUEST)
        # except Exception as e:
        #     response_format = {
        #         "status": status.HTTP_400_BAD_REQUEST,
        #         "data": None,
        #         "status_code": status.HTTP_400_BAD_REQUEST,
        #         "message": str(e),
        #     }
        #     return Response(response_format, status=status.HTTP_400_BAD_REQUEST)


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


class TestcaseOptionAPI(generics.GenericAPIView):

    serializer_class = MetrixSerializer

    def get_queryset(self):
        search = self.request.query_params.get('search', None)
        if search:
            search_filers =  Q(testcase__name__icontains=search) | Q(testcase__module__name__icontains=search) | Q(testcase__testcase_type__icontains=search) | Q(testcase__priority__icontains=search)
            if search.isdigit():
                search_filers |= Q(testcase__id__exact=search)
            queryset = TestCaseMetric.objects.select_related('testcase').filter(
                search_filers
            ).distinct()
        else:
            queryset = []
        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        if serializer.data:
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)


class TestcaseScore(generics.GenericAPIView):

    serializer_class = TestCaseScoreSerializer

    def get_queryset(self):
        testcase_metrix = TestCaseMetric.objects.filter(testcase__id__in=self.kwargs['pk'])
        return testcase_metrix

    def post(self, request, *args, **kwargs):
        serializer = TestMetrixSerializer(data=self.queryset(), many=True)
        if serializer.data:
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)


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
        print(queryset)
        return queryset
    
    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object(), data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConvertAPIView(APIView):

    def get_modules(self, modules):
        if modules:
            modules = Module.objects.filter(name__in=modules).values('id', 'name')
            return list(modules)
        return []

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            modules = request.data.get('module') if request.data.get('module') else []
            name = request.data.get('name') if 'name' in request.data else ""
            description = request.data.get('description') if 'description' in request.data else ""
            priority = request.data.get('priority') if 'priority' in request.data else ""
            response_format = {
                "status": "Success",
                "data": {
                    "name": name,
                    "description": description,
                    "priority": priority,
                    "modules": self.get_modules(modules),
                },
                "status_code": status.HTTP_200_OK,
                "message": "Success"
            }
            return Response(
                response_format,
                status=status.HTTP_200_OK
            )
        return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "data": None,
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "ERROR"
            }, status=status.HTTP_400_BAD_REQUEST)
    

class TestPlanHistroryView(generics.ListAPIView):

    serializer_class = PlanHistorySerializer

    def get_queryset(self):
        testplan_id = self.kwargs['id']
        queryset = HistoryTestPlan.objects.filter(testplan_id=testplan_id).order_by('-created')
        return queryset
    
    def list(self, request, *args, **kwargs):
        try:
            response = super().list(request, *args, **kwargs)
            if response.status_code == status.HTTP_200_OK and response.data:
                response_format = {
                    "status": status.HTTP_200_OK,
                    "data": response.data,
                    "status_code": status.HTTP_200_OK,
                    "message": "success",
                }
                return Response(response_format, status=status.HTTP_200_OK)
            else:
                response_format = {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "data": None,
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "No data Found",
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
        
    

class HistoryPlanDetailsView(generics.RetrieveAPIView):

    serializer_class = HistroryPlanDetailsSerializer

    def get_object(self):
        queryset = HistoryTestPlan.objects.get(id=self.kwargs['history_id'])
        return queryset
    
    def get(self, request, *args, **kwargs):
        try:
            response = super().get(request, *args, **kwargs)
            if response.status_code == status.HTTP_200_OK:
                response_format = {
                    "status": status.HTTP_200_OK,
                    "data": response.data,
                    "status_code": status.HTTP_200_OK,
                    "message": "success",
                }
                return Response(response_format, status=status.HTTP_200_OK)
            else:
                response_format = {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "data": None,
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "No data Found",
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


class TestingView(APIView):

    def post(self, request, *args, **kwargs):
        serializer = TestPlanSerializer(data=request.data)
        if serializer.is_valid():
            score = generate_score(request.data)
            return Response(score, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
