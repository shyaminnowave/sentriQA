from sqlite3 import IntegrityError

from django.core.management.base import BaseCommand, CommandError
from apps.core.helpers import save_score
from apps.core.models import TestCaseModel, TestCaseMetric, TestCaseScoreModel
from apps.core.testscore import TestCaseScore
from django.db import transaction


def get_testcase(testcase_id: int):
    queryset = TestCaseModel.objects.filter(id=testcase_id)
    return queryset.first()

class Command(BaseCommand):
    
    help = "Command to store the Testcase score to the Database."

    def handle(self, *args, **options):
        try:
            queryset = TestCaseMetric.objects.all()
            _data = []
            score = TestCaseScore()
            score_obj = score.calculate_scores(queryset)
            if score_obj:
                for sc in score_obj:
                    test_score = {
                        "testcases": get_testcase(sc.testcase_id),
                        "rpn_value": sc.risk_component,
                        "score": sc.total_score,
                    }
                    _data.append(TestCaseScoreModel(**test_score))
                with transaction.atomic():
                    try:
                        TestCaseScoreModel.objects.bulk_create(_data)
                        self.stdout.write(
                            self.style.SUCCESS('Successfully')
                        )
                    except IntegrityError:
                        self.stdout.write(
                            self.style.ERROR('Error')
                        )
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to calculate scores')
                )
        except Exception as e:
            raise CommandError(f"Error scoring test cases: {e}")