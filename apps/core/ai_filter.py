from apps.core.models import TestCaseModel, TestCaseMetric, TestCaseScoreModel
from apps.core.apis.serializers import TestcaseListSerializer, TestcaseFilterSerializer
from apps.core.pagination import CustomPagination
from django.db.models import Q, Prefetch
from django.core.exceptions import ValidationError
import logging
from django.contrib.postgres import search

logger = logging.getLogger(__name__)


def get_filtered_data(data):
    """
    param = {
                "feature/module": ["", ],
                "testcase_type": ["",],
                "priority": ["",],
            }
    """
    print('filter', data)
    logger.info(f"get_filtered_data: {data}")

    logger.info('Entered the Filter Function')
    module = data.get('module', [])
    testcase_type = data.get('testcase_type', [])
    priority = data.get('priority', [])
    try:
        queryset = (
            TestCaseModel.objects
            .select_related('module')
            .prefetch_related(
                Prefetch('metrics', queryset=TestCaseMetric.objects.all(), to_attr='prefetched_metrics'),
                Prefetch('scores', queryset=TestCaseScoreModel.objects.all(), to_attr='prefetched_scores')
            )
        )
        if module:
            if isinstance(module, list):
                queryset &= queryset.filter(module__name__in=module)
            else:
                queryset &= queryset.filter(module__name=module)

        if testcase_type:
            if isinstance(testcase_type, list):
                queryset &= queryset.filter(testcase_type__in=testcase_type)
            else:
                queryset &= queryset.filter(testcase_type=testcase_type)
        if priority:
            if isinstance(priority, list):
                queryset &= queryset.filter(priority__in=priority)
            else:
                queryset &= queryset.filter(priority=priority)
        if queryset:
            data = TestcaseFilterSerializer(queryset, many=True)
            return {
                "test_repo": True,
                "tcs": data.data
            }
        else:
            return {
                    "test_repo": False,
                    "tcs": {}
                }

        # queryset = TestCaseModel.objects.select_related('module').prefetch_related(
        #     Prefetch('metrics', queryset=TestCaseMetric.objects.only('likelihood',
        #                                                              'impact',
        #                                                              'failure_rate',
        #                                                              'failure',
        #                                                              'total_runs',
        #                                                              'direct_impact',
        #                                                              'defects',
        #                                                              'severity',
        #                                                              'feature_size',
        #                                                              'execution_time')),
        #     Prefetch('scores', queryset=TestCaseScoreModel.objects.only('score'))
        # )
        # filters = Q()
        # if module:
        #     if isinstance(module, list):
        #         filters &= Q(module__name__in=module)
        #     else:
        #         filters &= Q(module__name=module)
        # if testcase_type:
        #     if isinstance(testcase_type, list):
        #         filters &= Q(testcase_type__in=testcase_type)
        #     else:
        #         filters &= Q(testcase_type=testcase_type)
        # if priority:
        #     if isinstance(priority, list):
        #         filters &= Q(priority__in=priority)
        #     else:
        #         filters &= Q(priority=priority)
        #
        # if filters:
        #     queryset = queryset.filter(filters)
        # logger.info(f'Entered the Filter Function {queryset}, {filters}')
        # if not queryset.exists():
        #     return {
        #         "test_repo": False,
        #         "tcs": {}
        #     }
        # data = TestcaseListSerializer(queryset, many=True)
        # return {
        #     "test_repo": True,
        #     "tcs": data.data
        # }
    except ValidationError as ve:
        logger.error(f"Validation error in filtering: {ve}")
        return {
            "error": "Invalid filter parameters",
            "details": str(ve),
            "test_repo": False
        }

    except Exception as e:
        logger.exception(f"Unexpected error in get_filtered_data: {e}")
        return {
            "error": "An error occurred while fetching data",
            "details": str(e),
            "test_repo": False
        }

