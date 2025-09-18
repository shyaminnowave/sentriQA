from django.urls import path
from apps.account.apis import views

urlpatterns = [
    path('login/', views.LoginAPIView.as_view(), name='login'),
    path('sign-up', views.AccountCreateView.as_view(), name='register'),
]