from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.urls import path, include


class MainSchemaView(SpectacularAPIView):

    patterns = [
        path("api/", include("apps.core.apis.urls")),
    ]

    def get_spectacular_settings(self):
        return {
            'TITLE': 'Main API Documentation',
            'DESCRIPTION': 'Combined API documentation for Core',
            'VERSION': '1.0.0',
        }

class JiraSchemaView(SpectacularAPIView):

    patterns = [
        path("api/jira/", include("apps.jira_integrations.urls")),
    ]

    def get_spectacular_settings(self):
        return {
            'TITLE': 'App4 API Documentation',
            'DESCRIPTION': 'Separate API documentation for Jira App',
            'VERSION': '1.0.0',
        }

class MainAppsSwaggerView(SpectacularSwaggerView):
    schema_url_name = 'main-schema'


class JiraSwaggerView(SpectacularSwaggerView):
    schema_url_name = 'Jira-schema'
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)