from abc import ABC, abstractmethod
import pandas as pd
from django.db import transaction
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from openpyxl import load_workbook
from apps.core.helpers import QueryHelpers
from apps.core.models import TestCaseModel, TestCaseMetric


class FileFactory(ABC):

    @abstractmethod
    def import_data(self):
        pass


class ExcelFileFactory(FileFactory):
    """Base factory class to handle Excel file operations."""

    def __init__(self, file):
        self.response_format = {
            "status": True,
            "status_code": HTTP_200_OK,
            "data": "",
            "message": ""
        }
        self.file = file

    def _init_workbook(self):
        """Initialize the workbook and return the active sheet."""
        workbook = load_workbook(self.file)
        return workbook.active

    def import_data(self):
        pass


class TestcaseImportExcel(ExcelFileFactory):

    def __init__(self, file):
        super().__init__(file)
        self.ws = self._init_workbook()

    def _build_error_response(self, error):
        self.response_format.update({
            "status": False,
            "status_code": HTTP_400_BAD_REQUEST,
            "message": str(error),
        })
        return self.response_format

    def _build_success_response(self, message):
        self.response_format.update({
            "data": "Success",
            "message": message,
        })
        return self.response_format

    @staticmethod
    def get_priority(name):
        match name:
            case 'Class 1':
                return 'class_1'
            case 'Class 2':
                return 'class_2'
            case 'Class 3':
                return 'class_3'
        return False


    # def import_data(self):
    #     try:
    #         current_module = None
    #         lst = []
    #         matrix = []
    #         for row in self.ws.iter_rows(
    #             min_row=2,
    #             values_only=True,
    #         ):
    #             if current_module != row[0]:
    #                 current_module = QueryHelpers.get_module_instance(row[0])
    #             _temp = {
    #                 "name": row[3],
    #                 "priority": self.get_priority(row[8]),
    #                 "status": "completed",
    #                 "module": current_module,
    #             }
    #             _matrix = {
    #                         "testcase": row[3],
    #                         "likelihood": row[4],
    #                         "impact": row[7],
    #                         "failure_rate": row[9],
    #                         "failure": row[10],
    #                         "total_runs": row[11],
    #                         "direct_impact": row[12],
    #                         "defects": row[14],
    #                         "severity": 0,
    #                         "feature_size": 0,
    #                         "execution_time": row[15]
    #                     }
    #     except Exception as e:
    #         print(e)

    @staticmethod
    def get_failure_rate(failure, total_runs):
        if failure and total_runs:
            return (failure / total_runs) * 100
        else:
            return 0


    def import_data(self):
        try:
            current_module = None
            lst = []
            matrix = []
            for row in self.ws.iter_rows(
                min_row=2, values_only=True
            ):
                if row[1] is not None:
                    current_module = QueryHelpers.get_module_instance(row[2])
                _temp = {
                    "name": row[1],
                    "priority": self.get_priority(row[7]),
                    "status": "completed",
                    "module": current_module,
                }
                lst.append(TestCaseModel(**_temp))
                _matrix = {
                    "testcase": row[1],
                    "likelihood": row[4],
                    "impact": row[6],
                    "failure_rate": round(self.get_failure_rate(row[10], row[11])),
                    "failure": row[10],
                    "total_runs": row[11],
                    "direct_impact": row[12],
                    "defects": row[14],
                    "severity": 0,
                    "feature_size": 0,
                    "execution_time": row[15]
                }
                matrix.append(_matrix)
            TestCaseModel.objects.bulk_create(lst)
            for i in range(len(matrix)):
                matrix[i]['testcase'] = QueryHelpers.get_test_case_instance(matrix[i]['testcase'])
                matrix[i] = TestCaseMetric(**matrix[i])

            with transaction.atomic():
                TestCaseMetric.objects.bulk_create(matrix)
            return True
        except Exception as e:
            print(e)
            return False

