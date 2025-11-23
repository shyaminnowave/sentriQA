from django.urls import path
from apps.jira_integrations.views import JiraProjectView, JiraGetTestcase, JiraGetIssue, \
    JiraTestCaseDetail

urlpatterns = [
    path('project', view=JiraProjectView.as_view(), name='jira-project'),
    path('<str:project>/testcases/', view=JiraGetTestcase.as_view(), name='jira-get-testcase'),
    path('<str:project>/issue/', view=JiraGetIssue.as_view(), name='jira-get-issue'),
    path('issue/<str:issue_id>/', view=JiraTestCaseDetail.as_view(), name='jira-get-issue'),
]