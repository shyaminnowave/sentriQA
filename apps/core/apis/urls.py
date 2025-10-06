from django.urls import path
from apps.core.apis import views

urlpatterns = [
    path('', views.TestCaseList.as_view(), name='testcase-list'),
    path('module/', views.ModuleAPIView.as_view(), name='module-list'),
    path('testcases', views.TestCaseView.as_view(), name='testcase'),
    path('classic-options', views.ClassicOptionAPI.as_view(), name='classic-option-list'),
    path("testcase-options", views.TestcaseOptionAPI.as_view(), name='search-list'),
    path('testcase/<int:pk>', views.TestCaseDetail.as_view(), name='testcase-detail'),
    path('file-upload', views.FileUploadView.as_view(), name='file-upload'),
    path('test-plan', views.TestPlanningView.as_view(), name='test-plan'),
    path('create-testplan', views.CreateTestPlanView.as_view(), name='create-testplan'),
    path('ai-test-plan', views.AITestPlanningView.as_view(), name='ai-test-plan'), ############
    path('get-plans', views.TestPlanView.as_view(), name='get-plans'),
    path('plan/<int:id>', views.PlanDetailsView.as_view(), name='plan-detail'),
    path('test-scores', views.TestScores.as_view(), name='test-scores'),
    path('get-excel', views.TestScoreExcel.as_view(), name='get-excel'),
    path('convert', views.ConvertAPIView.as_view(), name='convert'),
    path('plan-history/<int:id>', views.TestPlanHistroryView.as_view(), name='plan-history'),
    path('plan-history/<int:id>/<int:history_id>', views.HistoryPlanDetailsView.as_view(), name='plan-history'),
    path('testing', views.TestingView.as_view(), name='testing'),
]