import requests
from .client import ApiHTTPClient
from requests.auth import HTTPBasicAuth

class JiraClient(ApiHTTPClient):

    def __init__(self, jira_server, jira_username, jira_password):
        self.jira_server = jira_server
        self.jira_username = jira_username
        self.jira_password = jira_password

    def get_authentication(self):
        headers = HTTPBasicAuth(self.jira_username, self.jira_password)
        return headers

    def get_projects(self):
        """
        API to get all Jira projects associated with a user
        """
        auth = self.get_authentication()
        base_url = '/rest/api/3/project'
        endpoint = self.jira_server + base_url
        response = requests.get(endpoint, auth=auth, headers={"Accept": "application/json"})
        projects = []
        for project in response.json():
            _data = {
                "id": project["id"],
                "key": project["key"],
                "name": project["name"],
                "project": project["self"],
            }
            projects.append(_data)
        return projects


    def get_issues(self, query):
        auth = self.get_authentication()
        base_url = f'/rest/api/3/search/jql'
        endpoint = self.jira_server + base_url
        response = requests.get(endpoint, headers={"Accept": "application/json"}, params=query, auth=auth)
        return response.json()

    def get_test(self, query):
        auth = self.get_authentication()
        base_url = f'/rest/api/3/search/jql'
        endpoint = self.jira_server + base_url
        response = requests.get(endpoint, headers={"Accept": "application/json"}, params=query, auth=auth)
        return response.json()

    def get_issue(self, issue_id):
        auth = self.get_authentication()
        base_url = f'rest/api/3/issues/{issue_id}'
        endpoint = self.jira_server + base_url
        response = requests.get(endpoint, headers={"Accept": "application/json"}, auth=auth)
        return response.json()