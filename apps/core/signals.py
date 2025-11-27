from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.core.testscore import TestCaseScore
from apps.core.models import TestCaseModel, TestCaseScoreModel, TestCaseMetric, TestCaseScoreModel



# @receiver(post_save, sender=TestCaseMetric)
# def modify_score(sender, instance, created, **kwargs):
#     try:
#         _instance = TestCaseScoreModel.objects.get(testcase__id = instance.testcase.id)
#         if _instance:
#             score = TestCaseScore()
#             score_obj = score.calculate_scores(instance)
#             if score_obj:
#                 for sc in score_obj:
#                     TestCaseScoreModel.objects.create(
#                         testcase = _instance,
#                         score = sc.score,
#                         rpn_value = sc.rpn_value,
#                     )
#             else:
#                 return None
#         return None
#     except Exception as e:
#         print(str(e))
#         return None
