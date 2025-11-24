from django.urls import path
from apps.core.apis import views

urlpatterns = [

    # TestcaseRepo APIs
    path('', views.TestCaseList.as_view(), name='testcase-list'),
    path('testcase', views.TestCaseView.as_view(), name='testcase'),
    path('testcase/<int:pk>', views.TestCaseDetail.as_view(), name='testcase-detail'),
    path('search/testcase', views.SearchTestcaseModel.as_view(), name='search-testcase'),

    # module API
    path('module/', views.ModuleAPIView.as_view(), name='module-list'),

    # Option DropDown APIs
    path('classic-options', views.ClassicOptionAPI.as_view(), name='classic-option-list'),
    path('testcase-options', views.TestcaseOptionAPI.as_view(), name='search-list'),

    # Search
    path('search', views.SearchAPIView.as_view(), name='search-list'),

    # Session API
    path('session/save', views.TestPlanVersionAPI.as_view(), name='test-plan-version'),

    # Version APIs
    path('version/<str:token>', views.GetTestVersionAPI.as_view(), name='version'),
    path('version/<str:token>/<str:version>', views.VersionDetailAPI.as_view(), name='version'),

    # Testplan APIs
    path('test-plan', views.TestPlanningView.as_view(), name='test-plan'),
    path('create-testplan', views.CreateTestPlanView.as_view(), name='create-testplan'),
    path('plan', views.TestPlanView.as_view(), name='get-plans'),
    path('plan/<int:id>', views.PlanDetailsView.as_view(), name='plan-detail'),

    # AI TestPlanCreate API
    path('ai-test-plan', views.AITestPlanningView.as_view(), name='ai-test-plan'),
    path('ai-filter-test', views.AITestCaseFilterChat.as_view()),
    # Utils APIs
    path('file-upload', views.FileUploadView.as_view(), name='file-upload'),
    path('test-scores', views.TestScores.as_view(), name='test-scores'),
    path('get-excel', views.TestScoreExcel.as_view(), name='get-excel'),
    path('convert', views.ConvertAPIView.as_view(), name='convert'),
    path('testing', views.GenerateScoreView.as_view(), name='test'),
    path('plan-history/<int:id>', views.TestPlanHistoryView.as_view(), name='plan-history'),
    path('plan-history/<int:id>/<int:history_id>', views.HistoryPlanDetailsView.as_view(), name='plan-history'),
]