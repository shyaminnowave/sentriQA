import os
from rest_framework.views import APIView, Response
from apps.jira_integrations.services.jira_client import JiraClient

# Create your views here.


class JiraProjectView(APIView):


    def get(self, request, *args, **kwargs):
        client = JiraClient(
            jira_server=os.environ.get('JIRA_SERVER'),
            jira_username=os.environ.get('JIRA_USERNAME'),
            jira_password=os.environ.get('JIRA_API_KEY'),
        )
        project_lst = client.get_projects()
        return Response({
            "status": "SUCCESS",
            "data": project_lst,
            "message": "Success",
            "status_code": 200,
        })


class JiraGetTestcase(APIView):

    def get(self, request, *args, **kwargs):
        client = JiraClient(
            jira_server=os.environ.get('JIRA_SERVER'),
            jira_username=os.environ.get('JIRA_USERNAME'),
            jira_password=os.environ.get('JIRA_API_KEY'),
        )
        query = {
            'jql': f'project = {self.kwargs.get('project')} AND type = Test',
            'fields': 'summary,status,assignee,created,updated,priority,description',
        }
        print(query)
        testcases = client.get_test(query)
        return Response({
            "status": "SUCCESS",
            "data": testcases,
            "message": "Success",
            "status_code": 200,
        })


class JiraGetIssue(APIView):
    def get(self, request, *args, **kwargs):
        client = JiraClient(
            jira_server=os.environ.get('JIRA_SERVER'),
            jira_username=os.environ.get('JIRA_USERNAME'),
            jira_password=os.environ.get('JIRA_API_KEY'),
        )
        query = {
            'jql': f'project = {self.kwargs.get('project')}',
            'fields': 'summary',
        }
        testcases = client.get_issues(query)
        return Response({
            "status": "SUCCESS",
            "data": testcases,
            "message": "Success",
            "status_code": 200,
        })


class JiraTestCaseDetail(APIView):

    def get(self, request, *args, **kwargs):
        client = JiraClient(
            jira_server=os.environ.get('JIRA_SERVER'),
            jira_username=os.environ.get('JIRA_USERNAME'),
            jira_password=os.environ.get('JIRA_API_KEY'),
        )
        testcases = client.get_issue(self.kwargs.get('issue_id'))
        return Response({
            "status": "SUCCESS",
            "data": testcases,
            "message": "Success",
            "status_code": 200,
        })